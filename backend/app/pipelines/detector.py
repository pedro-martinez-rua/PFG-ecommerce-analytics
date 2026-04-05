"""
detector.py — Segunda capa del pipeline.

Detección híbrida por nombres de columna y contenido.
Optimizada para aceptar datasets transaccionales a nivel de línea como
Online Retail.xlsx sin exigir totales agregados por pedido.
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
    MIXED       = "mixed"
    UNKNOWN     = "unknown"


ORDERS_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "invoice_number",
    "transaction_id", "order_date", "fecha_pedido", "fecha", "created_at",
    "purchase_date", "invoice_date", "transaction_date",
    "total_amount", "total_sales", "price_usd", "final_total", "total",
    "importe", "amount", "revenue", "net_sales"
]

ORDER_LINES_SIGNALS = [
    "order_item_id", "order_item", "line_item_id", "item_id", "order_line_id",
    "line_id", "is_primary_item", "primary_item", "item_price", "item_cost",
    "order_item_refund_id", "refund_amount_usd", "order_item_refund",
    "sku", "stock_code", "stockcode", "description", "unit_price", "quantity"
]

CUSTOMERS_SIGNALS = [
    "customer_id", "customerid", "customer_name", "customer_email",
    "client_id", "email", "correo", "nombre_cliente", "full_name", "user_id"
]

PRODUCTS_SIGNALS = [
    "product_id", "productid", "product_name", "sku", "stock_code",
    "stockcode", "description", "descripcion", "producto", "articulo",
    "unit_price", "unitprice", "unit_cost"
]

ORDER_ID_SIGNALS = [
    "order_id", "order_number", "invoice_no", "invoiceno", "invoice_number",
    "transaction_id", "sale_id", "receipt_id"
]
ORDER_DATE_SIGNALS = [
    "order_date", "invoice_date", "created_at", "purchase_date", "transaction_date", "date"
]
PRODUCT_LIKE_SIGNALS = [
    "product_name", "description", "sku", "stock_code", "stockcode", "item_name"
]
QUANTITY_SIGNALS = ["quantity", "qty", "units", "cantidad"]
UNIT_PRICE_SIGNALS = ["unit_price", "unitprice", "price", "item_price"]

DETECTION_THRESHOLD = 2
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


def _has_signal(normalized_cols: list[str], signals: list[str], threshold: float = 80) -> bool:
    return any(_fuzzy_match_score(col, signals) >= threshold for col in normalized_cols)


def _infer_order_lines_from_content(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    qty_cols = []
    money_cols = []
    for col in df.columns:
        series = df[col].dropna().astype(str).head(25)
        if series.empty:
            continue
        num_ratio = series.apply(lambda v: bool(re.match(r"^-?\d+([\.,]\d+)?$", v.strip()))).mean()
        if num_ratio >= 0.7:
            col_norm = _normalize(col)
            if _fuzzy_match_score(col_norm, QUANTITY_SIGNALS) >= 75:
                qty_cols.append(col)
            if _fuzzy_match_score(col_norm, UNIT_PRICE_SIGNALS) >= 75:
                money_cols.append(col)
    return bool(qty_cols and money_cols)


def detect_type_with_confidence(columns: list[str], df: pd.DataFrame | None = None) -> tuple[UploadType, float]:
    normalized_cols = [_normalize(c) for c in columns]

    order_hits      = sum(1 for c in normalized_cols if _fuzzy_match_score(c, ORDERS_SIGNALS) >= FUZZY_SCORE_THRESHOLD)
    order_line_hits = sum(1 for c in normalized_cols if _fuzzy_match_score(c, ORDER_LINES_SIGNALS) >= FUZZY_SCORE_THRESHOLD)
    customer_hits   = sum(1 for c in normalized_cols if _fuzzy_match_score(c, CUSTOMERS_SIGNALS) >= FUZZY_SCORE_THRESHOLD)
    product_hits    = sum(1 for c in normalized_cols if _fuzzy_match_score(c, PRODUCTS_SIGNALS) >= FUZZY_SCORE_THRESHOLD)

    has_order_id   = _has_signal(normalized_cols, ORDER_ID_SIGNALS, 80)
    has_date       = _has_signal(normalized_cols, ORDER_DATE_SIGNALS, 80)
    has_product    = _has_signal(normalized_cols, PRODUCT_LIKE_SIGNALS, 75)
    has_quantity   = _has_signal(normalized_cols, QUANTITY_SIGNALS, 80)
    has_unit_price = _has_signal(normalized_cols, UNIT_PRICE_SIGNALS, 80)

    # Regla explícita para datasets transaccionales tipo Online Retail
    if has_order_id and has_date and has_product and has_quantity and has_unit_price:
        return UploadType.ORDER_LINES, 0.88

    detected = []
    if order_hits >= DETECTION_THRESHOLD:
        detected.append((UploadType.ORDERS, order_hits))
    if order_line_hits >= DETECTION_THRESHOLD:
        detected.append((UploadType.ORDER_LINES, order_line_hits))
    if customer_hits >= DETECTION_THRESHOLD:
        detected.append((UploadType.CUSTOMERS, customer_hits))
    if product_hits >= DETECTION_THRESHOLD:
        detected.append((UploadType.PRODUCTS, product_hits))

    if len(detected) == 0:
        if df is not None and _infer_order_lines_from_content(df) and has_product:
            return UploadType.ORDER_LINES, 0.62
        return UploadType.UNKNOWN, 0.0

    if len(detected) == 1:
        upload_type, hits = detected[0]
        confidence = min(hits / max(len(columns), 1), 1.0)
        return upload_type, round(confidence, 2)

    has_orders = any(t == UploadType.ORDERS for t, _ in detected)
    has_order_lines = any(t == UploadType.ORDER_LINES for t, _ in detected)

    if has_orders and has_order_lines:
        exclusive_line_signals = [
            "order_item_id", "order_item", "is_primary_item",
            "order_item_refund_id", "order_line_id"
        ]
        has_exclusive = any(
            _fuzzy_match_score(col, exclusive_line_signals) >= 85
            for col in normalized_cols
        )
        if has_exclusive or (has_order_id and has_product and has_quantity and has_unit_price):
            confidence = min(max(order_line_hits, 3) / max(len(columns), 1), 1.0)
            return UploadType.ORDER_LINES, round(max(confidence, 0.72), 2)

    total_hits = sum(h for _, h in detected)
    confidence = min(total_hits / max(len(columns), 1), 1.0)
    return UploadType.MIXED, round(confidence, 2)


def detect_upload_type(columns: list[str], df: pd.DataFrame | None = None) -> UploadType:
    upload_type, _ = detect_type_with_confidence(columns, df)
    return upload_type
