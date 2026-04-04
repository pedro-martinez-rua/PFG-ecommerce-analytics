"""
detector.py — Segunda capa del pipeline.

Responsabilidad: dado un ParsedSheet, determinar qué tipo de datos contiene
y con qué confianza.

Tipos soportados:
- orders:      pedidos con fecha y/o importe
- order_lines: líneas de pedido (order_items) sin fecha propia
- customers:   clientes con email o ID
- products:    catálogo de productos
- mixed:       combinación de tipos
- unknown:     no reconocido
"""
from enum import Enum
from rapidfuzz import fuzz


class UploadType(str, Enum):
    ORDERS      = "orders"
    ORDER_LINES = "order_lines"
    CUSTOMERS   = "customers"
    PRODUCTS    = "products"
    MIXED       = "mixed"
    UNKNOWN     = "unknown"


ORDERS_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "transaction_id",
    "order_date", "fecha_pedido", "fecha", "created_at", "purchase_date",
    "total_amount", "total_sales", "price_usd", "final_total", "total",
    "importe", "amount", "revenue", "net_sales"
]

ORDER_LINES_SIGNALS = [
    "order_item_id", "order_item", "line_item_id", "item_id", "order_line_id",
    "line_id", "is_primary_item", "primary_item", "item_price", "item_cost",
    "order_item_refund_id", "refund_amount_usd", "order_item_refund"
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

DETECTION_THRESHOLD  = 2
FUZZY_SCORE_THRESHOLD = 75


def _normalize(col: str) -> str:
    return col.lower().strip().replace(" ", "_").replace("-", "_").replace(".", "_")


def _fuzzy_match_score(col_normalized: str, signals: list[str]) -> float:
    best = 0
    for signal in signals:
        score = fuzz.token_sort_ratio(col_normalized, signal)
        if score > best:
            best = score
    return best


def detect_type_with_confidence(columns: list[str]) -> tuple[UploadType, float]:
    """
    Detecta el tipo de datos y devuelve (tipo, confianza 0.0-1.0).

    Proceso:
    1. Normalizar columnas
    2. Calcular score fuzzy contra señales de cada tipo
    3. Clasificar según umbral mínimo de hits
    4. Resolver conflictos: ORDER_LINES tiene prioridad sobre ORDERS
       cuando hay señales específicas de líneas (order_item_id, is_primary_item)
    """
    normalized_cols = [_normalize(c) for c in columns]

    order_hits      = 0
    order_line_hits = 0
    customer_hits   = 0
    product_hits    = 0

    for col in normalized_cols:
        if _fuzzy_match_score(col, ORDERS_SIGNALS)      >= FUZZY_SCORE_THRESHOLD:
            order_hits += 1
        if _fuzzy_match_score(col, ORDER_LINES_SIGNALS) >= FUZZY_SCORE_THRESHOLD:
            order_line_hits += 1
        if _fuzzy_match_score(col, CUSTOMERS_SIGNALS)   >= FUZZY_SCORE_THRESHOLD:
            customer_hits += 1
        if _fuzzy_match_score(col, PRODUCTS_SIGNALS)    >= FUZZY_SCORE_THRESHOLD:
            product_hits += 1

    detected = []
    if order_hits      >= DETECTION_THRESHOLD: detected.append((UploadType.ORDERS,      order_hits))
    if order_line_hits >= DETECTION_THRESHOLD: detected.append((UploadType.ORDER_LINES, order_line_hits))
    if customer_hits   >= DETECTION_THRESHOLD: detected.append((UploadType.CUSTOMERS,   customer_hits))
    if product_hits    >= DETECTION_THRESHOLD: detected.append((UploadType.PRODUCTS,    product_hits))

    if len(detected) == 0:
        return UploadType.UNKNOWN, 0.0

    if len(detected) == 1:
        upload_type, hits = detected[0]
        confidence = min(hits / max(len(columns), 1), 1.0)
        return upload_type, round(confidence, 2)

    # Resolver conflicto ORDERS vs ORDER_LINES:
    # Si hay señales específicas de líneas (order_item_id, is_primary_item),
    # clasificar como ORDER_LINES aunque también haya señales de ORDERS
    has_orders      = any(t == UploadType.ORDERS      for t, _ in detected)
    has_order_lines = any(t == UploadType.ORDER_LINES  for t, _ in detected)

    if has_orders and has_order_lines:
        # Señales que son exclusivas de order_lines
        exclusive_line_signals = ["order_item_id", "order_item", "is_primary_item",
                                  "order_item_refund_id", "order_line_id"]
        has_exclusive = any(
            _fuzzy_match_score(col, exclusive_line_signals) >= 85
            for col in normalized_cols
        )
        if has_exclusive:
            confidence = min(order_line_hits / max(len(columns), 1), 1.0)
            return UploadType.ORDER_LINES, round(confidence, 2)

    # Múltiples tipos sin resolver → MIXED
    total_hits = sum(h for _, h in detected)
    confidence = min(total_hits / max(len(columns), 1), 1.0)
    return UploadType.MIXED, round(confidence, 2)


def detect_upload_type(columns: list[str]) -> UploadType:
    """Compatibilidad con código existente."""
    upload_type, _ = detect_type_with_confidence(columns)
    return upload_type