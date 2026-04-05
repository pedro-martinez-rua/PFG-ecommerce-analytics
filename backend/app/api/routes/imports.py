from collections import Counter
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.import_record import Import
from app.models.import_sheet import ImportSheet
from app.models.raw_upload import RawUpload
from app.schemas.import_schema import ImportResponse
from app.pipelines.import_orchestrator import run_import
from app.services.kpi_service import invalidate_kpi_cache
from app.pipelines.explainer import ERROR_CATALOG, WARNING_CATALOG, build_import_explanation

router  = APIRouter(prefix="/api/imports", tags=["imports"])
limiter = Limiter(key_func=get_remote_address)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE      = 100 * 1024 * 1024


def _issue_from_validation_error(err: dict) -> dict:
    code = str(err.get("error_type") or "validation_error")
    meta = ERROR_CATALOG.get(code, ERROR_CATALOG["validation_error"])
    return {
        "code": code,
        "title": meta.get("title"),
        "description": meta.get("message"),
        "suggestion": meta.get("suggestion"),
    }


def _build_import_diagnosis_payload(db: Session, tenant_id: str, record: Import) -> dict:
    sheets = db.query(ImportSheet).filter_by(import_id=record.id, tenant_id=tenant_id).order_by(ImportSheet.created_at.asc()).all()
    sheet_payloads = []
    for sheet in sheets:
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
        for warning in getattr(sheet, "file_warnings", []) or []:
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
        diagnosis = None
        suggestions = []
        if top_errors:
            main_reason = top_errors[0]["title"]
            main_reason_code = top_errors[0]["code"]
            user_message = top_errors[0]["description"]
            diagnosis = top_errors[0]["description"]
            if top_errors[0].get("suggestion"):
                suggestions.append(top_errors[0]["suggestion"])
        elif (sheet.detected_type or "") == "unknown":
            main_reason = "Tipo de archivo no reconocido"
            main_reason_code = "unknown_type"
            user_message = "No se ha podido identificar una estructura válida para esta hoja."
            diagnosis = user_message
            suggestions.append("Revisa la cabecera del archivo y usa nombres de columna más reconocibles.")

        sheet_payloads.append({
            "sheet_name": sheet.sheet_name,
            "detected_type": sheet.detected_type or "unknown",
            "detection_confidence": round(sheet.detection_confidence or 0.0, 2),
            "valid_rows": sheet.valid_rows or 0,
            "invalid_rows": sheet.invalid_rows or 0,
            "skipped_rows": sheet.skipped_rows or 0,
            "top_errors": top_errors,
            "top_warnings": top_warnings,
            "file_warnings": [],
            "columns_found": None,
            "diagnosis": diagnosis,
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
        "main_reason_code": explanation.get("main_reason_code"),
        "main_reason": explanation.get("main_reason"),
        "user_message": explanation.get("user_message"),
        "top_errors": explanation.get("top_errors", []),
        "top_warnings": explanation.get("top_warnings", []),
        "suggestions": explanation.get("suggestions", []),
        "sheets": sheet_payloads,
    }


@router.post("/", response_model=ImportResponse, status_code=201)
@limiter.limit("20/hour")
async def create_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sube y procesa un fichero CSV o XLSX."""
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400,
            detail=f"Formato no soportado. Se aceptan: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El fichero está vacío")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400,
            detail=f"El fichero supera el límite de {MAX_FILE_SIZE // (1024*1024)} MB")

    result = run_import(
        db=db,
        tenant_id=str(current_user.tenant_id),
        filename=file.filename,
        file_content=content
    )
    return ImportResponse(**result)


@router.get("/available-range")
def get_available_range(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rango de fechas disponible en todos los datos del tenant."""
    result = db.execute(text("""
        SELECT
            MIN(order_date) AS date_from,
            MAX(order_date) AS date_to,
            COUNT(*)        AS total_orders,
            COUNT(DISTINCT DATE_TRUNC('month', order_date)) AS months_with_data
        FROM orders
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": str(current_user.tenant_id)})

    row = result.fetchone()
    if not row or not row[0]:
        return {"has_data": False, "date_from": None,
                "date_to": None, "total_orders": 0, "months_with_data": 0}
    return {
        "has_data":         True,
        "date_from":        row[0].isoformat(),
        "date_to":          row[1].isoformat(),
        "total_orders":     row[2],
        "months_with_data": row[3]
    }


@router.get("/")
def list_imports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista imports del tenant con estadísticas y rango de fechas de sus datos."""
    result = db.execute(text("""
        SELECT
            i.id::text,
            i.filename,
            i.file_format,
            i.status,
            i.detected_type,
            i.total_rows,
            i.valid_rows,
            i.invalid_rows,
            i.file_size_bytes,
            i.created_at,
            i.completed_at,
            MIN(o.order_date) AS data_date_from,
            MAX(o.order_date) AS data_date_to,
            COUNT(o.id)       AS orders_loaded,
            COUNT(ol.id)      AS lines_loaded
        FROM imports i
        LEFT JOIN orders o
               ON o.import_id = i.id
              AND o.tenant_id = i.tenant_id
        LEFT JOIN order_lines ol
               ON ol.import_id = i.id
              AND ol.tenant_id = i.tenant_id
        WHERE i.tenant_id = :tenant_id
        GROUP BY i.id, i.filename, i.file_format, i.status, i.detected_type,
                 i.total_rows, i.valid_rows, i.invalid_rows,
                 i.file_size_bytes, i.created_at, i.completed_at
        ORDER BY i.created_at DESC
    """), {"tenant_id": str(current_user.tenant_id)})

    rows = result.fetchall()
    keys = list(result.keys())

    def serialize(v):
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        if hasattr(v, 'hex'):
            return str(v)
        return v

    return [{k: serialize(v) for k, v in zip(keys, row)} for row in rows]


@router.get("/{import_id}")
def get_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detalle de un import."""
    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")
    return record


@router.get("/{import_id}/diagnosis")
def get_import_diagnosis(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Diagnóstico explicable de un import, orientado a frontend."""
    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    return _build_import_diagnosis_payload(db, current_user.tenant_id, record)

@router.get("/{import_id}/impact")
def get_import_impact(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve qué dashboards se verían afectados si se elimina este import.
    Para cada dashboard indica si quedaría vacío (se eliminaría) o incompleto.
    """
    from app.models.dashboard import Dashboard

    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    # Buscar todos los dashboards del tenant que incluyen este import
    dashboards = db.query(Dashboard).filter_by(
        tenant_id=current_user.tenant_id
    ).all()

    affected = []
    for d in dashboards:
        ids = d.import_ids or []
        if import_id not in ids:
            continue
        remaining = [i for i in ids if i != import_id]
        affected.append({
            "dashboard_id":   str(d.id),
            "dashboard_name": d.name,
            "total_imports":  len(ids),
            "remaining":      len(remaining),
            "will_be_deleted": len(remaining) == 0,
        })

    return {
        "import_id":   import_id,
        "filename":    record.filename,
        "affected":    affected,
        "has_impact":  len(affected) > 0,
    }

@router.delete("/{import_id}", status_code=200)
def delete_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un import y sus datos.
    - Dashboards que quedan sin imports → se eliminan automáticamente.
    - Los informes guardados asociados a esos dashboards NO se eliminan.
    """
    from app.models.dashboard import Dashboard

    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    tid = str(current_user.tenant_id)

    # 1 — Gestionar dashboards afectados ANTES de borrar datos
    dashboards = db.query(Dashboard).filter_by(tenant_id=current_user.tenant_id).all()
    dashboards_to_delete = []

    for d in dashboards:
        ids = list(d.import_ids or [])
        if import_id not in ids:
            continue
        remaining = [i for i in ids if i != import_id]
        if len(remaining) == 0:
            dashboards_to_delete.append(str(d.id))
        else:
            # Actualizar import_ids del dashboard
            db.execute(text("""
                UPDATE dashboards
                SET import_ids = :ids::jsonb
                WHERE id = :did AND tenant_id = :tid
            """), {
                "ids": str(remaining).replace("'", '"'),
                "did": str(d.id),
                "tid": tid
            })

    # Eliminar dashboards vacíos (los informes quedan huérfanos pero NO se borran)
    for did in dashboards_to_delete:
        # Desvincular informes antes de borrar
        db.execute(text("""
            UPDATE reports SET dashboard_id = NULL
            WHERE dashboard_id = :did
        """), {"did": did})

        db.execute(text(
            "DELETE FROM dashboards WHERE id = :did AND tenant_id = :tid"
        ), {"did": did, "tid": tid})

    # 2 — Eliminar datos del import en cascada
    for table in ["order_lines", "orders", "customers", "products",
                  "field_mappings", "raw_uploads", "import_sheets"]:
        db.execute(text(f"""
            DELETE FROM {table}
            WHERE tenant_id = :tid AND import_id = :iid
        """), {"tid": tid, "iid": import_id})

    invalidate_kpi_cache(db, tid)

    # 3 — Eliminar el import
    db.execute(text("""
        DELETE FROM imports WHERE id = :iid AND tenant_id = :tid
    """), {"iid": import_id, "tid": tid})

    db.commit()

    return {
        "message": "Import eliminado correctamente",
        "dashboards_deleted": dashboards_to_delete,
    }
    
@router.get("/{import_id}/preview")
def preview_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve las primeras 10 filas del import según su tipo detectado.
    Busca en la tabla correspondiente (orders, order_lines, products, customers).
    """
    record = db.query(Import).filter_by(
        id=import_id,
        tenant_id=current_user.tenant_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Import no encontrado")

    detected = (record.detected_type or "").lower()
    tenant_id = str(current_user.tenant_id)

    # Seleccionar tabla según tipo detectado
    if detected in ("orders", "mixed"):
        result = db.execute(text("""
            SELECT
                id::text AS id,
                external_id,
                order_date::text,
                total_amount,
                net_amount,
                discount_amount,
                status,
                channel,
                shipping_country,
                currency
            FROM orders
            WHERE tenant_id = :tenant_id
              AND import_id = :import_id
            ORDER BY order_date
            LIMIT 10
        """), {"tenant_id": tenant_id, "import_id": import_id})

    elif detected == "order_lines":
        result = db.execute(text("""
            SELECT
                id::text AS id,
                external_id,
                product_name,
                sku,
                category,
                quantity,
                unit_price,
                unit_cost,
                line_total
            FROM order_lines
            WHERE tenant_id = :tenant_id
              AND import_id = :import_id
            LIMIT 10
        """), {"tenant_id": tenant_id, "import_id": import_id})

    elif detected == "products":
        result = db.execute(text("""
            SELECT
                id::text AS id,
                external_id,
                name,
                sku,
                category,
                brand,
                unit_price,
                unit_cost
            FROM products
            WHERE tenant_id = :tenant_id
              AND import_id = :import_id
            LIMIT 10
        """), {"tenant_id": tenant_id, "import_id": import_id})

    elif detected == "customers":
        result = db.execute(text("""
            SELECT
                id::text AS id,
                external_id,
                email,
                full_name,
                country,
                created_at::text
            FROM customers
            WHERE tenant_id = :tenant_id
              AND import_id = :import_id
            LIMIT 10
        """), {"tenant_id": tenant_id, "import_id": import_id})

    else:
        # Tipo desconocido — intentar con orders
        result = db.execute(text("""
            SELECT id::text, external_id, order_date::text, total_amount
            FROM orders
            WHERE tenant_id = :tenant_id AND import_id = :import_id
            LIMIT 10
        """), {"tenant_id": tenant_id, "import_id": import_id})

    rows = result.fetchall()
    keys = list(result.keys())

    return {
        "import_id":    import_id,
        "detected_type": detected,
        "row_count":    len(rows),
        "columns":      keys,
        "rows":         [dict(zip(keys, row)) for row in rows],
    }