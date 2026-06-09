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

    if orders_df.empty:
        return None, "missing"

    # 1) Prioridad: net_amount si existe y tiene cobertura razonable
    if "net_amount" in orders_df.columns:
        vals = pd.to_numeric(orders_df["net_amount"], errors="coerce")
        coverage = vals.notna().sum() / max(len(orders_df), 1)

        if coverage >= 0.5:
            return round(float(vals.dropna().sum()), 2), "real"

    # 2) Fallback conservador: total_amount - refunds
    revenue = calc_total_revenue(orders_df)
    if revenue is None:
        return None, "missing"

    refunds = 0.0
    if "refund_amount" in orders_df.columns:
        refunds = float(pd.to_numeric(orders_df["refund_amount"], errors="coerce").sum())

    net = float(revenue) - refunds

    # 3) Si no hubo net_amount, esto es una aproximación
    return round(net, 2), "estimated"

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
# GRUPO F — COMPARATIVA ANUAL
# ─────────────────────────────────────────────

def calc_revenue_by_year(orders_df: pd.DataFrame) -> list[dict]:
    """
    Ingresos totales agrupados por año.
    Devuelve [{year, revenue, order_count}] ordenado ASC.
    """
    if orders_df.empty or "total_amount" not in orders_df.columns:
        return []
    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["order_date"]   = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])
    df["year"] = df["order_date"].dt.year

    grouped = (
        df.groupby("year")
        .agg(revenue=("total_amount", "sum"), order_count=("total_amount", "count"))
        .reset_index()
        .sort_values("year")
    )
    return [
        {
            "year":        int(row["year"]),
            "revenue":     round(float(row["revenue"]), 2),
            "order_count": int(row["order_count"]),
        }
        for _, row in grouped.iterrows()
    ]


def calc_revenue_multi_year(
    orders_df: pd.DataFrame,
    granularity: str = "month",
) -> list[dict]:
    """
    Revenue por periodo (mes o día) desglosado por año.
    Útil para gráfico multilinea donde cada línea es un año.
    Devuelve [{year, period, revenue, order_count}].
    """
    if orders_df.empty or "total_amount" not in orders_df.columns:
        return []
    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["order_date"]   = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date", "total_amount"])
    df["year"] = df["order_date"].dt.year

    if granularity == "month":
        df["period"] = df["order_date"].dt.month
        df["period_label"] = df["order_date"].dt.strftime("%b")  # Jan, Feb...
    else:
        df["period"] = df["order_date"].dt.dayofyear
        df["period_label"] = df["order_date"].dt.strftime("%m-%d")

    grouped = (
        df.groupby(["year", "period", "period_label"])
        .agg(revenue=("total_amount", "sum"), order_count=("total_amount", "count"))
        .reset_index()
        .sort_values(["year", "period"])
    )
    return [
        {
            "year":         int(row["year"]),
            "period":       int(row["period"]),
            "period_label": row["period_label"],
            "revenue":      round(float(row["revenue"]), 2),
            "order_count":  int(row["order_count"]),
        }
        for _, row in grouped.iterrows()
    ]


# ─────────────────────────────────────────────
# GRUPO G — CANALES POR TIEMPO
# ─────────────────────────────────────────────

def calc_orders_by_channel_over_time(
    orders_df: pd.DataFrame,
    granularity: str = "month",
    top_n: int = 5,
) -> list[dict]:
    """
    Revenue y pedidos por canal a lo largo del tiempo.
    Devuelve solo los top_n canales por revenue total para no saturar el gráfico.
    Formato: [{period, channel, revenue, order_count}].
    """
    if orders_df.empty or "channel" not in orders_df.columns:
        return []
    df = orders_df.copy()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df["order_date"]   = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date", "channel"])

    if granularity == "month":
        df["period"] = df["order_date"].dt.to_period("M").astype(str)
    else:
        df["period"] = df["order_date"].dt.date.astype(str)

    # Identificar top canales por revenue global
    top_channels = (
        df.groupby("channel")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index.tolist()
    )
    df = df[df["channel"].isin(top_channels)]

    grouped = (
        df.groupby(["period", "channel"])
        .agg(revenue=("total_amount", "sum"), order_count=("total_amount", "count"))
        .reset_index()
        .sort_values(["period", "channel"])
    )
    return [
        {
            "period":      row["period"],
            "channel":     row["channel"],
            "revenue":     round(float(row["revenue"]), 2),
            "order_count": int(row["order_count"]),
        }
        for _, row in grouped.iterrows()
    ]


# ─────────────────────────────────────────────
# GRUPO H — SUBCATEGORÍA
# ─────────────────────────────────────────────

def calc_revenue_by_subcategory(lines_df: pd.DataFrame) -> list[dict]:
    """Revenue por subcategoría de producto."""
    if lines_df.empty or "subcategory" not in lines_df.columns:
        return []
    df = lines_df.copy()
    df["line_total"] = pd.to_numeric(df.get("line_total"), errors="coerce")
    grouped = (
        df.dropna(subset=["subcategory"])
        .groupby("subcategory")["line_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return [
        {"label": row["subcategory"], "value": round(float(row["line_total"]), 2)}
        for _, row in grouped.iterrows()
    ]


# ─────────────────────────────────────────────
# GRUPO I — MÉTRICAS WEB / MARKETING
# ─────────────────────────────────────────────

def calc_session_metrics(orders_df: pd.DataFrame) -> dict:
    """
    Métricas de sesiones web extraídas de los datos de pedidos.
    Solo disponibles si el dataset contiene session_id, utm_source o device_type.
    """
    result = {
        "has_session_data":    False,
        "session_count":       None,
        "unique_sessions":     None,
        "conversion_rate":     None,
        "sessions_by_device":  [],
        "sessions_by_source":  [],
        "sessions_by_campaign": [],
    }

    if orders_df.empty:
        return result

    # Detectar si hay datos de sesión
    has_session  = "session_id"  in orders_df.columns and \
                   orders_df["session_id"].notna().sum() > 0
    has_source   = "utm_source"  in orders_df.columns and \
                   orders_df["utm_source"].notna().sum() > 0
    has_device   = "device_type" in orders_df.columns and \
                   orders_df["device_type"].notna().sum() > 0
    has_campaign = "utm_campaign" in orders_df.columns and \
                   orders_df["utm_campaign"].notna().sum() > 0

    if not any([has_session, has_source, has_device, has_campaign]):
        return result

    result["has_session_data"] = True

    # Sesiones únicas
    if has_session:
        unique = int(orders_df["session_id"].dropna().nunique())
        total  = int(orders_df["session_id"].dropna().count())
        result["unique_sessions"] = unique
        result["session_count"]   = total
        # Conversion rate: pedidos con session_id / sesiones únicas
        orders_with_session = int(orders_df["session_id"].notna().sum())
        if unique > 0:
            result["conversion_rate"] = round((orders_with_session / unique) * 100, 2)

    # Distribución por dispositivo
    if has_device:
        device_counts = (
            orders_df.dropna(subset=["device_type"])
            .groupby("device_type")
            .size()
            .sort_values(ascending=False)
            .reset_index(name="count")
        )
        result["sessions_by_device"] = [
            {"label": row["device_type"], "value": int(row["count"])}
            for _, row in device_counts.iterrows()
        ]

    # Distribución por fuente UTM
    if has_source:
        source_counts = (
            orders_df.dropna(subset=["utm_source"])
            .groupby("utm_source")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="count")
        )
        result["sessions_by_source"] = [
            {"label": row["utm_source"], "value": int(row["count"])}
            for _, row in source_counts.iterrows()
        ]

    # Distribución por campaña
    if has_campaign:
        campaign_counts = (
            orders_df.dropna(subset=["utm_campaign"])
            .groupby("utm_campaign")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="count")
        )
        result["sessions_by_campaign"] = [
            {"label": row["utm_campaign"], "value": int(row["count"])}
            for _, row in campaign_counts.iterrows()
        ]

    return result

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