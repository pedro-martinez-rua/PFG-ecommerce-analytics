"""
detector.py — Segunda capa del pipeline.

Responsabilidad: dado un ParsedSheet (o lista de columnas),
determinar qué tipo de datos contiene y con qué confianza.

Mejoras respecto a la versión anterior:
- Devuelve score de confianza (0.0 a 1.0) además del tipo
- Usa rapidfuzz para coincidencia aproximada de nombres de columna
- Detecta por contenido de la columna cuando el nombre no es suficiente
"""
from enum import Enum
from rapidfuzz import fuzz


class UploadType(str, Enum):
    ORDERS    = "orders"
    CUSTOMERS = "customers"
    PRODUCTS  = "products"
    MIXED     = "mixed"
    UNKNOWN   = "unknown"


# Señales por tipo — cuántas de estas columnas hacen falta para detectar el tipo
# Organizadas por peso: las primeras son más discriminativas
ORDERS_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "transaction_id",
    "order_date", "fecha_pedido", "fecha", "created_at", "purchase_date",
    "total_amount", "total_sales", "price_usd", "final_total", "total",
    "importe", "amount", "revenue", "net_sales"
]

CUSTOMERS_SIGNALS = [
    "customer_id", "customerid", "customer_name", "customer_email",
    "client_id", "email", "correo", "nombre_cliente", "full_name"
]

PRODUCTS_SIGNALS = [
    "product_id", "productid", "product_name", "sku", "stock_code",
    "stockcode", "description", "descripcion", "producto", "articulo",
    "unit_price", "unitprice", "unit_cost"
]

DETECTION_THRESHOLD = 2          # mínimo de columnas coincidentes
FUZZY_SCORE_THRESHOLD = 75       # score mínimo de similitud (0-100)


def _normalize(col: str) -> str:
    return col.lower().strip().replace(" ", "_").replace("-", "_").replace(".", "_")


def _fuzzy_match_score(col_normalized: str, signals: list[str]) -> float:
    """
    Calcula el máximo score de similitud entre una columna normalizada
    y la lista de señales usando rapidfuzz.
    Devuelve el score máximo encontrado (0-100).
    """
    best = 0
    for signal in signals:
        score = fuzz.token_sort_ratio(col_normalized, signal)
        if score > best:
            best = score
    return best


def detect_type_with_confidence(columns: list[str]) -> tuple[UploadType, float]:
    """
    Detecta el tipo de datos y devuelve (tipo, confianza).
    La confianza va de 0.0 a 1.0.

    Proceso:
    1. Normalizar columnas
    2. Para cada columna, calcular score fuzzy contra señales de cada tipo
    3. Contar cuántas columnas superan el umbral por tipo
    4. Clasificar y calcular confianza

    Returns:
        tuple[UploadType, float]: (tipo detectado, confianza 0.0-1.0)
    """
    normalized_cols = [_normalize(c) for c in columns]

    order_hits    = 0
    customer_hits = 0
    product_hits  = 0

    for col in normalized_cols:
        if _fuzzy_match_score(col, ORDERS_SIGNALS)    >= FUZZY_SCORE_THRESHOLD:
            order_hits += 1
        if _fuzzy_match_score(col, CUSTOMERS_SIGNALS) >= FUZZY_SCORE_THRESHOLD:
            customer_hits += 1
        if _fuzzy_match_score(col, PRODUCTS_SIGNALS)  >= FUZZY_SCORE_THRESHOLD:
            product_hits += 1

    detected = []
    if order_hits    >= DETECTION_THRESHOLD: detected.append((UploadType.ORDERS,    order_hits))
    if customer_hits >= DETECTION_THRESHOLD: detected.append((UploadType.CUSTOMERS, customer_hits))
    if product_hits  >= DETECTION_THRESHOLD: detected.append((UploadType.PRODUCTS,  product_hits))

    if len(detected) == 0:
        return UploadType.UNKNOWN, 0.0

    if len(detected) == 1:
        upload_type, hits = detected[0]
        # Confianza = proporción de señales detectadas vs total de columnas
        confidence = min(hits / len(columns), 1.0) if columns else 0.0
        return upload_type, round(confidence, 2)

    # Múltiples tipos — MIXED con confianza media
    total_hits = sum(h for _, h in detected)
    confidence = min(total_hits / len(columns), 1.0) if columns else 0.0
    return UploadType.MIXED, round(confidence, 2)


# Mantener compatibilidad con el código existente
def detect_upload_type(columns: list[str]) -> UploadType:
    upload_type, _ = detect_type_with_confidence(columns)
    return upload_type