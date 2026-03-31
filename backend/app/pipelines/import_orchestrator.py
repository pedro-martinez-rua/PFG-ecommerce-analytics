"""
import_orchestrator.py — Capa de orquestación del pipeline.

Coordina todas las capas en orden:
file_parser → detector → mapper → validator → transformer → canonical_loader

Gestiona el ciclo de vida completo de un Import:
- Crea el registro Import en BD al inicio
- Crea un ImportSheet por cada hoja procesada
- Bulk inserts para máximo rendimiento
- Staging solo para filas inválidas
- Deduplicación en memoria — sin queries por fila
- Los datos del usuario nunca salen del servidor
"""
import uuid
from datetime import datetime, timezone
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

from app.models.import_record import Import
from app.models.import_sheet import ImportSheet
from app.models.raw_upload import RawUpload
from app.models.order import Order
from app.models.order_line import OrderLine
from app.models.customer import Customer
from app.models.product import Product

# PUNTO DE ENTRADA PRINCIPAL
def run_import(
    db: Session,
    tenant_id: str,
    filename: str,
    file_content: bytes
) -> dict:
    """
    Punto de entrada principal del pipeline.

    SEGURIDAD:
    - file_content nunca se escribe en disco — solo memoria
    - tenant_id siempre viene del JWT — nunca del body del request
    - Ningún dato del usuario se envía a servicios externos en esta capa
    """
    file_size   = len(file_content)
    file_format = "xlsx" if filename.lower().endswith((".xlsx", ".xls")) else "csv"

    # Crear registro Import
    import_record = Import(
        tenant_id=tenant_id,
        filename=filename,
        file_format=file_format,
        file_size_bytes=file_size,
        status="processing"
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)
    import_id = str(import_record.id)

    # FASE 1 — Parsing del fichero
    try:
        sheets = parse_file(file_content, filename)
    except ValueError as e:
        import_record.status        = "failed"
        import_record.error_message = str(e)
        import_record.completed_at  = datetime.now(timezone.utc)
        db.commit()
        return _failed_response(import_id, filename, str(e))

    # FASE 2 — Procesar cada hoja
    total_valid = total_invalid = total_skipped = 0
    sheet_results = []

    for sheet in sheets:
        result = _process_sheet(db, tenant_id, import_id, sheet)
        sheet_results.append(result)
        total_valid   += result["valid_rows"]
        total_invalid += result["invalid_rows"]
        total_skipped += result["skipped_rows"]

    # Actualizar Import con totales finales
    total_rows = total_valid + total_invalid + total_skipped
    import_record.total_rows    = total_rows
    import_record.valid_rows    = total_valid
    import_record.invalid_rows  = total_invalid
    import_record.skipped_rows  = total_skipped
    import_record.status        = "completed" if total_invalid == 0 else "completed_with_errors"
    import_record.completed_at  = datetime.now(timezone.utc)

    detected_types = list({r["detected_type"] for r in sheet_results})
    import_record.detected_type        = detected_types[0] if len(detected_types) == 1 else "mixed"
    import_record.detection_confidence = sheet_results[0]["detection_confidence"] if sheet_results else 0.0

    db.commit()

    return {
        "import_id":            import_id,
        "filename":             filename,
        "file_format":          file_format,
        "status":               import_record.status,
        "total_rows":           total_rows,
        "valid_rows":           total_valid,
        "invalid_rows":         total_invalid,
        "skipped_rows":         total_skipped,
        "sheets_processed":     len(sheet_results),
        "sheets":               sheet_results,
        "detected_type":        import_record.detected_type,
        "detection_confidence": import_record.detection_confidence,
    }

# PROCESAMIENTO DE UNA HOJA
def _process_sheet(
    db: Session,
    tenant_id: str,
    import_id: str,
    sheet: ParsedSheet
) -> dict:
    """
    Procesa una sola hoja del fichero.
    Flujo: detección → mapping → validación → bulk insert canónico
    """
    BATCH_SIZE = 1000

    # Crear ImportSheet
    import_sheet = ImportSheet(
        import_id=import_id,
        tenant_id=tenant_id,
        sheet_name=sheet.sheet_name,
        status="processing",
        total_rows=sheet.row_count
    )
    db.add(import_sheet)
    db.commit()
    db.refresh(import_sheet)
    sheet_id = str(import_sheet.id)

    # FASE 2a — Detección de tipo con confianza
    upload_type, confidence = detect_type_with_confidence(sheet.columns)
    import_sheet.detected_type        = upload_type.value
    import_sheet.detection_confidence = confidence
    db.commit()

    # Tipo desconocido — guardar en staging y devolver diagnóstico útil
    if upload_type == UploadType.UNKNOWN or confidence < 0.3:
        _stage_all_rows(db, tenant_id, import_id, sheet_id, sheet, upload_type.value)
        import_sheet.status       = "completed"
        import_sheet.valid_rows   = 0
        import_sheet.invalid_rows = sheet.row_count
        db.commit()

        columns_found = sheet.columns[:20]
        hint = _build_unrecognized_hint(sheet.columns)

        return {
            "sheet_name":           sheet.sheet_name,
            "detected_type":        "unknown",
            "detection_confidence": round(confidence, 2),
            "valid_rows":           0,
            "invalid_rows":         sheet.row_count,
            "skipped_rows":         0,
            "top_errors":           [],
            "columns_found":        columns_found,
            "diagnosis":            hint,
            "note": (
                f"No se reconoció el tipo de datos de esta hoja. "
                f"Se encontraron {len(sheet.columns)} columnas. "
                f"{hint}"
            )
        }

    # FASE 2b — Mapping de columnas
    saved_mapping = get_saved_mapping(db, tenant_id, upload_type.value)
    if saved_mapping:
        mapping = saved_mapping
    else:
        mapping_with_confidence = infer_mapping_with_confidence(sheet.columns)
        mapping = {
            col: info["canonical"]
            for col, info in mapping_with_confidence.items()
            if info["canonical"]
        }
        persist_mapping(db, tenant_id, upload_type.value, mapping_with_confidence, import_id)

    # FASE 2c — Aplicar mapping al DataFrame
    import pandas as pd
    df           = sheet.dataframe.copy()
    rename_map   = {col: mapping[col] for col in df.columns if col in mapping}
    df_canonical = df.rename(columns=rename_map)

    # FASE 2d — Validación con Pandera
    validation_results, processable_df = validate_dataframe(df_canonical, upload_type.value)
    summary = build_validation_summary(validation_results)

    # Staging SOLO para filas inválidas
    invalid_results = [
        r for r in validation_results
        if r.status.value in ("invalid", "error")
    ]
    if invalid_results:
        staging_records = []
        for result in invalid_results:
            row_dict = df.iloc[result.row_index].where(
                pd.notna(df.iloc[result.row_index]), None
            ).to_dict() if result.row_index < len(df) else {}

            staging_records.append({
                "id":                str(uuid.uuid4()),
                "tenant_id":         tenant_id,
                "upload_id":         import_id,
                "import_id":         import_id,
                "sheet_id":          sheet_id,
                "upload_type":       upload_type.value,
                "filename":          sheet.sheet_name,
                "row_index":         result.row_index,
                "raw_data":          row_dict,
                "mapped_data":       {},
                "transformed_data":  {},
                "validation_errors": result.errors,
                "status":            result.status.value,
                "skip_reason":       None,
                "error_message":     None,
                "processed_at":      None,
            })

        try:
            db.bulk_insert_mappings(RawUpload, staging_records)
            db.commit()
        except Exception:
            db.rollback()

    # FASE 2e — Bulk insert al schema canónico
    valid_loaded = 0

    if not processable_df.empty:
        if upload_type in (UploadType.ORDERS, UploadType.MIXED):
            existing_ids = _get_existing_external_ids(db, tenant_id, Order)
            valid_loaded  = _bulk_write_orders(
                db, tenant_id, processable_df, df, mapping, existing_ids, BATCH_SIZE
            )
        elif upload_type == UploadType.CUSTOMERS:
            existing_ids = _get_existing_external_ids(db, tenant_id, Customer)
            valid_loaded  = _bulk_write_customers(
                db, tenant_id, processable_df, existing_ids, BATCH_SIZE
            )
        elif upload_type == UploadType.PRODUCTS:
            existing_ids = _get_existing_external_ids(db, tenant_id, Product)
            valid_loaded  = _bulk_write_products(
                db, tenant_id, processable_df, existing_ids, BATCH_SIZE
            )

    # Actualizar ImportSheet con resultados finales
    import_sheet.valid_rows   = valid_loaded
    import_sheet.invalid_rows = summary["invalid_rows"]
    import_sheet.skipped_rows = summary["skipped_rows"]
    import_sheet.status       = "completed"
    db.commit()

    return {
        "sheet_name":           sheet.sheet_name,
        "detected_type":        upload_type.value,
        "detection_confidence": round(confidence, 2),
        "valid_rows":           valid_loaded,
        "invalid_rows":         summary["invalid_rows"],
        "skipped_rows":         summary["skipped_rows"],
        "top_errors":           summary.get("top_errors", []),
    }

# HELPERS DE RENDIMIENTO
def _get_existing_external_ids(db: Session, tenant_id: str, model) -> set:
    """
    Carga todos los external_ids existentes para este tenant en UN solo query.
    Evita hacer un SELECT por cada fila — clave para el rendimiento con ficheros grandes.
    """
    rows = db.query(model.external_id).filter(
        model.tenant_id == tenant_id,
        model.external_id.isnot(None)
    ).all()
    return {r[0] for r in rows}

def _bulk_write_orders(
    db, tenant_id, processable_df, original_df, mapping, existing_ids, batch_size
) -> int:
    """
    Inserta pedidos y sus líneas en bulk.
    Deduplicación en memoria usando el set de external_ids precargado.
    """
    import pandas as pd
    orders_batch = []
    lines_batch  = []
    loaded       = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["external_id"]) if transformed.get("external_id") else None

        # Deduplicación en memoria — sin tocar la BD
        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        extra = {
            col: row_dict.get(col)
            for col in original_df.columns
            if col not in mapping and col in original_df.columns
        }

        order_id = str(uuid.uuid4())
        orders_batch.append({
            "id":               order_id,
            "tenant_id":        tenant_id,
            "customer_id":      None,
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
            "extra_attributes": extra or {},
        })

        if transformed.get("product_name") or transformed.get("sku"):
            lines_batch.append({
                "id":              str(uuid.uuid4()),
                "tenant_id":       tenant_id,
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

    # Último batch
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

def _bulk_write_customers(
    db, tenant_id, processable_df, existing_ids, batch_size
) -> int:
    import pandas as pd
    batch  = []
    loaded = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["customer_external_id"]) \
                 if transformed.get("customer_external_id") else None
        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        batch.append({
            "id":               str(uuid.uuid4()),
            "tenant_id":        tenant_id,
            "external_id":      ext_id,
            "email":            transformed.get("customer_email"),
            "full_name":        transformed.get("customer_name"),
            "country":          transformed.get("country"),
            "region":           transformed.get("region"),
            "total_orders":     0,
            "total_spent":      0,
            "avg_order_value":  None,
            "customer_rating":  None,
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
    db, tenant_id, processable_df, existing_ids, batch_size
) -> int:
    import pandas as pd
    batch  = []
    loaded = 0

    for _, row in processable_df.iterrows():
        row_dict    = row.where(pd.notna(row), None).to_dict()
        transformed = transform_row(row_dict)

        ext_id = str(transformed["product_external_id"]) \
                 if transformed.get("product_external_id") else None
        if ext_id and ext_id in existing_ids:
            continue
        if ext_id:
            existing_ids.add(ext_id)

        batch.append({
            "id":               str(uuid.uuid4()),
            "tenant_id":        tenant_id,
            "external_id":      ext_id,
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
    """
    Guarda todas las filas en staging cuando el tipo es desconocido.
    Usa bulk insert para eficiencia.
    """
    import pandas as pd
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
    """
    Construye un mensaje de diagnóstico explicando por qué no se reconoció
    la hoja y qué necesitaría el usuario para que sea procesable.
    """
    from rapidfuzz import fuzz

    ORDER_SIGNALS    = ["order_date", "total_amount", "order_id", "fecha", "importe"]
    CUSTOMER_SIGNALS = ["customer_id", "email", "customer_name", "correo"]
    PRODUCT_SIGNALS  = ["product_name", "sku", "category", "brand"]

    normalized = [c.lower().strip().replace(" ", "_") for c in columns]

    def best_score(cols, signals):
        hits = 0
        for col in cols:
            for sig in signals:
                if fuzz.token_sort_ratio(col, sig) >= 70:
                    hits += 1
                    break
        return hits

    order_hits    = best_score(normalized, ORDER_SIGNALS)
    customer_hits = best_score(normalized, CUSTOMER_SIGNALS)
    product_hits  = best_score(normalized, PRODUCT_SIGNALS)

    best_type = max(
        [("pedidos", order_hits), ("clientes", customer_hits), ("productos", product_hits)],
        key=lambda x: x[1]
    )

    if best_type[1] == 0:
        return (
            "Las columnas no coinciden con ningún tipo conocido. "
            "Para pedidos necesitas columnas como: fecha, importe, id_pedido. "
            "Para clientes: email, nombre, id_cliente. "
            "Para productos: nombre_producto, sku, categoria."
        )

    return (
        f"El tipo más cercano detectado es '{best_type[0]}' "
        f"con {best_type[1]} columna(s) reconocida(s), "
        f"pero se necesitan al menos 2 para procesar automáticamente. "
        f"Revisa los nombres de columna o renómbralos a nombres estándar."
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
    }