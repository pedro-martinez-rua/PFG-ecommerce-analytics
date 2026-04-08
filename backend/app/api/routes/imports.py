from collections import Counter

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.import_record import Import
from app.models.import_sheet import ImportSheet
from app.models.raw_upload import RawUpload
from app.models.user import User
from app.pipelines.detector import detect_type_with_confidence
from app.pipelines.explainer import ERROR_CATALOG, WARNING_CATALOG, build_import_explanation
from app.pipelines.import_orchestrator import run_import, reprocess_import_with_mapping
from app.pipelines.mapper import infer_mapping_with_confidence
from app.pipelines.profiler import dataframe_from_raw_rows, profile_dataframe
from app.schemas.import_schema import ImportResponse
from app.schemas.mapping_schema import MappingApplyRequest, MappingApplyResponse, MappingSuggestionResponse
from app.services.kpi_service import invalidate_kpi_cache

router = APIRouter(prefix="/api/imports", tags=["imports"])
limiter = Limiter(key_func=get_remote_address)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 100 * 1024 * 1024


def _serialize_value(v):
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def _issue_from_validation_error(err: dict) -> dict:
    code = str(err.get("error_type") or "validation_error")
    meta = ERROR_CATALOG.get(code, ERROR_CATALOG["validation_error"])
    return {
        "code": code,
        "title": meta.get("title"),
        "description": meta.get("message"),
        "suggestion": meta.get("suggestion"),
    }


def _load_sheet_raw_dataframe(db: Session, tenant_id: str, import_id: str, sheet_id) -> tuple[pd.DataFrame, dict]:
    raw_rows = (
        db.query(RawUpload)
        .filter_by(import_id=import_id, tenant_id=tenant_id, sheet_id=sheet_id)
        .order_by(RawUpload.row_index.asc())
        .all()
    )
    data = [dict(r.raw_data or {}) for r in raw_rows]
    df = dataframe_from_raw_rows(data)
    profile = profile_dataframe(df)
    return df, profile


def _build_import_diagnosis_payload(db: Session, tenant_id: str, record: Import) -> dict:
    sheets = (
        db.query(ImportSheet)
        .filter_by(import_id=record.id, tenant_id=tenant_id)
        .order_by(ImportSheet.created_at.asc())
        .all()
    )
    sheet_payloads = []

    for sheet in sheets:
        _, profile = _load_sheet_raw_dataframe(db, tenant_id, record.id, sheet.id)
        raw_rows = db.query(RawUpload).filter_by(import_id=record.id, tenant_id=tenant_id, sheet_id=sheet.id).all()
        error_counter: Counter[str] = Counter()
        for raw in raw_rows:
            for err in raw.validation_errors or []:
                error_counter[str(err.get("error_type") or "validation_error")] += 1

        top_errors = []
        for code, count in error_counter.most_common(5):
            item = _issue_from_validation_error({"error_type": code})
            item["count"] = count
            top_errors.append(item)

        top_warnings = []
        for warning in profile.get("warnings", []):
            meta = WARNING_CATALOG["parser_warning"]
            top_warnings.append({
                "code": "parser_warning",
                "title": meta.get("title"),
                "description": warning,
                "suggestion": meta.get("suggestion"),
                "count": 1,
            })

        main_reason = None
        main_reason_code = None
        user_message = None
        suggestions = []
        if record.status == "needs_review":
            main_reason = "Revisión manual necesaria"
            main_reason_code = "needs_review"
            user_message = "El archivo se ha leído, pero faltan columnas mínimas o la detección automática no es lo bastante fiable para procesarlo con seguridad."
            suggestions.append("Abre la revisión de columnas y confirma el mapping manual.")
        elif top_errors:
            main_reason = top_errors[0]["title"]
            main_reason_code = top_errors[0]["code"]
            user_message = top_errors[0]["description"]
            if top_errors[0].get("suggestion"):
                suggestions.append(top_errors[0]["suggestion"])
        elif top_warnings:
            main_reason = top_warnings[0]["title"]
            main_reason_code = top_warnings[0]["code"]
            user_message = top_warnings[0]["description"]

        sheet_payloads.append({
            "sheet_name": sheet.sheet_name,
            "detected_type": sheet.detected_type or "unknown",
            "detection_confidence": round(sheet.detection_confidence or 0.0, 2),
            "valid_rows": sheet.valid_rows or 0,
            "invalid_rows": sheet.invalid_rows or 0,
            "skipped_rows": sheet.skipped_rows or 0,
            "top_errors": top_errors,
            "top_warnings": top_warnings,
            "file_warnings": profile.get("warnings", []),
            "columns_found": profile.get("columns", []),
            "diagnosis": user_message,
            "main_reason_code": main_reason_code,
            "main_reason": main_reason,
            "user_message": user_message,
            "suggestions": suggestions,
            "note": user_message,
            "user_explanations": [],
        })

    explanation = build_import_explanation(record.filename, record.status, sheet_payloads)
    return {
        "import_id": str(record.id),
        "filename": record.filename,
        "status": record.status,
        "detected_type": record.detected_type or "unknown",
        "detection_confidence": round(record.detection_confidence or 0.0, 2),
        "valid_rows": record.valid_rows or 0,
        "invalid_rows": record.invalid_rows or 0,
        "skipped_rows": record.skipped_rows or 0,
        "main_reason_code": explanation.get("main_reason_code") or (sheet_payloads[0].get("main_reason_code") if sheet_payloads else None),
        "main_reason": explanation.get("main_reason") or (sheet_payloads[0].get("main_reason") if sheet_payloads else None),
        "user_message": explanation.get("user_message") or (sheet_payloads[0].get("user_message") if sheet_payloads else None),
        "top_errors": explanation.get("top_errors", []),
        "top_warnings": explanation.get("top_warnings", []),
        "suggestions": explanation.get("suggestions", []) or ["Revisa la preview raw y confirma manualmente las columnas si el sistema no acierta."],
        "sheets": sheet_payloads,
    }


@router.post("/", response_model=ImportResponse, status_code=201)
@limiter.limit("20/hour")
async def create_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Se aceptan: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El fichero está vacío")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"El fichero supera el límite de {MAX_FILE_SIZE // (1024*1024)} MB")

    result = run_import(
        db=db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        filename=file.filename,
        file_content=content
    ) 
    return ImportResponse(**result)


@router.get("/available-range")
def get_available_range(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.execute(text("""
        SELECT
            MIN(o.order_date) AS date_from,
            MAX(o.order_date) AS date_to,
            COUNT(*) AS total_orders,
            COUNT(DISTINCT DATE_TRUNC('month', o.order_date)) AS months_with_data
        FROM orders o
        JOIN imports i ON i.id = o.import_id
        WHERE o.tenant_id = :tenant_id
        AND i.tenant_id = :tenant_id
        AND i.user_id = :user_id
    """), {
        "tenant_id": str(current_user.tenant_id),
        "user_id": str(current_user.id),
    })
    row = result.fetchone()
    if not row or not row[0]:
        return {"has_data": False, "date_from": None, "date_to": None, "total_orders": 0, "months_with_data": 0}
    return {"has_data": True, "date_from": row[0].isoformat(), "date_to": row[1].isoformat(), "total_orders": row[2], "months_with_data": row[3]}


@router.get("/")
def list_imports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.execute(text("""
        WITH user_imports AS (
            SELECT id, filename, file_format, status, detected_type,
                total_rows, valid_rows, invalid_rows, file_size_bytes,
                created_at, completed_at
            FROM imports
            WHERE tenant_id = :tenant_id
            AND user_id = :user_id
        ),
        orders_agg AS (
            SELECT o.import_id,
                MIN(o.order_date) AS data_date_from,
                MAX(o.order_date) AS data_date_to,
                COUNT(*) AS orders_loaded
            FROM orders o
            JOIN imports i ON i.id = o.import_id
            WHERE o.tenant_id = :tenant_id
            AND i.user_id = :user_id
            GROUP BY o.import_id
        ),
        lines_agg AS (
            SELECT ol.import_id,
                COUNT(*) AS lines_loaded
            FROM order_lines ol
            JOIN imports i ON i.id = ol.import_id
            WHERE ol.tenant_id = :tenant_id
            AND i.user_id = :user_id
            GROUP BY ol.import_id
        )
        SELECT ui.id::text, ui.filename, ui.file_format, ui.status, ui.detected_type,
            ui.total_rows, ui.valid_rows, ui.invalid_rows, ui.file_size_bytes,
            ui.created_at, ui.completed_at,
            oa.data_date_from, oa.data_date_to,
            COALESCE(oa.orders_loaded, 0) AS orders_loaded,
            COALESCE(la.lines_loaded, 0) AS lines_loaded
        FROM user_imports ui
        LEFT JOIN orders_agg oa ON oa.import_id = ui.id
        LEFT JOIN lines_agg la ON la.import_id = ui.id
        ORDER BY ui.created_at DESC
    """), {
        "tenant_id": str(current_user.tenant_id),
        "user_id": str(current_user.id),
    })
    items = []
    for row in result.mappings().all():
        item = {k: _serialize_value(v) for k, v in row.items()}
        if item["status"] == "needs_review":
            item["main_reason"] = "Revisión manual necesaria"
            item["user_message"] = "El archivo se ha leído, pero necesita confirmación manual de columnas."
            item["has_warnings"] = True
        elif (item.get("invalid_rows") or 0) > 0:
            item["main_reason"] = "Import completado con incidencias"
            item["user_message"] = "Hay filas inválidas o omitidas."
            item["has_warnings"] = True
        else:
            item["main_reason"] = None
            item["user_message"] = None
            item["has_warnings"] = False
        items.append(item)
    return items


@router.get("/{import_id}")
def get_import(import_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")
    return record


@router.get("/{import_id}/diagnosis")
def get_import_diagnosis(import_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")
    return _build_import_diagnosis_payload(db, str(current_user.tenant_id), record)


@router.get("/{import_id}/mapping-suggestion", response_model=MappingSuggestionResponse)
def get_mapping_suggestion(import_id: str, sheet_name: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    query = db.query(ImportSheet).filter_by(import_id=record.id, tenant_id=current_user.tenant_id)
    if sheet_name:
        query = query.filter_by(sheet_name=sheet_name)
    sheet = query.order_by(ImportSheet.created_at.asc()).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Hoja no encontrada")

    raw_df, profile = _load_sheet_raw_dataframe(db, str(current_user.tenant_id), record.id, sheet.id)
    upload_type, confidence = detect_type_with_confidence(profile.get("columns", []), raw_df)
    suggestions = infer_mapping_with_confidence(profile.get("columns", []), raw_df)
    required_fields = ["order_date"] if upload_type.value in ("orders", "mixed") else (["product_name"] if upload_type.value == "products" else [])
    mapped_fields = {info.get("canonical") for info in suggestions.values() if info.get("canonical")}
    missing = [field for field in required_fields if field not in mapped_fields]

    return {
        "import_id": str(record.id),
        "sheet_name": sheet.sheet_name,
        "upload_type": upload_type.value,
        "confidence": round(confidence, 2),
        "requires_review": bool(missing or upload_type.value == "unknown" or confidence < 0.3),
        "required_fields_missing": missing,
        "raw_columns": profile.get("columns", []),
        "profiler_warnings": profile.get("warnings", []),
        "suggestions": [
            {
                "source_column": col,
                "canonical_field": info.get("canonical"),
                "confidence": info.get("confidence", 0.0),
                "method": info.get("method", "unresolved"),
                "inferred_type": profile.get("inferred_types", {}).get(col),
                "null_ratio": profile.get("null_ratio", {}).get(col),
            }
            for col, info in suggestions.items()
        ],
    }


@router.post("/{import_id}/mapping", response_model=MappingApplyResponse)
def apply_import_mapping(import_id: str, payload: MappingApplyRequest = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mapping = {item.source_column: item.canonical_field for item in payload.assignments}
    try:
        record = db.query(Import).filter_by(
            id=import_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Import no encontrado")
        
        result = reprocess_import_with_mapping(
            db=db,
            tenant_id=str(current_user.tenant_id),
            import_id=import_id,
            user_id=str(current_user.id),
            sheet_name=payload.sheet_name,
            upload_type=payload.upload_type,
            mapping=mapping,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    first_sheet = result["sheets"][0] if result.get("sheets") else {}
    return {
        "import_id": result["import_id"],
        "sheet_name": first_sheet.get("sheet_name") or payload.sheet_name or "sheet",
        "status": result["status"],
        "valid_rows": first_sheet.get("valid_rows", 0),
        "invalid_rows": first_sheet.get("invalid_rows", 0),
        "skipped_rows": first_sheet.get("skipped_rows", 0),
        "detected_type": first_sheet.get("detected_type") or result.get("detected_type") or "unknown",
    }


@router.get("/{import_id}/impact")
def get_import_impact(import_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.dashboard import Dashboard

    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    dashboards = db.query(Dashboard).filter_by(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    ).all()
    affected = []
    for d in dashboards:
        ids = d.import_ids or []
        if import_id not in ids:
            continue
        remaining = [i for i in ids if i != import_id]
        affected.append({
            "dashboard_id": str(d.id),
            "dashboard_name": d.name,
            "total_imports": len(ids),
            "remaining": len(remaining),
            "will_be_deleted": len(remaining) == 0,
        })
    return {"import_id": import_id, "filename": record.filename, "affected": affected, "has_impact": len(affected) > 0}


@router.delete("/{import_id}", status_code=200)
def delete_import(import_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.dashboard import Dashboard

    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    tid = str(current_user.tenant_id)
    dashboards = db.query(Dashboard).filter_by(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    ).all()
    dashboards_to_delete = []

    for d in dashboards:
        ids = list(d.import_ids or [])
        if import_id not in ids:
            continue
        remaining = [i for i in ids if i != import_id]
        if len(remaining) == 0:
            dashboards_to_delete.append(str(d.id))
        else:
            db.execute(text("""UPDATE dashboards SET import_ids = :ids::jsonb WHERE id = :did AND tenant_id = :tid AND user_id = :uid"""), {
                "ids": str(remaining).replace("'", '"'), "did": str(d.id), "tid": tid
            })

    for did in dashboards_to_delete:
        db.execute(text("""UPDATE reports SET dashboard_id = NULL WHERE dashboard_id = :did AND tenant_id = :tid AND created_by = :uid"""), {
            "did": did, "tid": tid, "uid": str(current_user.id)})
        db.execute(text("DELETE FROM dashboards WHERE id = :did AND tenant_id = :tid AND user_id = :uid"), {"did": did, "tid": tid, "uid": str(current_user.id)})
    for table in ["order_lines", "orders", "customers", "products", "field_mappings", "raw_uploads", "import_sheets"]:
        db.execute(text(f"DELETE FROM {table} WHERE tenant_id = :tid AND import_id = :iid"), {"tid": tid, "iid": import_id})

    invalidate_kpi_cache(db, tid)
    db.execute(text("DELETE FROM imports WHERE id = :iid AND tenant_id = :tid"), {"iid": import_id, "tid": tid})
    db.commit()
    return {"message": "Import eliminado correctamente", "dashboards_deleted": dashboards_to_delete}


@router.get("/{import_id}/preview")
def preview_import(import_id: str, mode: str = "raw", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(Import).filter_by(id=import_id, tenant_id=current_user.tenant_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    if mode == "normalized":
        detected = (record.detected_type or "").lower()
        tenant_id = str(current_user.tenant_id)
        if detected in ("orders", "mixed"):
            result = db.execute(text("""SELECT id::text AS id, external_id, order_date::text, total_amount, net_amount, discount_amount, status, channel, shipping_country, currency FROM orders WHERE tenant_id = :tenant_id AND import_id = :import_id ORDER BY order_date NULLS LAST LIMIT 10"""), {"tenant_id": tenant_id, "import_id": import_id})
        elif detected == "order_lines":
            result = db.execute(text("""SELECT id::text AS id, external_id, product_name, sku, category, quantity, unit_price, unit_cost, line_total FROM order_lines WHERE tenant_id = :tenant_id AND import_id = :import_id LIMIT 10"""), {"tenant_id": tenant_id, "import_id": import_id})
        elif detected == "products":
            result = db.execute(text("""SELECT id::text AS id, external_id, name, sku, category, brand, unit_price, unit_cost FROM products WHERE tenant_id = :tenant_id AND import_id = :import_id LIMIT 10"""), {"tenant_id": tenant_id, "import_id": import_id})
        else:
            result = db.execute(text("""SELECT id::text AS id, external_id, email, full_name, country, created_at::text FROM customers WHERE tenant_id = :tenant_id AND import_id = :import_id LIMIT 10"""), {"tenant_id": tenant_id, "import_id": import_id})
        rows = result.fetchall()
        keys = list(result.keys())
        return {"import_id": import_id, "mode": "normalized", "detected_type": detected, "row_count": len(rows), "columns": keys, "rows": [dict(zip(keys, row)) for row in rows]}

    sheet = db.query(ImportSheet).filter_by(import_id=record.id, tenant_id=current_user.tenant_id).order_by(ImportSheet.created_at.asc()).first()
    if not sheet:
        return {"import_id": import_id, "mode": "raw", "detected_type": record.detected_type or "unknown", "row_count": 0, "columns": [], "rows": []}

    raw_df, profile = _load_sheet_raw_dataframe(db, str(current_user.tenant_id), record.id, sheet.id)
    sample_df = raw_df.head(10)
    raw_rows = sample_df.where(pd.notna(sample_df), None).to_dict(orient="records") if not sample_df.empty else []
    return {
        "import_id": import_id,
        "mode": "raw",
        "detected_type": record.detected_type or "unknown",
        "row_count": len(raw_rows),
        "columns": profile.get("columns", []),
        "rows": raw_rows,
        "warnings": profile.get("warnings", []),
    }
