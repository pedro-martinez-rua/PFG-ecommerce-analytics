from enum import Enum


class UploadType(str, Enum):
    ORDERS    = "orders"
    CUSTOMERS = "customers"
    PRODUCTS  = "products"
    MIXED     = "mixed"
    UNKNOWN   = "unknown"


# Columnas que identifican cada tipo de entidad.
# Si el CSV contiene suficientes de estas, se clasifica como ese tipo.
ORDERS_SIGNALS = {
    "order_id", "order_number", "invoice_no", "invoiceno",
    "transaction_id", "order_date", "fecha_pedido", "fecha",
    "created_at", "total_amount", "total_sales", "price_usd",
    "final_total", "total", "importe", "amount"
}

CUSTOMERS_SIGNALS = {
    "customer_id", "customer_name", "customer_email",
    "client_id", "email", "correo", "nombre_cliente"
}

PRODUCTS_SIGNALS = {
    "product_id", "product_name", "sku", "stock_code",
    "stockcode", "description", "producto", "articulo",
    "category", "brand", "unit_price", "unitprice"
}

# Mínimo de columnas coincidentes para clasificar como ese tipo
DETECTION_THRESHOLD = 2


def detect_upload_type(columns: list[str]) -> UploadType:
    """
    Recibe la lista de columnas del CSV y devuelve el tipo detectado.

    Proceso:
    1. Normaliza los nombres de columna (lowercase, sin espacios)
    2. Cuenta cuántas columnas coinciden con cada tipo
    3. Si supera el umbral, clasifica como ese tipo
    4. Si supera en más de uno, devuelve MIXED

    Ejemplos de datasets reales:
    - Maven orders.csv   → ORDERS  (order_id, created_at, price_usd, cogs_usd)
    - Online-eCommerce   → ORDERS  (Order_Number, Order_Date, Total_Sales)
    - ecommerce_sales    → ORDERS  (Transaction_ID, Customer_ID, Final_Total)
    - jewelry.csv        → UNKNOWN (sin cabecera legible)
    """
    # Normalizar columnas: lowercase y sin espacios ni guiones
    normalized = {
        col.lower().strip().replace(" ", "_").replace("-", "_")
        for col in columns
    }

    # Contar coincidencias por tipo
    order_score    = len(normalized & ORDERS_SIGNALS)
    customer_score = len(normalized & CUSTOMERS_SIGNALS)
    product_score  = len(normalized & PRODUCTS_SIGNALS)

    # Clasificar
    detected = []
    if order_score    >= DETECTION_THRESHOLD: detected.append(UploadType.ORDERS)
    if customer_score >= DETECTION_THRESHOLD: detected.append(UploadType.CUSTOMERS)
    if product_score  >= DETECTION_THRESHOLD: detected.append(UploadType.PRODUCTS)

    if len(detected) == 0: return UploadType.UNKNOWN
    if len(detected) == 1: return detected[0]
    return UploadType.MIXED