"""
detector.py — Segunda capa del pipeline.

Detección híbrida por nombres de columna y contenido.
Soporta: orders, order_lines, customers, products,
         web_sessions, marketing, refunds, mixed, unknown.
"""
from __future__ import annotations

import re
import pandas as pd
from enum import Enum
from rapidfuzz import fuzz


class UploadType(str, Enum):
    ORDERS      = "orders"
    ORDER_LINES = "order_lines"
    CUSTOMERS   = "customers"
    PRODUCTS    = "products"
    WEB_SESSIONS = "web_sessions"
    MARKETING   = "marketing"
    REFUNDS     = "refunds"
    MIXED       = "mixed"
    UNKNOWN     = "unknown"


# Label legible para mostrar al usuario
UPLOAD_TYPE_LABELS: dict[str, str] = {
    "orders":       "Pedidos",
    "order_lines":  "Líneas de pedido",
    "customers":    "Clientes",
    "products":     "Catálogo de productos",
    "web_sessions": "Sesiones web",
    "marketing":    "Campañas de marketing",
    "refunds":      "Devoluciones y reembolsos",
    "mixed":        "Dataset mixto",
    "unknown":      "Tipo no reconocido",
}


def get_upload_type_label(upload_type: str) -> str:
    return UPLOAD_TYPE_LABELS.get(upload_type, upload_type)


# Señales por tipo

ORDERS_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "invoice_number",
    "transaction_id", "order_date", "fecha_pedido", "fecha", "created_at",
    "purchase_date", "invoice_date", "transaction_date",
    "total_amount", "total_sales", "price_usd", "final_total", "total",
    "importe", "amount", "revenue", "net_sales",
]

ORDER_LINES_SIGNALS = [
    "order_item_id", "order_item", "line_item_id", "item_id", "order_line_id",
    "line_id", "is_primary_item", "primary_item", "item_price", "item_cost",
    "order_item_refund_id", "refund_amount_usd", "order_item_refund",
    "sku", "stock_code", "stockcode", "description", "unit_price", "quantity",
]

CUSTOMERS_SIGNALS = [
    "customer_id", "customerid", "customer_name", "customer_email",
    "client_id", "email", "correo", "nombre_cliente", "full_name", "user_id",
    "phone", "telefono", "fecha_registro", "signup_date",
]

PRODUCTS_SIGNALS = [
    "product_id", "productid", "product_name", "sku", "stock_code",
    "stockcode", "description", "descripcion", "producto", "articulo",
    "unit_price", "unitprice", "unit_cost", "category", "brand", "subcategory",
]

WEB_SESSIONS_SIGNALS = [
    "website_session_id", "session_id", "visit_id", "web_session",
    "pageviews", "page_views", "is_bounce", "bounced_session",
    "landing_page", "first_page_seen", "device_type", "device_category",
    "traffic_source", "sessions_to_order", "new_visitor",
    "utm_source", "utm_campaign", "utm_medium",
    "time_on_site", "pages_per_session", "bounce_rate",
]

MARKETING_SIGNALS = [
    "campaign_name", "campaign_id", "campaña", "ad_group", "ad_set",
    "impressions", "impresiones", "clicks", "clics",
    "ctr", "click_through_rate",
    "cost", "spend", "ad_spend", "coste_publicidad", "budget_spent",
    "roas", "return_on_ad_spend",
    "conversions", "conversiones", "cost_per_conversion", "cpa",
    "cost_per_click", "cpc",
    "reach", "frequency", "keyword", "ad_name",
]

REFUNDS_SIGNALS = [
    "refund_id", "return_id", "refund_date", "return_date",
    "refund_amount", "refund_usd", "reembolso",
    "return_reason", "refund_reason", "devolucion", "motivo_devolucion",
    "refunded_at", "returned_at", "credit_note",
    "order_item_refund_id", "refund_amount_usd", "order_item_id",         
]

# Señales para reglas estructurales 
ORDER_ID_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "invoice_number",
    "transaction_id", "sale_id", "receipt_id",
]
ORDER_DATE_SIGNALS = [
    "order_date", "invoice_date", "created_at", "purchase_date",
    "transaction_date", "date",
]
PRODUCT_LIKE_SIGNALS = [
    "product_name", "description", "sku", "stock_code", "stockcode", "item_name",
]
QUANTITY_SIGNALS  = ["quantity", "qty", "units", "cantidad"]
UNIT_PRICE_SIGNALS = ["unit_price", "unitprice", "price", "item_price"]

# Señales exclusivas que fuerzan web_sessions sin ambigüedad
WEB_EXCLUSIVE_SIGNALS = [
    "website_session_id", "is_bounce", "bounced_session",
    "pages_per_session", "time_on_site", "new_visitor",
    "sessions_to_order", "landing_page", "first_page_seen",
]

# Señales exclusivas que fuerzan marketing sin ambigüedad
MARKETING_EXCLUSIVE_SIGNALS = [
    "impressions", "impresiones", "roas", "return_on_ad_spend",
    "cost_per_click", "cpc", "ad_spend", "ad_group", "ad_set",
    "campaign_id", "campaign_name", "campaña",
]

REFUNDS_EXCLUSIVE_SIGNALS = [
    "refund_id", "return_id", "refund_reason", "return_reason",
    "refunded_at", "returned_at", "credit_note",
    "order_item_refund_id", "refund_amount_usd", "refund_amount",         
]

DETECTION_THRESHOLD   = 2
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


def _has_signal(
    normalized_cols: list[str],
    signals: list[str],
    threshold: float = 80,
) -> bool:
    return any(_fuzzy_match_score(col, signals) >= threshold for col in normalized_cols)


def _count_hits(normalized_cols: list[str], signals: list[str]) -> int:
    return sum(
        1 for c in normalized_cols
        if _fuzzy_match_score(c, signals) >= FUZZY_SCORE_THRESHOLD
    )


def _has_exclusive(normalized_cols: list[str], exclusive: list[str]) -> bool:
    """Devuelve True si alguna columna coincide fuerte con una señal exclusiva."""
    return any(
        _fuzzy_match_score(col, exclusive) >= 85
        for col in normalized_cols
    )


def _infer_order_lines_from_content(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    qty_cols   = []
    money_cols = []
    for col in df.columns:
        series = df[col].dropna().astype(str).head(25)
        if series.empty:
            continue
        num_ratio = series.apply(
            lambda v: bool(re.match(r"^-?\d+([\.,]\d+)?$", v.strip()))
        ).mean()
        if num_ratio >= 0.7:
            col_norm = _normalize(col)
            if _fuzzy_match_score(col_norm, QUANTITY_SIGNALS) >= 75:
                qty_cols.append(col)
            if _fuzzy_match_score(col_norm, UNIT_PRICE_SIGNALS) >= 75:
                money_cols.append(col)
    return bool(qty_cols and money_cols)


def _infer_web_sessions_from_content(df: pd.DataFrame) -> bool:
    """
    Detecta sesiones web por contenido cuando los nombres de columna
    no son suficientemente claros.
    """
    if df is None or df.empty:
        return False
    for col in df.columns:
        col_norm = _normalize(col)
        # Columna con valores típicos de dispositivo
        if _fuzzy_match_score(col_norm, ["device_type", "device", "dispositivo"]) >= 80:
            sample = df[col].dropna().astype(str).str.lower().head(30).tolist()
            devices = {"mobile", "desktop", "tablet", "smartphone", "app"}
            if sum(1 for v in sample if v.strip() in devices) / max(len(sample), 1) > 0.4:
                return True
        # Columna booleana de bounce
        if _fuzzy_match_score(col_norm, ["bounce", "is_bounce", "rebote"]) >= 80:
            return True
    return False


def _infer_marketing_from_content(df: pd.DataFrame) -> bool:
    """
    Detecta datasets de marketing por contenido numérico en columnas
    con nombres propios de métricas de campaña.
    """
    if df is None or df.empty:
        return False
    numeric_marketing = 0
    for col in df.columns:
        col_norm = _normalize(col)
        marketing_score = _fuzzy_match_score(
            col_norm,
            ["impressions", "clicks", "ctr", "spend", "roas", "conversions", "cpc"]
        )
        if marketing_score >= 75:
            series = df[col].dropna().astype(str).head(20)
            num_ratio = series.apply(
                lambda v: bool(re.match(r"^-?\d+([\.,]\d+)?$", v.strip()))
            ).mean()
            if num_ratio >= 0.7:
                numeric_marketing += 1
    return numeric_marketing >= 2

def detect_type_with_confidence(
    columns: list[str],
    df: pd.DataFrame | None = None,
) -> tuple[UploadType, float]:
    normalized_cols = [_normalize(c) for c in columns]

    # Paso 1: señales exclusivas (mayor prioridad)
    if _has_exclusive(normalized_cols, WEB_EXCLUSIVE_SIGNALS):
        web_hits = _count_hits(normalized_cols, WEB_SESSIONS_SIGNALS)
        confidence = min(max(web_hits, 2) / max(len(columns), 1), 1.0)
        return UploadType.WEB_SESSIONS, round(max(confidence, 0.80), 2)

    if _has_exclusive(normalized_cols, MARKETING_EXCLUSIVE_SIGNALS):
        mkt_hits = _count_hits(normalized_cols, MARKETING_SIGNALS)
        confidence = min(max(mkt_hits, 2) / max(len(columns), 1), 1.0)
        return UploadType.MARKETING, round(max(confidence, 0.80), 2)

    if _has_exclusive(normalized_cols, REFUNDS_EXCLUSIVE_SIGNALS):
        ref_hits = _count_hits(normalized_cols, REFUNDS_SIGNALS)
        confidence = min(max(ref_hits, 2) / max(len(columns), 1), 1.0)
        return UploadType.REFUNDS, round(max(confidence, 0.78), 2)

    # Paso 2: conteo de hits por tipo
    order_hits      = _count_hits(normalized_cols, ORDERS_SIGNALS)
    order_line_hits = _count_hits(normalized_cols, ORDER_LINES_SIGNALS)
    customer_hits   = _count_hits(normalized_cols, CUSTOMERS_SIGNALS)
    product_hits    = _count_hits(normalized_cols, PRODUCTS_SIGNALS)
    web_hits        = _count_hits(normalized_cols, WEB_SESSIONS_SIGNALS)
    marketing_hits  = _count_hits(normalized_cols, MARKETING_SIGNALS)
    refund_hits     = _count_hits(normalized_cols, REFUNDS_SIGNALS)

    # Señales estructurales para reglas específicas
    has_order_id   = _has_signal(normalized_cols, ORDER_ID_SIGNALS, 80)
    has_date       = _has_signal(normalized_cols, ORDER_DATE_SIGNALS, 80)
    has_product    = _has_signal(normalized_cols, PRODUCT_LIKE_SIGNALS, 75)
    has_quantity   = _has_signal(normalized_cols, QUANTITY_SIGNALS, 80)
    has_unit_price = _has_signal(normalized_cols, UNIT_PRICE_SIGNALS, 80)

    # Paso 3: regla explícita para transaccionales tipo Online Retail
    if has_order_id and has_date and has_product and has_quantity and has_unit_price:
        return UploadType.ORDER_LINES, 0.88

    # Paso 4: inferencia por contenido para tipos no-transaccionales
    if df is not None:
        if web_hits >= 1 and web_hits > order_hits and _infer_web_sessions_from_content(df):
            confidence = min(max(web_hits, 2) / max(len(columns), 1), 1.0)
            return UploadType.WEB_SESSIONS, round(max(confidence, 0.72), 2)

        if marketing_hits >= 1 and marketing_hits > order_hits and _infer_marketing_from_content(df):
            confidence = min(max(marketing_hits, 2) / max(len(columns), 1), 1.0)
            return UploadType.MARKETING, round(max(confidence, 0.72), 2)

    # Paso 5: votación general
    detected: list[tuple[UploadType, int]] = []

    if order_hits      >= DETECTION_THRESHOLD:
        detected.append((UploadType.ORDERS,       order_hits))
    if order_line_hits >= DETECTION_THRESHOLD:
        detected.append((UploadType.ORDER_LINES,  order_line_hits))
    if customer_hits   >= DETECTION_THRESHOLD:
        detected.append((UploadType.CUSTOMERS,    customer_hits))
    if product_hits    >= DETECTION_THRESHOLD:
        detected.append((UploadType.PRODUCTS,     product_hits))
    if web_hits        >= DETECTION_THRESHOLD:
        detected.append((UploadType.WEB_SESSIONS, web_hits))
    if marketing_hits  >= DETECTION_THRESHOLD:
        detected.append((UploadType.MARKETING,    marketing_hits))
    if refund_hits     >= DETECTION_THRESHOLD:
        detected.append((UploadType.REFUNDS,      refund_hits))

    if len(detected) == 0:
        if df is not None and _infer_order_lines_from_content(df) and has_product:
            return UploadType.ORDER_LINES, 0.62
        return UploadType.UNKNOWN, 0.0

    if len(detected) == 1:
        upload_type, hits = detected[0]
        confidence = min(hits / max(len(columns), 1), 1.0)
        return upload_type, round(confidence, 2)

    # Paso 6: resolución de conflictos
    has_orders      = any(t == UploadType.ORDERS      for t, _ in detected)
    has_order_lines = any(t == UploadType.ORDER_LINES  for t, _ in detected)
    has_products    = any(t == UploadType.PRODUCTS     for t, _ in detected)
    has_web         = any(t == UploadType.WEB_SESSIONS for t, _ in detected)
    has_marketing   = any(t == UploadType.MARKETING    for t, _ in detected)

    # Web sessions comparte utm_source/channel con orders
    if has_web and (has_orders or has_order_lines):
        if has_order_id and (has_date or has_unit_price):
            detected = [(t, h) for t, h in detected if t != UploadType.WEB_SESSIONS]
        else:
            confidence = min(max(web_hits, 2) / max(len(columns), 1), 1.0)
            return UploadType.WEB_SESSIONS, round(max(confidence, 0.72), 2)

    # Marketing comparte campaign/channel con orders
    if has_marketing and (has_orders or has_order_lines):
        if marketing_hits > order_hits and marketing_hits > order_line_hits:
            confidence = min(marketing_hits / max(len(columns), 1), 1.0)
            return UploadType.MARKETING, round(max(confidence, 0.75), 2)
        detected = [(t, h) for t, h in detected if t != UploadType.MARKETING]

    # Resolver conflicto ORDERS vs CUSTOMERS
    # customer_id en una hoja de pedidos no la convierte en clientes
    has_customers = any(t == UploadType.CUSTOMERS for t, _ in detected)
    if has_customers and has_orders and not has_order_lines:
        if has_order_id and has_date:
            detected = [(t, h) for t, h in detected if t != UploadType.CUSTOMERS]

    # Resolver conflicto PRODUCTS vs ORDER_LINES
    if has_products and has_order_lines and not has_orders:
        if not has_order_id and not has_date and not has_quantity:
            confidence = min(product_hits / max(len(columns), 1), 1.0)
            return UploadType.PRODUCTS, round(max(confidence, 0.75), 2)
        if has_order_id and has_product and has_quantity and has_unit_price:
            confidence = min(max(order_line_hits, 3) / max(len(columns), 1), 1.0)
            return UploadType.ORDER_LINES, round(max(confidence, 0.72), 2)

    # Resolver conflicto ORDERS vs ORDER_LINES
    if has_orders and has_order_lines:
        exclusive_line_signals = [
            "order_item_id", "order_item", "is_primary_item",
            "order_item_refund_id", "order_line_id",
        ]
        has_excl = any(
            _fuzzy_match_score(col, exclusive_line_signals) >= 85
            for col in normalized_cols
        )
        if has_excl or (has_order_id and has_product and has_quantity and has_unit_price):
            confidence = min(max(order_line_hits, 3) / max(len(columns), 1), 1.0)
            return UploadType.ORDER_LINES, round(max(confidence, 0.72), 2)
        else:
            # Sin señales exclusivas de líneas — gana orders
            detected = [(t, h) for t, h in detected if t != UploadType.ORDER_LINES]

    # Si tras resolver conflictos queda un solo tipo
    if len(detected) == 1:
        upload_type, hits = detected[0]
        confidence = min(hits / max(len(columns), 1), 1.0)
        return upload_type, round(confidence, 2)

    total_hits = sum(hits for _, hits in detected)
    confidence = min(total_hits / max(len(columns), 1), 1.0)
    return UploadType.MIXED, round(confidence, 2)


def detect_upload_type(
    columns: list[str],
    df: pd.DataFrame | None = None,
) -> UploadType:
    upload_type, _ = detect_type_with_confidence(columns, df)
    return upload_type