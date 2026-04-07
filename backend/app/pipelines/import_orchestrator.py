"""
import_orchestrator.py — Capa de orquestación del pipeline.

Coordina todas las capas en orden:
file_parser → detector → mapper → validator → transformer → canonical_loader

Tipos soportados: orders, order_lines, customers, products, mixed.
import_id en todas las entidades para trazabilidad y delete en cascada.
Resolución automática de relaciones entre imports distintos.
Los datos del usuario nunca salen del servidor.
"""
import uuid
import hashlib
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.pipelines.file_parser import parse_file, ParsedSheet
from app.pipelines.detector import detect_type_with_confidence, UploadType
from app.pipelines.mapper import (
    infer_mapping_with_confidence,
    persist_mapping,
    get_saved_mapping,
)
from app.pipelines.transformer import transform_row
from app.pipelines.validator import validate_dataframe, build_validation_summary
from app.pipelines.entity_resolver import run_all_resolvers

from app.models.import_record import Import
from app.models.import_sheet import ImportSheet
from app.models.raw_upload import RawUpload
from app.models.order import Order
from app.models.order_line import OrderLine
from app.models.customer import Customer
from app.models.product import Product


# SEGURIDAD
SENSITIVE_FIELDS_BLOCKLIST = {
    "password", "contraseña", "passwd", "pin", "cvv", "cvc",
    "card_number", "numero_tarjeta", "tarjeta", "tarjeta_credito",
    "iban", "account_number", "numero_cuenta", "cuenta_bancaria",
    "nif", "dni", "nie", "passport", "pasaporte", "ssn",
    "credit_card", "debit_card", "swift", "routing_number",
    "secret", "token", "api_key", "private_key"
}

def _sanitize_extra(extra: dict) -> dict:
    return {
        k: v for k, v in extra.items()
        if k.lower().replace(" ", "_").replace("-", "_")
        not in SENSITIVE_FIELDS_BLOCKLIST
    }

def _generate_dedup_key(transformed: dict) -> str | None:
    date_val  = str(transformed.get("order_date", ""))
    total_val = str(transformed.get("total_amount", ""))
    prod_val  = str(transformed.get("product_name", ""))
    cust_val  = str(transformed.get("customer_external_id", ""))

    if date_val and date_val not in ("None", ""):
        raw = f"{date_val}|{total_val}|{prod_val}|{cust_val}"
        return f"hash_{hashlib.md5(raw.encode()).hexdigest()}"
    return None

# PUNTO DE ENTRADA PRINCIPAL
def run_import(
    db: Session,
    tenant_id: str,
    user_id: str,
    filename: str,
    file_content: bytes
) -> dict:
    file_size = len(file_content)
    file_format = "xlsx" if filename.lower().endswith((".xlsx", ".xls")) else "csv"

    import_record = Import(
        tenant_id=tenant_id,
        user_id=user_id,
        filename=filename,
        file_format=file_format,
        file_size_bytes=file_size,
        status="processing"
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)
    import_id = str(import_record.id)

    try:
        sheets = parse_file(file_content, filename)
    except ValueError as e:
        import_record.status = "failed"
        import_record.error_message = str(e)
        import_record.completed_at = datetime.now(timezone.utc)
        db.commit()
        return _failed_response(import_id, filename, str(e))

    return _process_parsed_sheets(db, tenant_id, import_record, sheets)


def reprocess_import_with_mapping(
    db: Session,
    tenant_id: str,
    import_id: str,
    user_id: str,
    sheet_name: str | None,
    upload_type: str | None,
    mapping: dict[str, str | None],
) -> dict:
    import_record = db.query(Import).filter_by(id=import_id, tenant_id=tenant_id, user_id=user_id).first()
    if not import_record:
        raise ValueError("Import no encontrado")

    # 1) Leer primero los datos raw. Son la fuente para poder reprocesar.
    raw_rows = (
        db.query(RawUpload)
        .filter_by(import_id=import_id, tenant_id=tenant_id)
        .order_by(RawUpload.sheet_id.asc(), RawUpload.row_index.asc())
        .all()
    )
    if not raw_rows:
        raise ValueError("No hay datos raw para reprocesar este import")

    grouped: dict[str, list[dict]] = {}
    for row in raw_rows:
        key = row.filename or str(row.sheet_id) or import_record.filename
        grouped.setdefault(key, []).append(dict(row.raw_data or {}))

    parsed_sheets: list[ParsedSheet] = []
    for current_sheet_name, rows in grouped.items():
        if sheet_name and current_sheet_name != sheet_name:
            continue

        df = pd.DataFrame(rows)
        df = df.where(pd.notna(df), None)

        parsed_sheets.append(
            ParsedSheet(
                sheet_name=current_sheet_name,
                dataframe=df,
                source_format=import_record.file_format,
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns),
                warnings=[],
            )
        )

    if not parsed_sheets:
        raise ValueError("No se encontró la hoja solicitada para reprocesar")

    # 2) Limpiar SOLO datos normalizados/derivados.
    #    No borrar ImportSheet ni RawUpload aquí, porque forman parte
    #    de la base raw que se usa para preview y reprocesado.
    try:
        db.query(OrderLine).filter_by(
            import_id=import_id,
            tenant_id=tenant_id,
        ).delete(synchronize_session=False)

        db.query(Order).filter_by(
            import_id=import_id,
            tenant_id=tenant_id,
        ).delete(synchronize_session=False)

        db.query(Customer).filter_by(
            import_id=import_id,
            tenant_id=tenant_id,
        ).delete(synchronize_session=False)

        db.query(Product).filter_by(
            import_id=import_id,
            tenant_id=tenant_id,
        ).delete(synchronize_session=False)

        db.commit()

    except Exception:
        db.rollback()
        raise

    # 3) Reprocesar desde los raws persistidos con el mapping manual aplicado.
    return _process_parsed_sheets(
        db,
        tenant_id,
        import_record,
        parsed_sheets,
        manual_mapping=mapping,
        forced_upload_type=upload_type,
    )

def _process_parsed_sheets(
    db: Session,
    tenant_id: str,
    import_record: Import,
    sheets: list[ParsedSheet],
    manual_mapping: dict[str, str | None] | None = None,
    forced_upload_type: str | None = None,
) -> dict:
    total_valid = total_invalid = total_skipped = 0
    sheet_results = []

    for sheet in sheets:
        result = _process_sheet(
            db=db,
            tenant_id=tenant_id,
            import_id=str(import_record.id),
            sheet=sheet,
            manual_mapping=manual_mapping,
            forced_upload_type=forced_upload_type,
        )
        sheet_results.append(result)
        total_valid += result["valid_rows"]
        total_invalid += result["invalid_rows"]
        total_skipped += result["skipped_rows"]

    total_rows = total_valid + total_invalid + total_skipped
    import_record.total_rows = total_rows
    import_record.valid_rows = total_valid
    import_record.invalid_rows = total_invalid
    import_record.skipped_rows = total_skipped
    import_record.completed_at = datetime.now(timezone.utc)

    detected_types = list({r["detected_type"] for r in sheet_results})
    import_record.detected_type = detected_types[0] if len(detected_types) == 1 else "mixed"
    import_record.detection_confidence = sheet_results[0]["detection_confidence"] if sheet_results else 0.0
    import_record.mapping_confirmed = bool(manual_mapping)

    if any(r.get("requires_review") for r in sheet_results):
        import_record.status = "needs_review"
    elif total_invalid > 0:
        import_record.status = "completed_with_errors"
    else:
        import_record.status = "completed"
    db.commit()

    resolution_results = None
    if import_record.status != "needs_review":
        resolution_results = run_all_resolvers(db, tenant_id)
        try:
            from app.services.kpi_service import invalidate_kpi_cache
            invalidate_kpi_cache(db, tenant_id)
        except Exception:
            pass

    return {
        "import_id": str(import_record.id),
        "filename": import_record.filename,
        "file_format": import_record.file_format,
        "status": import_record.status,
        "total_rows": total_rows,
        "valid_rows": total_valid,
        "invalid_rows": total_invalid,
        "skipped_rows": total_skipped,
        "sheets_processed": len(sheet_results),
        "sheets": sheet_results,
        "detected_type": import_record.detected_type,
        "detection_confidence": import_record.detection_confidence,
        "relations_resolved": resolution_results,
        "main_reason": sheet_results[0].get("main_reason") if sheet_results else None,
        "user_message": sheet_results[0].get("user_message") if sheet_results else None,
        "suggestions": sheet_results[0].get("suggestions", []) if sheet_results else [],
    }


def _process_sheet(
    db: Session,
    tenant_id: str,
    import_id: str,
    sheet: ParsedSheet,
    manual_mapping: dict[str, str | None] | None = None,
    forced_upload_type: str | None = None,
) -> dict:
    BATCH_SIZE = 1000
    import_sheet = ImportSheet(
        import_id=import_id,
        tenant_id=tenant_id,
        sheet_name=sheet.sheet_name,
        status="processing",
        total_rows=sheet.row_count,
    )
    db.add(import_sheet)
    db.commit()
    db.refresh(import_sheet)
    sheet_id = str(import_sheet.id)

    _stage_raw_rows(db, tenant_id, import_id, sheet_id, sheet)

    upload_type, confidence = detect_type_with_confidence(sheet.columns, sheet.dataframe)
    if forced_upload_type:
        upload_type = UploadType(forced_upload_type)
        confidence = max(confidence, 0.8)

    import_sheet.detected_type = upload_type.value
    import_sheet.detection_confidence = confidence
    db.commit()

    mapping_with_confidence = infer_mapping_with_confidence(sheet.columns, sheet.dataframe)
    if manual_mapping:
        for source, target in manual_mapping.items():
            mapping_with_confidence[source] = {
                "canonical": target,
                "confidence": 1.0 if target else 0.0,
                "method": "manual" if target else "ignored",
            }
        persist_mapping(db, tenant_id, upload_type.value, mapping_with_confidence, import_id, confirmed=True)
    else:
        saved_mapping = get_saved_mapping(db, tenant_id, upload_type.value)
        if saved_mapping:
            for source, target in saved_mapping.items():
                if source in mapping_with_confidence:
                    mapping_with_confidence[source]["canonical"] = target
                    mapping_with_confidence[source]["method"] = "saved"
                    mapping_with_confidence[source]["confidence"] = max(mapping_with_confidence[source].get("confidence", 0), 0.95)
        persist_mapping(db, tenant_id, upload_type.value, mapping_with_confidence, import_id, confirmed=False)

    mapping = {col: info["canonical"] for col, info in mapping_with_confidence.items() if info.get("canonical")}
    required_fields = ["order_date"] if upload_type.value in ("orders", "mixed") else (["product_name"] if upload_type.value == "products" else [])
    missing_required = [field for field in required_fields if field not in mapping.values()]
    low_confidence = upload_type == UploadType.UNKNOWN or confidence < 0.3
    requires_review = bool(missing_required or low_confidence)

    if requires_review and not manual_mapping:
        import_sheet.valid_rows = 0
        import_sheet.invalid_rows = sheet.row_count
        import_sheet.status = "completed"
        db.commit()
        return {
            "sheet_name": sheet.sheet_name,
            "detected_type": upload_type.value,
            "detection_confidence": round(confidence, 2),
            "valid_rows": 0,
            "invalid_rows": sheet.row_count,
            "skipped_rows": 0,
            "top_errors": [],
            "file_warnings": sheet.warnings,
            "requires_review": True,
            "main_reason": "Revisión manual necesaria",
            "user_message": "El archivo se ha leído, pero faltan columnas mínimas o la detección automática no es suficiente para procesarlo con seguridad.",
            "suggestions": [
                "Revisa la asignación de columnas antes de procesar este import.",
                *([f"Falta asignar: {', '.join(missing_required)}"] if missing_required else []),
            ],
        }

    df = sheet.dataframe.copy()
    rename_map = {col: mapping[col] for col in df.columns if col in mapping}
    df_canonical = df.rename(columns=rename_map)
    validation_results, processable_df = validate_dataframe(df_canonical, upload_type.value)
    summary = build_validation_summary(validation_results)
    _apply_validation_results_to_raw_rows(db, tenant_id, import_id, sheet_id, validation_results, df, rename_map)

    valid_loaded = 0
    if not processable_df.empty:
        if upload_type in (UploadType.ORDERS, UploadType.MIXED):
            existing_ids = _get_existing_external_ids(db, tenant_id, Order)
            valid_loaded = _bulk_write_orders(db, tenant_id, import_id, processable_df, df, mapping, existing_ids, BATCH_SIZE)
        elif upload_type == UploadType.ORDER_LINES:
            existing_ids = _get_existing_external_ids(db, tenant_id, OrderLine)
            valid_loaded = _bulk_write_order_lines(db, tenant_id, import_id, processable_df, mapping, existing_ids, BATCH_SIZE)
        elif upload_type == UploadType.CUSTOMERS:
            existing_ids = _get_existing_external_ids(db, tenant_id, Customer)
            valid_loaded = _bulk_write_customers(db, tenant_id, import_id, processable_df, existing_ids, BATCH_SIZE)
        elif upload_type == UploadType.PRODUCTS:
            existing_ids = _get_existing_external_ids(db, tenant_id, Product)
            valid_loaded = _bulk_write_products(db, tenant_id, import_id, processable_df, existing_ids, BATCH_SIZE)

    import_sheet.valid_rows = valid_loaded
    import_sheet.invalid_rows = summary["invalid_rows"]
    import_sheet.skipped_rows = summary["skipped_rows"]
    import_sheet.status = "completed"
    db.commit()

    return {
        "sheet_name": sheet.sheet_name,
        "detected_type": upload_type.value,
        "detection_confidence": round(confidence, 2),
        "valid_rows": valid_loaded,
        "invalid_rows": summary["invalid_rows"],
        "skipped_rows": summary["skipped_rows"],
        "top_errors": summary.get("top_errors", []),
        "file_warnings": sheet.warnings,
        "requires_review": False,
        "main_reason": None,
        "user_message": None,
        "suggestions": [],
    }


def _stage_raw_rows(db, tenant_id, import_id, sheet_id, sheet):
    batch = []
    for idx, row in sheet.dataframe.iterrows():
        row_dict = row.where(pd.notna(row), None).to_dict()
        batch.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "upload_id": import_id,
            "import_id": import_id,
            "sheet_id": sheet_id,
            "upload_type": None,
            "filename": sheet.sheet_name,
            "row_index": int(idx),
            "raw_data": row_dict,
            "mapped_data": {},
            "transformed_data": {},
            "validation_errors": [],
            "status": "pending",
            "skip_reason": None,
            "error_message": None,
            "processed_at": None,
        })
    if batch:
        db.bulk_insert_mappings(RawUpload, batch)
        db.commit()


def _apply_validation_results_to_raw_rows(db, tenant_id, import_id, sheet_id, validation_results, original_df, rename_map):
    for result in validation_results:
        if result.status.value == "valid":
            continue
        row_dict = original_df.loc[result.row_index].where(pd.notna(original_df.loc[result.row_index]), None).to_dict() if result.row_index in original_df.index else {}
        mapped = {rename_map.get(k, k): v for k, v in row_dict.items() if rename_map.get(k, k)}
        transformed = transform_row(mapped) if mapped else {}
        db.query(RawUpload).filter_by(import_id=import_id, tenant_id=tenant_id, sheet_id=sheet_id, row_index=result.row_index).update({
            RawUpload.mapped_data: mapped,
            RawUpload.transformed_data: transformed,
            RawUpload.validation_errors: result.errors,
            RawUpload.status: result.status.value,
            RawUpload.error_message: '; '.join(e.get('message', '') for e in result.errors)[:500] if result.errors else None,
        }, synchronize_session=False)
    db.commit()

# HELPERS DE RENDIMIENTO
def _get_existing_external_ids(db: Session, tenant_id: str, model) -> set:
    rows = db.query(model.external_id).filter(
        model.tenant_id == tenant_id,
        model.external_id.isnot(None)
    ).all()
    return {r[0] for r in rows}

def _bulk_write_orders(
    db, tenant_id, import_id,
    processable_df, original_df, mapping,
    existing_ids, batch_size
) -> int:
    orders_batch = []
    lines_batch  = []
    loaded       = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["external_id"]) if transformed.get("external_id") else None
        if not ext_id:
            ext_id = _generate_dedup_key(transformed)

        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        extra = _sanitize_extra({
            col: row_dict.get(col)
            for col in original_df.columns
            if col not in mapping and col in original_df.columns
        })

        order_id = str(uuid.uuid4())
        orders_batch.append({
            "id":               order_id,
            "tenant_id":        tenant_id,
            "import_id":        import_id,
            "customer_id":      None,
            "customer_reference": transformed.get("customer_external_id") or
                      transformed.get("customer_email"),
            "external_id":      ext_id,
            "order_date":       transformed.get("order_date"),
            "total_amount":     transformed.get("total_amount"),
            "discount_amount":  transformed.get("discount_amount"),
            "net_amount":       transformed.get("net_amount"),
            "shipping_cost":    transformed.get("shipping_cost"),
            "refund_amount":    transformed.get("refund_amount"),
            "cogs_amount":      transformed.get("cogs_amount"),
            "currency":         transformed.get("currency"),
            "channel":          transformed.get("channel"),
            "status":           transformed.get("status"),
            "payment_method":   transformed.get("payment_method"),
            "shipping_country": transformed.get("shipping_country"),
            "shipping_region":  transformed.get("shipping_region"),
            "delivery_days":    transformed.get("delivery_days"),
            "is_returned":      transformed.get("is_returned", False),
            "device_type":      transformed.get("device_type"),
            "utm_source":       transformed.get("utm_source"),
            "utm_campaign":     transformed.get("utm_campaign"),
            "session_id":       transformed.get("session_id"),
            "extra_attributes": extra,
        })

        if transformed.get("product_name") or transformed.get("sku"):
            lines_batch.append({
                "id":              str(uuid.uuid4()),
                "tenant_id":       tenant_id,
                "import_id":       import_id,
                "order_id":        order_id,
                "product_id":      None,
                "external_id":     None,
                "product_name":    transformed.get("product_name"),
                "sku":             transformed.get("sku"),
                "category":        transformed.get("category"),
                "brand":           transformed.get("brand"),
                "quantity":        transformed.get("quantity"),
                "unit_price":      transformed.get("unit_price"),
                "unit_cost":       transformed.get("unit_cost"),
                "line_total":      transformed.get("line_total") or transformed.get("total_amount"),
                "discount_amount": None,
                "refund_amount":   None,
                "is_primary_item": None,
                "is_refunded":     False,
                "extra_attributes": {},
            })

        if len(orders_batch) >= batch_size:
            try:
                db.bulk_insert_mappings(Order, orders_batch)
                if lines_batch:
                    db.bulk_insert_mappings(OrderLine, lines_batch)
                db.commit()
                loaded      += len(orders_batch)
                orders_batch = []
                lines_batch  = []
            except Exception:
                db.rollback()
                orders_batch = []
                lines_batch  = []

    if orders_batch:
        try:
            db.bulk_insert_mappings(Order, orders_batch)
            if lines_batch:
                db.bulk_insert_mappings(OrderLine, lines_batch)
            db.commit()
            loaded += len(orders_batch)
        except Exception:
            db.rollback()

    return loaded

def _parse_bool(value) -> bool:
    """Convierte cualquier representación de booleano a bool de Python."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).lower().strip() in ("1", "true", "yes", "si", "sí")

def _bulk_write_order_lines(
    db, tenant_id, import_id,
    processable_df, mapping,
    existing_ids, batch_size
) -> int:
    """
    Inserta líneas de pedido directamente desde ficheros tipo order_items.
    order_id y product_id quedan NULL — entity_resolver los vincula después
    usando external_id (= order_id del fichero origen) como clave de unión.
    """
    batch  = []
    loaded = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        # external_id = order_item_id del CSV — para deduplicación
        ext_id = str(transformed.get("external_id")) \
                 if transformed.get("external_id") else None
        if not ext_id:
            ext_id = str(uuid.uuid4())

        if ext_id in existing_ids:
            continue
        existing_ids.add(ext_id)

        batch.append({
            "id":              str(uuid.uuid4()),
            "tenant_id":       tenant_id,
            "import_id":       import_id,
            "order_id":        None,         # resolver vincula después
            "product_id":      None,         # resolver vincula después
            "external_id":     ext_id,
            "product_name":    transformed.get("product_name"),
            "sku":             transformed.get("sku"),
            "category":        transformed.get("category"),
            "brand":           transformed.get("brand"),
            "quantity":        transformed.get("quantity"),
            "unit_price":      transformed.get("unit_price"),
            "unit_cost":       transformed.get("unit_cost"),
            "line_total":      transformed.get("line_total"),
            "discount_amount": None,
            "refund_amount":   transformed.get("refund_amount"),
            "is_primary_item": _parse_bool(transformed.get("is_primary_item")),
            "is_refunded":     _parse_bool(transformed.get("is_refunded", False)),
            "extra_attributes": {},
        })

        if len(batch) >= batch_size:
            try:
                db.bulk_insert_mappings(OrderLine, batch)
                db.commit()
                loaded += len(batch)
                batch   = []
            except Exception:
                db.rollback()
                batch = []

    if batch:
        try:
            db.bulk_insert_mappings(OrderLine, batch)
            db.commit()
            loaded += len(batch)
        except Exception:
            db.rollback()
            batch=[]

    return loaded

def _bulk_write_customers(
    db, tenant_id, import_id,
    processable_df,
    existing_ids, batch_size
) -> int:
    batch  = []
    loaded = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["customer_external_id"]) \
                 if transformed.get("customer_external_id") else None
        if not ext_id:
            email = transformed.get("customer_email")
            if email:
                ext_id = f"email_{email}"

        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        batch.append({
            "id":               str(uuid.uuid4()),
            "tenant_id":        tenant_id,
            "import_id":        import_id,
            "external_id":      str(transformed["customer_external_id"])
                                 if transformed.get("customer_external_id") else None,
            "email":            transformed.get("customer_email"),
            "full_name":        transformed.get("customer_name"),
            "country":          transformed.get("country"),
            "region":           transformed.get("region"),
            "total_orders":     0,
            "total_spent":      0,
            "avg_order_value":  None,
            "customer_rating":  transformed.get("customer_rating"),
            "first_seen_at":    None,
            "last_order_at":    None,
            "extra_attributes": {},
        })

        if len(batch) >= batch_size:
            try:
                db.bulk_insert_mappings(Customer, batch)
                db.commit()
                loaded += len(batch)
                batch   = []
            except Exception:
                db.rollback()
                batch = []

    if batch:
        try:
            db.bulk_insert_mappings(Customer, batch)
            db.commit()
            loaded += len(batch)
        except Exception:
            db.rollback()

    return loaded

def _bulk_write_products(
    db, tenant_id, import_id,
    processable_df,
    existing_ids, batch_size
) -> int:
    batch  = []
    loaded = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["product_external_id"]) \
                 if transformed.get("product_external_id") else None
        if not ext_id:
            name = transformed.get("product_name", "")
            sku  = transformed.get("sku", "")
            if name:
                raw    = f"{name}|{sku}"
                ext_id = f"hash_{hashlib.md5(raw.encode()).hexdigest()}"

        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        batch.append({
            "id":               str(uuid.uuid4()),
            "tenant_id":        tenant_id,
            "import_id":        import_id,
            "external_id":      str(transformed["product_external_id"])
                                 if transformed.get("product_external_id") else None,
            "name":             transformed.get("product_name", "Sin nombre"),
            "sku":              transformed.get("sku"),
            "category":         transformed.get("category"),
            "brand":            transformed.get("brand"),
            "unit_cost":        transformed.get("unit_cost"),
            "unit_price":       transformed.get("unit_price"),
            "extra_attributes": {},
        })

        if len(batch) >= batch_size:
            try:
                db.bulk_insert_mappings(Product, batch)
                db.commit()
                loaded += len(batch)
                batch   = []
            except Exception:
                db.rollback()
                batch = []

    if batch:
        try:
            db.bulk_insert_mappings(Product, batch)
            db.commit()
            loaded += len(batch)
        except Exception:
            db.rollback()

    return loaded

# HELPERS AUXILIARES
def _stage_all_rows(db, tenant_id, import_id, sheet_id, sheet, upload_type):
    batch = []
    for idx, row in sheet.dataframe.iterrows():
        row_dict = row.where(pd.notna(row), None).to_dict()
        batch.append({
            "id":                str(uuid.uuid4()),
            "tenant_id":         tenant_id,
            "upload_id":         import_id,
            "import_id":         import_id,
            "sheet_id":          sheet_id,
            "upload_type":       upload_type,
            "filename":          sheet.sheet_name,
            "row_index":         int(idx),
            "raw_data":          row_dict,
            "mapped_data":       {},
            "transformed_data":  {},
            "validation_errors": [{"error_type": "unknown_type",
                                   "message": "No se pudo determinar el tipo de datos"}],
            "status":            "invalid",
            "skip_reason":       None,
            "error_message":     None,
            "processed_at":      None,
        })

        if len(batch) >= 1000:
            try:
                db.bulk_insert_mappings(RawUpload, batch)
                db.commit()
                batch = []
            except Exception:
                db.rollback()
                batch = []

    if batch:
        try:
            db.bulk_insert_mappings(RawUpload, batch)
            db.commit()
        except Exception:
            db.rollback()

def _build_unrecognized_hint(columns: list[str]) -> str:
    from rapidfuzz import fuzz

    ORDER_SIGNALS      = ["order_date", "total_amount", "order_id", "fecha", "importe"]
    ORDER_LINE_SIGNALS = ["order_item_id", "is_primary_item", "item_price", "line_total"]
    CUSTOMER_SIGNALS   = ["customer_id", "email", "customer_name", "correo"]
    PRODUCT_SIGNALS    = ["product_name", "sku", "category", "brand"]

    normalized = [c.lower().strip().replace(" ", "_") for c in columns]

    def best_score(cols, signals):
        hits = 0
        for col in cols:
            for sig in signals:
                if fuzz.token_sort_ratio(col, sig) >= 70:
                    hits += 1
                    break
        return hits

    scores = {
        "pedidos":         best_score(normalized, ORDER_SIGNALS),
        "líneas de pedido": best_score(normalized, ORDER_LINE_SIGNALS),
        "clientes":        best_score(normalized, CUSTOMER_SIGNALS),
        "productos":       best_score(normalized, PRODUCT_SIGNALS),
    }

    best_type = max(scores.items(), key=lambda x: x[1])

    if best_type[1] == 0:
        return (
            "Las columnas no coinciden con ningún tipo conocido. "
            "Para pedidos: fecha, importe, id_pedido. "
            "Para líneas de pedido: order_item_id, is_primary_item. "
            "Para clientes: email, nombre, id_cliente. "
            "Para productos: nombre_producto, sku, categoria."
        )

    return (
        f"El tipo más cercano es '{best_type[0]}' "
        f"con {best_type[1]} columna(s) reconocida(s), "
        f"pero se necesitan al menos 2. "
        f"Revisa los nombres de columna."
    )

def _failed_response(import_id, filename, error_message):
    return {
        "import_id":            import_id,
        "filename":             filename,
        "file_format":          "unknown",
        "status":               "failed",
        "total_rows":           0,
        "valid_rows":           0,
        "invalid_rows":         0,
        "skipped_rows":         0,
        "sheets_processed":     0,
        "sheets":               [],
        "detected_type":        "unknown",
        "detection_confidence": 0.0,
        "error":                error_message,
        "relations_resolved":   None,
    }