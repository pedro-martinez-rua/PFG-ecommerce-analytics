"""
import_orchestrator.py — Capa de orquestación del pipeline.

Coordina todas las capas en orden:
file_parser → detector → mapper → validator → transformer → canonical_loader

Gestiona el ciclo de vida completo de un Import:
- Crea el registro Import en BD al inicio
- Crea un ImportSheet por cada hoja procesada
- Actualiza estados en tiempo real
- Garantiza que los datos del usuario nunca salen del servidor
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
    apply_mapping
)
from app.pipelines.transformer import transform_row
from app.pipelines.validator import validate_dataframe, build_validation_summary, RowStatus

from app.models.import_record import Import
from app.models.import_sheet import ImportSheet
from app.models.raw_upload import RawUpload
from app.models.order import Order
from app.models.order_line import OrderLine
from app.models.customer import Customer
from app.models.product import Product


def run_import(
    db: Session,
    tenant_id: str,
    filename: str,
    file_content: bytes
) -> dict:
    """
    Punto de entrada principal del pipeline.
    Procesa un fichero completo (CSV o XLSX) y devuelve el resultado.

    SEGURIDAD:
    - file_content nunca se escribe en disco — solo se trabaja en memoria
    - tenant_id siempre viene del JWT — nunca del body del request
    - Los datos del usuario no se envían a ningún servicio externo en esta capa

    Returns:
        dict con el resumen completo del import
    """
    file_size = len(file_content)

    # Detectar formato
    file_format = "xlsx" if filename.lower().endswith((".xlsx", ".xls")) else "csv"

    # Crear registro Import en BD
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

    # FASE 1 — Parsing
    try:
        sheets = parse_file(file_content, filename)
    except ValueError as e:
        import_record.status = "failed"
        import_record.error_message = str(e)
        import_record.completed_at = datetime.now(timezone.utc)
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

    # Actualizar Import con totales
    total_rows = total_valid + total_invalid + total_skipped
    import_record.total_rows   = total_rows
    import_record.valid_rows   = total_valid
    import_record.invalid_rows = total_invalid
    import_record.skipped_rows = total_skipped
    import_record.status       = "completed" if total_invalid == 0 else "completed_with_errors"
    import_record.completed_at = datetime.now(timezone.utc)

    # Tipo detectado: usar el del primer sheet (o mixed si hay varios tipos distintos)
    detected_types = list({r["detected_type"] for r in sheet_results})
    import_record.detected_type        = detected_types[0] if len(detected_types) == 1 else "mixed"
    import_record.detection_confidence = sheet_results[0]["detection_confidence"] if sheet_results else 0.0

    db.commit()

    return {
        "import_id":           import_id,
        "filename":            filename,
        "file_format":         file_format,
        "status":              import_record.status,
        "total_rows":          total_rows,
        "valid_rows":          total_valid,
        "invalid_rows":        total_invalid,
        "skipped_rows":        total_skipped,
        "sheets_processed":    len(sheet_results),
        "sheets":              sheet_results,
        "detected_type":       import_record.detected_type,
        "detection_confidence": import_record.detection_confidence,
    }


def _process_sheet(
    db: Session,
    tenant_id: str,
    import_id: str,
    sheet: ParsedSheet
) -> dict:
    """
    Procesa una sola hoja: detecta tipo, mapea, valida, transforma y carga.
    Crea un ImportSheet en BD y actualiza su estado.
    """

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

    # FASE 2a — Detección de tipo
    upload_type, confidence = detect_type_with_confidence(sheet.columns)
    import_sheet.detected_type        = upload_type.value
    import_sheet.detection_confidence = confidence
    db.commit()

    # Si es UNKNOWN con baja confianza — guardar en staging y reportar
    if upload_type == UploadType.UNKNOWN or confidence < 0.3:
        _stage_all_rows(db, tenant_id, import_id, sheet_id, sheet, upload_type.value)
        import_sheet.status      = "completed"
        import_sheet.valid_rows  = 0
        import_sheet.invalid_rows = sheet.row_count
        db.commit()
        return {
            "sheet_name":          sheet.sheet_name,
            "detected_type":       upload_type.value,
            "detection_confidence": confidence,
            "valid_rows":          0,
            "invalid_rows":        sheet.row_count,
            "skipped_rows":        0,
            "note":                "Tipo de datos no reconocido — datos guardados en staging para revisión"
        }

    # FASE 2b — Mapping de columnas
    # Primero intentar usar mapping guardado de imports anteriores del mismo tenant
    saved_mapping = get_saved_mapping(db, tenant_id, upload_type.value)
    if saved_mapping:
        mapping = saved_mapping
    else:
        mapping_with_confidence = infer_mapping_with_confidence(sheet.columns)
        mapping = {col: info["canonical"] for col, info in mapping_with_confidence.items() if info["canonical"]}
        persist_mapping(db, tenant_id, upload_type.value, mapping_with_confidence, import_id)

    # FASE 2c — Aplicar mapping al DataFrame completo
    import pandas as pd
    df = sheet.dataframe.copy()
    # Renombrar columnas al canonical usando el mapping
    rename_map = {col: mapping[col] for col in df.columns if col in mapping}
    df_canonical = df.rename(columns=rename_map)

    # FASE 2d — Validación con Pandera
    validation_results, processable_df = validate_dataframe(df_canonical, upload_type.value)
    summary = build_validation_summary(validation_results)

    # Guardar staging para TODAS las filas (válidas e inválidas)
    for result in validation_results:
        row_dict = df.iloc[result.row_index].where(pd.notna(df.iloc[result.row_index]), None).to_dict() \
                   if result.row_index < len(df) else {}

        canonical_dict = df_canonical.iloc[result.row_index].where(
            pd.notna(df_canonical.iloc[result.row_index]), None
        ).to_dict() if result.row_index < len(df_canonical) else {}

        raw = RawUpload(
            tenant_id=tenant_id,
            upload_id=import_id,         # reutilizar upload_id como import_id
            import_id=import_id,
            sheet_id=sheet_id,
            upload_type=upload_type.value,
            filename=sheet.sheet_name,
            row_index=result.row_index,
            raw_data=row_dict,           # datos originales sin modificar
            mapped_data=canonical_dict,  # tras el mapping
            validation_errors=[e for e in result.errors],
            status=result.status.value,
            skip_reason=result.warnings[0]["message"] if result.status.value == "skipped" and result.warnings else None
        )
        db.add(raw)

    try:
        db.commit()
    except Exception:
        db.rollback()

    # FASE 2e — Transformar y cargar al schema canónico solo filas procesables
    valid_loaded = 0
    for _, row in processable_df.iterrows():
        row_dict = row.where(pd.notna(row), None).to_dict()
        extra = {col: row_dict.get(col) for col in df.columns
                 if col not in mapping and col in df.columns}

        try:
            transformed = transform_row(row_dict)

            if upload_type in (UploadType.ORDERS, UploadType.MIXED):
                _write_order(db, tenant_id, transformed, extra)
            elif upload_type == UploadType.CUSTOMERS:
                _write_customer(db, tenant_id, transformed, extra)
            elif upload_type == UploadType.PRODUCTS:
                _write_product(db, tenant_id, transformed, extra)

            db.commit()
            valid_loaded += 1
        except Exception as e:
            db.rollback()

    # Actualizar ImportSheet con resultados
    import_sheet.valid_rows   = valid_loaded
    import_sheet.invalid_rows = summary["invalid_rows"]
    import_sheet.skipped_rows = summary["skipped_rows"]
    import_sheet.status       = "completed"
    db.commit()

    return {
        "sheet_name":            sheet.sheet_name,
        "detected_type":         upload_type.value,
        "detection_confidence":  round(confidence, 2),
        "valid_rows":            valid_loaded,
        "invalid_rows":          summary["invalid_rows"],
        "skipped_rows":          summary["skipped_rows"],
        "top_errors":            summary.get("top_errors", []),
    }


def _stage_all_rows(db, tenant_id, import_id, sheet_id, sheet, upload_type):
    """Guarda todas las filas en staging con status=invalid cuando el tipo es desconocido."""
    import pandas as pd
    for idx, row in sheet.dataframe.iterrows():
        row_dict = row.where(pd.notna(row), None).to_dict()
        raw = RawUpload(
            tenant_id=tenant_id,
            upload_id=import_id,
            import_id=import_id,
            sheet_id=sheet_id,
            upload_type=upload_type,
            filename=sheet.sheet_name,
            row_index=int(idx),
            raw_data=row_dict,
            status="invalid",
            validation_errors=[{"error_type": "unknown_type",
                                 "message": "No se pudo determinar el tipo de datos"}]
        )
        db.add(raw)
    try:
        db.commit()
    except Exception:
        db.rollback()


def _failed_response(import_id, filename, error_message):
    return {
        "import_id":    import_id,
        "filename":     filename,
        "status":       "failed",
        "total_rows":   0,
        "valid_rows":   0,
        "invalid_rows": 0,
        "skipped_rows": 0,
        "error":        error_message
    }


def _write_order(db, tenant_id, data, extra):
    if data.get("external_id"):
        existing = db.query(Order).filter_by(
            tenant_id=tenant_id,
            external_id=str(data["external_id"])
        ).first()
        if existing:
            return

    order = Order(
        tenant_id=tenant_id,
        external_id=str(data["external_id"]) if data.get("external_id") else None,
        order_date=data.get("order_date"),
        total_amount=data.get("total_amount"),
        discount_amount=data.get("discount_amount"),
        net_amount=data.get("net_amount"),
        shipping_cost=data.get("shipping_cost"),
        cogs_amount=data.get("cogs_amount"),
        currency=data.get("currency"),
        channel=data.get("channel"),
        status=data.get("status"),
        payment_method=data.get("payment_method"),
        shipping_country=data.get("shipping_country"),
        shipping_region=data.get("shipping_region"),
        delivery_days=data.get("delivery_days"),
        is_returned=data.get("is_returned", False),
        device_type=data.get("device_type"),
        utm_source=data.get("utm_source"),
        utm_campaign=data.get("utm_campaign"),
        session_id=data.get("session_id"),
        extra_attributes=extra or {}
    )
    db.add(order)

    if data.get("product_name") or data.get("sku"):
        db.flush()
        line = OrderLine(
            tenant_id=tenant_id,
            order_id=order.id,
            product_name=data.get("product_name"),
            sku=data.get("sku"),
            category=data.get("category"),
            brand=data.get("brand"),
            quantity=data.get("quantity"),
            unit_price=data.get("unit_price"),
            unit_cost=data.get("unit_cost"),
            line_total=data.get("line_total") or data.get("total_amount"),
            extra_attributes={}
        )
        db.add(line)


def _write_customer(db, tenant_id, data, extra):
    customer = Customer(
        tenant_id=tenant_id,
        external_id=str(data["customer_external_id"]) if data.get("customer_external_id") else None,
        email=data.get("customer_email"),
        full_name=data.get("customer_name"),
        extra_attributes=extra or {}
    )
    db.add(customer)


def _write_product(db, tenant_id, data, extra):
    product = Product(
        tenant_id=tenant_id,
        external_id=str(data["product_external_id"]) if data.get("product_external_id") else None,
        name=data.get("product_name", "Sin nombre"),
        sku=data.get("sku"),
        category=data.get("category"),
        brand=data.get("brand"),
        unit_cost=data.get("unit_cost"),
        unit_price=data.get("unit_price"),
        extra_attributes=extra or {}
    )
    db.add(product)