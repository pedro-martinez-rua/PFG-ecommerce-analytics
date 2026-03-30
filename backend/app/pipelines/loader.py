import uuid
import pandas as pd
from sqlalchemy.orm import Session
from app.pipelines.detector import detect_upload_type, UploadType
from app.pipelines.mapper import infer_mapping, apply_mapping
from app.pipelines.transformer import transform_row
from app.models.raw_upload import RawUpload
from app.models.order import Order
from app.models.order_line import OrderLine
from app.models.customer import Customer
from app.models.product import Product


def load_csv(
    db: Session,
    tenant_id: str,
    filename: str,
    file_content: bytes
) -> dict:
    """
    Punto de entrada del pipeline. Recibe el CSV como bytes y lo procesa completo.

    Flujo:
    1. Leer CSV con pandas
    2. Detectar tipo de upload
    3. Inferir mapping de columnas
    4. Por cada fila: guardar en staging + transformar + escribir en canónico
    5. Devolver resumen del proceso

    Gestión de errores por fila:
    - Si una fila falla (ej: date nula, constraint violation), se hace rollback
      solo de esa fila y se continúa con la siguiente.
    - El error se registra en raw_uploads con status="error".
    """
    upload_id = str(uuid.uuid4())
    errors = []

    # 1. Leer CSV
    try:
        df = _read_csv(file_content)
    except Exception as e:
        return {
            "upload_id": upload_id,
            "upload_type": "unknown",
            "total_rows": 0,
            "processed": 0,
            "errors": 1,
            "error_details": [f"No se pudo leer el fichero: {str(e)}"]
        }

    columns = list(df.columns)
    total_rows = len(df)

    # 2. Detectar tipo
    upload_type = detect_upload_type(columns)

    # 3. Inferir mapping
    mapping = infer_mapping(columns)

    # 4. Procesar fila por fila — cada fila es una transacción independiente
    processed = 0
    for row_index, row in df.iterrows():
        row_dict = row.where(pd.notna(row), None).to_dict()

        try:
            # 4a. Mapear y transformar
            canonical, extra = apply_mapping(row_dict, mapping)
            transformed = transform_row(canonical)

            # 4b. Validación mínima antes de intentar escribir en BD
            # Para orders: necesitamos order_date obligatoriamente
            if upload_type in (UploadType.ORDERS, UploadType.MIXED):
                if not transformed.get("order_date"):
                    errors.append(
                        f"Fila {row_index}: sin fecha de pedido — fila omitida"
                    )
                    continue  # saltar esta fila sin tocar la BD

            # 4c. Guardar en staging
            raw = RawUpload(
                tenant_id=tenant_id,
                upload_id=upload_id,
                upload_type=upload_type.value,
                filename=filename,
                row_index=int(row_index),
                raw_data=row_dict,
                status="pending"
            )
            db.add(raw)

            # 4d. Escribir en schema canónico
            if upload_type in (UploadType.ORDERS, UploadType.MIXED):
                _write_order(db, tenant_id, transformed, extra)
            elif upload_type == UploadType.CUSTOMERS:
                _write_customer(db, tenant_id, transformed, extra)
            elif upload_type == UploadType.PRODUCTS:
                _write_product(db, tenant_id, transformed, extra)

            # 4e. Commit de esta fila
            db.commit()
            raw.status = "processed"
            processed += 1

        except Exception as e:
            # Rollback solo de esta fila — la sesión queda limpia para la siguiente
            db.rollback()
            errors.append(f"Fila {row_index}: {str(e)[:120]}")

            # Guardar el error en staging de forma independiente
            try:
                error_raw = RawUpload(
                    tenant_id=tenant_id,
                    upload_id=upload_id,
                    upload_type=upload_type.value,
                    filename=filename,
                    row_index=int(row_index),
                    raw_data=row_dict,
                    status="error",
                    error_message=str(e)[:500]
                )
                db.add(error_raw)
                db.commit()
            except Exception:
                db.rollback()

    return {
        "upload_id": upload_id,
        "upload_type": upload_type.value,
        "total_rows": total_rows,
        "processed": processed,
        "errors": len(errors),
        "error_details": errors[:10]
    }


def _read_csv(content: bytes) -> pd.DataFrame:
    """
    Lee un CSV con detección automática de encoding y delimitador.
    Intenta UTF-8 primero, luego latin-1 (cubre exports europeos).
    """
    import io

    for encoding in ["utf-8", "latin-1", "utf-8-sig", "cp1252"]:
        for separator in [",", ";", "\t"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    sep=separator,
                    on_bad_lines="skip",
                    dtype=str              # todo como string — el transformer convierte
                )
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue

    raise ValueError("No se pudo leer el CSV con ningún encoding o delimitador conocido")


def _write_order(db: Session, tenant_id: str, data: dict, extra: dict):
    """
    Escribe una fila de pedido en la tabla orders.
    Incluye deduplicación por external_id + tenant_id.
    """
    # Deduplicación
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
        order_date=data.get("order_date"),          # ya validado como no-None antes
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

    # Si hay datos de producto en la misma fila, crear order_line
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


def _write_customer(db: Session, tenant_id: str, data: dict, extra: dict):
    """Escribe un cliente en la tabla customers."""
    customer = Customer(
        tenant_id=tenant_id,
        external_id=str(data["customer_external_id"]) if data.get("customer_external_id") else None,
        email=data.get("customer_email"),
        full_name=data.get("customer_name"),
        extra_attributes=extra or {}
    )
    db.add(customer)


def _write_product(db: Session, tenant_id: str, data: dict, extra: dict):
    """Escribe un producto en la tabla products."""
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