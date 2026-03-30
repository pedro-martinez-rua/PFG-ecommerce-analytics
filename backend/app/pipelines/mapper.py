# Diccionario de aliases: campo canónico → lista de nombres posibles en CSVs reales
# Construido a partir del análisis de los datasets reales del proyecto:
# Maven, Online-eCommerce, ecommerce_sales, data_csv (Online Retail), jewelry

CANONICAL_ALIASES: dict[str, list[str]] = {

    # --- CAMPOS DE PEDIDO ---
    "external_id": [
        "order_id", "order_number", "orderid", "ordernumber",
        "invoice_no", "invoiceno", "transaction_id", "transactionid",
        "nº_pedido", "num_pedido", "pedido_id"
    ],
    "order_date": [
        "order_date", "date", "fecha", "fecha_pedido", "created_at",
        "invoice_date", "invoicedate", "transaction_date", "f_pedido"
    ],
    "total_amount": [
        "total_amount", "total_sales", "price_usd", "final_total",
        "total", "importe", "amount", "revenue", "pvp", "sales",
        "total_price_before_discount"
    ],
    "discount_amount": [
        "discount_amount", "discount", "descuento", "discount_value"
    ],
    "net_amount": [
        "net_amount", "price_after_discount", "net_total", "importe_neto"
    ],
    "shipping_cost": [
        "shipping_cost", "shipping", "envio", "freight", "delivery_cost"
    ],
    "cogs_amount": [
        "cogs_usd", "cogs", "cost", "total_cost", "coste", "unit_cost_total"
    ],
    "currency": [
        "currency", "moneda", "coin"
    ],
    "channel": [
        "channel", "canal", "source", "fuente", "sales_channel"
    ],
    "status": [
        "status", "estado", "order_status", "estado_pedido"
    ],
    "payment_method": [
        "payment_method", "payment", "metodo_pago", "forma_pago", "payment_type"
    ],
    "shipping_country": [
        "country", "pais", "shipping_country", "ship_country", "destination"
    ],
    "shipping_region": [
        "state_code", "state", "region", "provincia", "comunidad"
    ],
    "delivery_days": [
        "delivery_days", "dias_entrega", "days_to_deliver", "lead_time"
    ],
    "is_returned": [
        "return_status", "returned", "devuelto", "is_returned", "refunded"
    ],
    "session_id": [
        "website_session_id", "session_id", "visit_id"
    ],
    "utm_source": [
        "utm_source", "source", "fuente_trafico"
    ],
    "utm_campaign": [
        "utm_campaign", "campaign", "campaña"
    ],
    "device_type": [
        "device_type", "device", "dispositivo"
    ],

    # --- CAMPOS DE CLIENTE ---
    "customer_external_id": [
        "customer_id", "customerid", "user_id", "userid",
        "client_id", "clientid", "id_cliente"
    ],
    "customer_email": [
        "customer_email", "email", "correo", "mail", "email_cliente"
    ],
    "customer_name": [
        "customer_name", "nombre_cliente", "client_name", "nombre"
    ],

    # --- CAMPOS DE PRODUCTO ---
    "product_external_id": [
        "product_id", "productid", "stock_code", "stockcode",
        "sku", "item_id", "id_producto"
    ],
    "product_name": [
        "product_name", "product", "description", "descripcion",
        "nombre_producto", "item_name", "producto", "articulo", "item"
    ],
    "sku": [
        "sku", "stock_code", "stockcode", "reference", "referencia", "codigo"
    ],
    "category": [
        "category", "categoria", "product_category", "tipo"
    ],
    "brand": [
        "brand", "marca", "manufacturer", "fabricante"
    ],
    "quantity": [
        "quantity", "qty", "units", "unidades", "cantidad",
        "items_purchased", "num_units"
    ],
    "unit_price": [
        "unit_price", "unitprice", "price", "precio", "precio_unitario",
        "price_usd", "pvp_unitario", "sales"
    ],
    "unit_cost": [
        "cogs_usd", "unit_cost", "cost", "coste_unitario", "cost_usd"
    ],
    "line_total": [
        "line_total", "total_line", "subtotal", "line_amount",
        "total_sales", "final_total"
    ],
}


def infer_mapping(columns: list[str]) -> dict[str, str]:
    """
    Recibe las columnas originales del CSV y devuelve un diccionario
    {nombre_original: campo_canónico}.

    Solo mapea las columnas que encuentra — las que no coinciden
    con ningún alias se ignoran (irán a extra_attributes).

    Ejemplo:
        infer_mapping(["Order_Number", "Order_Date", "Total_Sales", "Brand"])
        → {
            "Order_Number": "external_id",
            "Order_Date":   "order_date",
            "Total_Sales":  "total_amount",
            "Brand":        "brand"
          }
    """
    mapping = {}

    for col in columns:
        col_normalized = col.lower().strip().replace(" ", "_").replace("-", "_")

        for canonical, aliases in CANONICAL_ALIASES.items():
            if col_normalized in aliases:
                mapping[col] = canonical
                break  # una columna solo puede mapearse a un campo canónico

    return mapping


def apply_mapping(row: dict, mapping: dict[str, str]) -> tuple[dict, dict]:
    """
    Aplica el mapping a una fila del CSV.

    Devuelve dos diccionarios:
    - canonical: campos mapeados al schema canónico
    - extra:     campos que no tienen mapping (van a extra_attributes)

    Ejemplo:
        row     = {"Order_Number": "1001", "Brand": "Samsung", "Supervisor": "Juan"}
        mapping = {"Order_Number": "external_id", "Brand": "brand"}
        →
        canonical = {"external_id": "1001", "brand": "Samsung"}
        extra     = {"Supervisor": "Juan"}
    """
    canonical = {}
    extra = {}

    for col, value in row.items():
        if col in mapping:
            canonical[mapping[col]] = value
        else:
            extra[col] = value

    return canonical, extra