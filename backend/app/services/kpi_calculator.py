"""
kpi_calculator.py — Funciones puras de cálculo de KPIs.

Cada función recibe un DataFrame de orders/lines/customers
ya filtrado por tenant y periodo, y devuelve el valor calculado.

Principio: funciones puras sin side effects.
El kpi_service es el que orquesta y persiste.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
import pandas as pd


# ─────────────────────────────────────────────
# COBERTURA DE DATOS
# ─────────────────────────────────────────────

def check_data_coverage(orders_df: pd.DataFrame, lines_df: pd.DataFrame) -> dict:
    """
    Analiza qué campos tienen datos suficientes para calcular KPIs.
    Un campo se considera disponible si tiene datos en al menos el 20% de los registros.
    """
    def coverage(series: pd.Series) -> float:
        if len(series) == 0:
            return 0.0
        return series.notna().sum() / len(series)

    cogs_cov     = coverage(orders_df.get("cogs_amount", pd.Series(dtype=float)))
    channel_cov  = coverage(orders_df.get("channel", pd.Series(dtype=str)))
    country_cov  = coverage(orders_df.get("shipping_country", pd.Series(dtype=str)))
    returned_cov = coverage(orders_df.get("is_returned", pd.Series(dtype=bool)))
    discount_cov = coverage(orders_df.get("discount_amount", pd.Series(dtype=float)))
    delivery_cov = coverage(orders_df.get("delivery_days", pd.Series(dtype=float)))
    refund_cov   = coverage(orders_df.get("refund_amount", pd.Series(dtype=float)))
    customer_cov = coverage(orders_df.get("customer_id", pd.Series(dtype=str)))

    has_products  = len(lines_df) > 0
    has_categories = has_products and coverage(
        lines_df.get("category", pd.Series(dtype=str))
    ) > 0.2

    return {
        "has_cogs":       cogs_cov > 0.2,
        "has_channels":   channel_cov > 0.2,
        "has_countries":  country_cov > 0.2,
        "has_returns":    returned_cov > 0.2,
        "has_discounts":  discount_cov > 0.2,
        "has_delivery":   delivery_cov > 0.2,
        "has_refunds":    refund_cov > 0.2,
        "has_customers":  customer_cov > 0.2,
        "has_products":   has_products,
        "has_categories": has_categories,
        "order_count":    len(orders_df),
        # scores para adaptive metrics
        "cogs_coverage":     round(cogs_cov, 2),
        "customer_coverage": round(customer_cov, 2),
    }


# ─────────────────────────────────────────────
# GRUPO A — VENTAS
# ─────────────────────────────────────────────

def calc_total_revenue(orders_df: pd.DataFrame) -> Optional[float]:
    if orders_df.empty or "total_amount" not in orders_df.columns:
        return None
    val = orders_df["total_amount"].apply(pd.to_numeric, errors="coerce").sum()
    return round(float(val), 2)


def calc_order_count(orders_df: pd.DataFrame) -> int:
    return len(orders_df)


def calc_avg_order_value(orders_df: pd.DataFrame) -> Optional[float]:
    revenue = calc_total_revenue(orders_df)
    count   = calc_order_count(orders_df)
    if not revenue or not count:
        return None
    return round(revenue / count, 2)


def calc_growth_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def calc_total_discounts(orders_df: pd.DataFrame) -> Optional[float]:
    if "discount_amount" not in orders_df.columns:
        return None
    val = orders_df["discount_amount"].apply(pd.to_numeric, errors="coerce").sum()
    return round(float(val), 2) if val > 0 else None


def calc_discount_rate(orders_df: pd.DataFrame) -> Optional[float]:
    discounts = calc_total_discounts(orders_df)
    revenue   = calc_total_revenue(orders_df)
    if not discounts or not revenue:
        return None
    return round((discounts / revenue) * 100, 2)


# ─────────────────────────────────────────────
# GRUPO B — RENTABILIDAD
# ─────────────────────────────────────────────

def calc_gross_margin(orders_df: pd.DataFrame, coverage: dict) -> tuple[Optional[float], str]:
    """
    Devuelve (valor, availability).
    Adaptativo según cobertura de COGS.
    """
    if not coverage.get("has_cogs"):
        return None, "missing"

    cogs_cov = coverage.get("cogs_coverage", 0)
    revenue  = calc_total_revenue(orders_df)

    if revenue is None:
        return None, "missing"

    cogs_val = orders_df["cogs_amount"].apply(pd.to_numeric, errors="coerce").sum()
    margin   = float(revenue) - float(cogs_val)

    availability = "real" if cogs_cov >= 0.8 else "estimated"
    return round(margin, 2), availability


def calc_gross_margin_pct(orders_df: pd.DataFrame, coverage: dict) -> tuple[Optional[float], str]:
    margin, availability = calc_gross_margin(orders_df, coverage)
    revenue = calc_total_revenue(orders_df)
    if margin is None or not revenue:
        return None, availability
    return round((margin / float(revenue)) * 100, 2), availability


def calc_net_revenue(orders_df: pd.DataFrame) -> tuple[Optional[float], str]:
    """Net revenue = revenue - refunds - discounts. Adaptativo."""
    revenue   = calc_total_revenue(orders_df)
    if revenue is None:
        return None, "missing"

    has_refunds   = "refund_amount" in orders_df.columns
    has_discounts = "discount_amount" in orders_df.columns

    refunds   = orders_df["refund_amount"].apply(pd.to_numeric, errors="coerce").sum() \
                if has_refunds else 0
    discounts = orders_df["discount_amount"].apply(pd.to_numeric, errors="coerce").sum() \
                if has_discounts else 0

    net = float(revenue) - float(refunds) - float(discounts)

    if not has_refunds and not has_discounts:
        return round(net, 2), "estimated"
    return round(net, 2), "real"


def calc_total_refunds(orders_df: pd.DataFrame) -> Optional[float]:
    if "refund_amount" not in orders_df.columns:
        return None
    val = orders_df["refund_amount"].apply(pd.to_numeric, errors="coerce").sum()
    return round(float(val), 2) if val > 0 else None


# ─────────────────────────────────────────────
# GRUPO C — PRODUCTOS
# ─────────────────────────────────────────────

def calc_top_products_revenue(lines_df: pd.DataFrame, n: int = 10) -> list[dict]:
    if lines_df.empty or "product_name" not in lines_df.columns:
        return []
    lines_df = lines_df.copy()
    lines_df["line_total"] = pd.to_numeric(lines_df.get("line_total"), errors="coerce")
    grouped = (
        lines_df.groupby("product_name")["line_total"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    return [{"label": row["product_name"], "value": round(float(row["line_total"]), 2)}
            for _, row in grouped.iterrows()]


def calc_top_products_units(lines_df: pd.DataFrame, n: int = 10) -> list[dict]:
    if lines_df.empty or "product_name" not in lines_df.columns:
        return []
    lines_df = lines_df.copy()
    lines_df["quantity"] = pd.to_numeric(lines_df.get("quantity"), errors="coerce")
    grouped = (
        lines_df.groupby("product_name")["quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    return [{"label": row["product_name"], "value": round(float(row["quantity"]), 0)}
            for _, row in grouped.iterrows()]


def calc_revenue_by_category(lines_df: pd.DataFrame) -> list[dict]:
    if lines_df.empty or "category" not in lines_df.columns:
        return []
    lines_df = lines_df.copy()
    lines_df["line_total"] = pd.to_numeric(lines_df.get("line_total"), errors="coerce")
    grouped = (
        lines_df.dropna(subset=["category"])
        .groupby("category")["line_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return [{"label": row["category"], "value": round(float(row["line_total"]), 2)}
            for _, row in grouped.iterrows()]


def calc_product_margin(lines_df: pd.DataFrame, n: int = 10) -> tuple[list[dict], str]:
    """Margen por producto. Requiere unit_price y unit_cost."""
    if lines_df.empty:
        return [], "missing"

    lines_df = lines_df.copy()
    lines_df["unit_price"] = pd.to_numeric(lines_df.get("unit_price"), errors="coerce")
    lines_df["unit_cost"]  = pd.to_numeric(lines_df.get("unit_cost"),  errors="coerce")

    has_cost = lines_df["unit_cost"].notna().sum() / max(len(lines_df), 1)
    if has_cost < 0.2:
        return [], "missing"

    lines_df["margin_pct"] = (
        (lines_df["unit_price"] - lines_df["unit_cost"]) / lines_df["unit_price"] * 100
    ).round(2)

    grouped = (
        lines_df.dropna(subset=["product_name", "margin_pct"])
        .groupby("product_name")["margin_pct"]
        .mean()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )

    result = [{"label": row["product_name"], "value": round(float(row["margin_pct"]), 2)}
              for _, row in grouped.iterrows()]

    availability = "real" if has_cost >= 0.8 else "estimated"
    return result, availability


# ─────────────────────────────────────────────
# GRUPO D — CLIENTES
# ─────────────────────────────────────────────

def calc_unique_customers(orders_df: pd.DataFrame) -> Optional[int]:
    if "customer_id" not in orders_df.columns:
        return None
    return int(orders_df["customer_id"].dropna().nunique())


def calc_new_vs_returning(
    orders_df: pd.DataFrame,
    all_orders_df: pd.DataFrame   # todos los pedidos históricos del tenant
) -> tuple[Optional[dict], str]:
    """
    Nuevo = cliente que aparece por primera vez en el periodo.
    Recurrente = cliente que ya tenía pedidos antes del periodo.
    Requiere customer_id.
    """
    if "customer_id" not in orders_df.columns:
        return None, "missing"

    period_customers   = set(orders_df["customer_id"].dropna().unique())
    historic_customers = set(all_orders_df["customer_id"].dropna().unique())

    # Clientes que existían antes del periodo actual
    returning = period_customers & (historic_customers - period_customers)
    new       = period_customers - historic_customers

    # Si no hay histórico suficiente, estimamos
    if len(all_orders_df) == len(orders_df):
        # Solo hay datos del periodo actual — no podemos distinguir
        total = len(period_customers)
        return {"new": total, "returning": 0}, "estimated"

    return {
        "new":       len(period_customers - returning),
        "returning": len(returning)
    }, "real"


def calc_repeat_purchase_rate(orders_df: pd.DataFrame) -> Optional[float]:
    if "customer_id" not in orders_df.columns:
        return None
    customer_orders = orders_df.groupby("customer_id").size()
    returning = (customer_orders > 1).sum()
    total     = len(customer_orders)
    if total == 0:
        return None
    return round((returning / total) * 100, 2)


def calc_avg_ltv(orders_df: pd.DataFrame) -> Optional[float]:
    revenue  = calc_total_revenue(orders_df)
    customers = calc_unique_customers(orders_df)
    if not revenue or not customers:
        return None
    return round(revenue / customers, 2)


# ─────────────────────────────────────────────
# GRUPO E — OPERACIÓN
# ─────────────────────────────────────────────

def calc_return_rate(orders_df: pd.DataFrame) -> Optional[float]:
    if "is_returned" not in orders_df.columns:
        return None
    total    = len(orders_df)
    returned = orders_df["is_returned"].apply(
        lambda x: str(x).lower() in ("true", "1", "yes", "returned", "devuelto")
    ).sum()
    if total == 0:
        return None
    return round((returned / total) * 100, 2)


def calc_returned_count(orders_df: pd.DataFrame) -> Optional[int]:
    if "is_returned" not in orders_df.columns:
        return None
    return int(orders_df["is_returned"].apply(
        lambda x: str(x).lower() in ("true", "1", "yes", "returned", "devuelto")
    ).sum())


def calc_avg_delivery_days(orders_df: pd.DataFrame) -> Optional[float]:
    if "delivery_days" not in orders_df.columns:
        return None
    vals = pd.to_numeric(orders_df["delivery_days"], errors="coerce")
    if vals.isna().all():
        return None
    return round(float(vals.mean()), 1)


def calc_delayed_orders_pct(orders_df: pd.DataFrame, threshold_days: int = 7) -> Optional[float]:
    """Pedidos que tardaron más de threshold_days días."""
    if "delivery_days" not in orders_df.columns:
        return None
    vals  = pd.to_numeric(orders_df["delivery_days"], errors="coerce").dropna()
    if len(vals) == 0:
        return None
    delayed = (vals > threshold_days).sum()
    return round((delayed / len(vals)) * 100, 2)


def calc_refund_rate(orders_df: pd.DataFrame) -> Optional[float]:
    revenue = calc_total_revenue(orders_df)
    refunds = calc_total_refunds(orders_df)
    if not revenue or not refunds:
        return None
    return round((refunds / revenue) * 100, 2)


# ─────────────────────────────────────────────
# GRÁFICAS — SERIES TEMPORALES Y DISTRIBUCIONES
# ─────────────────────────────────────────────

def calc_revenue_over_time(orders_df: pd.DataFrame, granularity: str = "day") -> list[dict]:
    """
    Serie temporal de revenue. Granularidad: day | month.
    Periodos cortos (≤90 días) → por día.
    Periodos largos → por mes.
    """
    if orders_df.empty or "total_amount" not in orders_df.columns:
        return []

    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["order_date"]   = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date", "total_amount"])

    if granularity == "month":
        df["period"] = df["order_date"].dt.to_period("M").astype(str)
    else:
        df["period"] = df["order_date"].dt.date.astype(str)

    grouped = df.groupby("period")["total_amount"].sum().reset_index()
    grouped = grouped.sort_values("period")

    return [{"label": row["period"], "value": round(float(row["total_amount"]), 2)}
            for _, row in grouped.iterrows()]


def calc_revenue_by_channel(orders_df: pd.DataFrame) -> list[dict]:
    if orders_df.empty or "channel" not in orders_df.columns:
        return []
    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    grouped = (
        df.dropna(subset=["channel"])
        .groupby("channel")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return [{"label": row["channel"], "value": round(float(row["total_amount"]), 2)}
            for _, row in grouped.iterrows()]


def calc_revenue_by_country(orders_df: pd.DataFrame, n: int = 10) -> list[dict]:
    if orders_df.empty or "shipping_country" not in orders_df.columns:
        return []
    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    grouped = (
        df.dropna(subset=["shipping_country"])
        .groupby("shipping_country")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    return [{"label": row["shipping_country"], "value": round(float(row["total_amount"]), 2)}
            for _, row in grouped.iterrows()]


def calc_orders_by_status(orders_df: pd.DataFrame) -> list[dict]:
    if orders_df.empty or "status" not in orders_df.columns:
        return []
    grouped = (
        orders_df.dropna(subset=["status"])
        .groupby("status")
        .size()
        .sort_values(ascending=False)
        .reset_index(name="count")
    )
    return [{"label": row["status"], "value": int(row["count"])}
            for _, row in grouped.iterrows()]


def calc_orders_over_time(orders_df: pd.DataFrame, granularity: str = "day") -> list[dict]:
    if orders_df.empty:
        return []
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])

    if granularity == "month":
        df["period"] = df["order_date"].dt.to_period("M").astype(str)
    else:
        df["period"] = df["order_date"].dt.date.astype(str)

    grouped = df.groupby("period").size().reset_index(name="count")
    grouped = grouped.sort_values("period")
    return [{"label": row["period"], "value": int(row["count"])}
            for _, row in grouped.iterrows()]