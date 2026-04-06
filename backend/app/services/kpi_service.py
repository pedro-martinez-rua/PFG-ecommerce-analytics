"""
kpi_service.py — Orquestación del KPI Engine.

Analiza TODOS los datos del tenant sin distinción de import.
El tenant tiene un negocio — todos sus imports son parte del mismo pool.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np


from app.services.kpi_calculator import (
    check_data_coverage,
    calc_total_revenue, calc_order_count, calc_avg_order_value,
    calc_growth_pct, calc_total_discounts, calc_discount_rate,
    calc_gross_margin, calc_gross_margin_pct, calc_net_revenue, calc_total_refunds,
    calc_top_products_revenue, calc_top_products_units,
    calc_revenue_by_category, calc_product_margin,
    calc_unique_customers, calc_new_vs_returning,
    calc_repeat_purchase_rate, calc_avg_ltv,
    calc_return_rate, calc_returned_count, calc_avg_delivery_days,
    calc_delayed_orders_pct, calc_refund_rate,
    calc_revenue_over_time, calc_revenue_by_channel,
    calc_revenue_by_country, calc_orders_by_status, calc_orders_over_time,
)

# RESOLUCIÓN DE PERIODOS
def resolve_period(
    period: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str]
) -> tuple[date, date, str]:
    today = datetime.now().date()

    if date_from and date_to:
        return date.fromisoformat(date_from), date.fromisoformat(date_to), "custom"
    if period == "last_30":
        return today - timedelta(days=30), today, "last_30"
    if period == "last_90":
        return today - timedelta(days=90), today, "last_90"
    if period == "ytd":
        return date(today.year, 1, 1), today, "ytd"
    if period == "last_year":
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31), "last_year"
    if period == "all":
        return date(2000, 1, 1), today, "all"

    return today - timedelta(days=30), today, "last_30"

def resolve_previous_period(
    period_start: date,
    period_end: date,
    period_label: str
) -> tuple[date, date]:
    if period_label == "ytd":
        return (
            date(period_start.year - 1, 1, 1),
            date(period_end.year - 1, period_end.month, period_end.day)
        )
    delta    = period_end - period_start
    prev_end = period_start - timedelta(days=1)
    return prev_end - delta, prev_end

# CARGA DE DATOS
def load_orders(
    db: Session,
    tenant_id: str,
    period_start: date,
    period_end: date,
    import_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    params = {
        "tenant_id": tenant_id,
        "date_from": period_start,
        "date_to": period_end,
    }

    import_filter = _build_import_filter_sql("import_id", import_ids, params)

    result = db.execute(text(f"""
        SELECT
            id::text, external_id, order_date,
            total_amount::float, discount_amount::float,
            net_amount::float, shipping_cost::float,
            refund_amount::float, cogs_amount::float,
            currency, channel, status, payment_method,
            shipping_country, shipping_region,
            delivery_days::float, is_returned,
            COALESCE(customer_reference, customer_id::text) AS customer_id,
            import_id::text
        FROM orders
        WHERE tenant_id = :tenant_id
          AND order_date >= :date_from
          AND order_date <= :date_to
          {import_filter}
    """), params)

    rows = result.fetchall()
    return pd.DataFrame(rows, columns=list(result.keys())) if rows else pd.DataFrame()

def load_order_lines(
    db: Session,
    tenant_id: str,
    period_start: date,
    period_end: date,
    import_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Carga líneas de pedido del periodo.
    Join con orders para filtrar por fecha e import_ids del dashboard.
    """
    params = {
        "tenant_id": tenant_id,
        "date_from": period_start,
        "date_to": period_end,
    }

    import_filter = _build_import_filter_sql("o.import_id", import_ids, params)

    result = db.execute(text(f"""
        SELECT
            ol.id::text,
            ol.order_id::text,
            ol.product_name,
            ol.sku,
            ol.category,
            ol.brand,
            ol.quantity::float,
            ol.unit_price::float,
            COALESCE(ol.unit_cost, p.unit_cost)::float AS unit_cost,
            ol.line_total::float,
            ol.is_primary_item,
            ol.is_refunded,
            o.order_date,
            o.import_id::text
        FROM order_lines ol
        INNER JOIN orders o ON ol.order_id = o.id
        LEFT JOIN products p ON ol.product_id = p.id
        WHERE ol.tenant_id = :tenant_id
          AND o.order_date >= :date_from
          AND o.order_date <= :date_to
          {import_filter}
    """), params)

    rows = result.fetchall()
    return pd.DataFrame(rows, columns=list(result.keys())) if rows else pd.DataFrame()

def load_all_orders(
    db: Session,
    tenant_id: str,
    import_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    params = {"tenant_id": tenant_id}
    import_filter = _build_import_filter_sql("import_id", import_ids, params)

    result = db.execute(text(f"""
        SELECT
            id::text,
            COALESCE(customer_reference, customer_id::text) AS customer_id,
            order_date,
            total_amount::float,
            import_id::text
        FROM orders
        WHERE tenant_id = :tenant_id
          {import_filter}
    """), params)

    rows = result.fetchall()
    return pd.DataFrame(rows, columns=list(result.keys())) if rows else pd.DataFrame()

def get_available_date_range(db: Session, tenant_id: str) -> dict:
    """Rango de fechas disponible en los datos del tenant."""
    result = db.execute(text("""
        SELECT
            MIN(order_date) AS date_from,
            MAX(order_date) AS date_to,
            COUNT(*)        AS total_orders
        FROM orders
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": tenant_id})
    row = result.fetchone()
    if not row or not row[0]:
        return {"has_data": False, "date_from": None, "date_to": None, "total_orders": 0}
    return {
        "has_data":     True,
        "date_from":    row[0].isoformat(),
        "date_to":      row[1].isoformat(),
        "total_orders": row[2]
    }

# CACHÉ
CACHE_TTL_MINUTES = 60
def invalidate_kpi_cache(db: Session, tenant_id: str) -> None:
    """Invalida el caché de KPIs. Llamar tras cada ingesta o borrado."""
    db.execute(
        text("DELETE FROM kpi_snapshots WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    db.commit()


# HELPERS KPI
def _make_kpi(
    value: Optional[float],
    previous: Optional[float] = None,
    availability: str = "real",
    reason: Optional[str] = None
) -> dict:
    growth = None
    if value is not None and previous is not None and previous != 0:
        growth = round(((value - previous) / previous) * 100, 2)
    return {
        "value":        value,
        "vs_previous":  previous,
        "growth_pct":   growth,
        "availability": availability,
        "reason":       reason
    }

def _missing_kpi(reason: str) -> dict:
    return {
        "value": None, "vs_previous": None,
        "growth_pct": None, "availability": "missing", "reason": reason
    }

def _make_serializable(obj):
    """
    Convierte recursivamente tipos numpy a tipos Python nativos.
    FastAPI no puede serializar numpy.bool, numpy.int64, numpy.float64, etc.
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def _clean_import_ids(import_ids: Optional[List[str]]) -> list[str]:
    return [str(x) for x in (import_ids or []) if x]


def _build_import_filter_sql(
    field_name: str,
    import_ids: Optional[List[str]],
    params: dict
) -> str:
    cleaned = _clean_import_ids(import_ids)
    if not cleaned:
        return ""
    params["import_ids"] = cleaned
    return f" AND {field_name} = ANY(CAST(:import_ids AS uuid[])) "

# CÁLCULO PRINCIPAL
def compute_kpis(
    db: Session,
    tenant_id: str,
    period: Optional[str] = "last_30",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    import_ids: Optional[List[str]] = None,
) -> dict:
    """
    Calcula todos los KPIs disponibles para el tenant y periodo.
    Analiza el pool completo de datos del tenant.
    """
    # Periodo
    p_start, p_end, p_label = resolve_period(period, date_from, date_to)
    prev_start, prev_end    = resolve_previous_period(p_start, p_end, p_label)
    delta_days  = (p_end - p_start).days
    granularity = "month" if delta_days > 90 else "day"

    # Datos
    orders_df      = load_orders(db, tenant_id, p_start, p_end, import_ids=import_ids)
    prev_orders_df = load_orders(db, tenant_id, prev_start, prev_end, import_ids=import_ids)
    lines_df       = load_order_lines(db, tenant_id, p_start, p_end, import_ids=import_ids)
    all_orders_df  = load_all_orders(db, tenant_id, import_ids=import_ids)

    # Cobertura
    coverage = check_data_coverage(orders_df, lines_df)

    # ── GRUPO A: Ventas ──
    revenue      = calc_total_revenue(orders_df)
    prev_revenue = calc_total_revenue(prev_orders_df)
    orders       = calc_order_count(orders_df)
    prev_orders  = calc_order_count(prev_orders_df)
    aov          = calc_avg_order_value(orders_df)
    prev_aov     = calc_avg_order_value(prev_orders_df)
    discounts    = calc_total_discounts(orders_df)
    disc_rate    = calc_discount_rate(orders_df)

    # ── GRUPO B: Rentabilidad ──
    gross_margin,     gm_avail  = calc_gross_margin(orders_df, coverage)
    gross_margin_pct, gmp_avail = calc_gross_margin_pct(orders_df, coverage)
    net_revenue,      nr_avail  = calc_net_revenue(orders_df)
    prev_net,         _         = calc_net_revenue(prev_orders_df)
    total_refunds               = calc_total_refunds(orders_df)
    refund_rate                 = calc_refund_rate(orders_df)
    prev_refund_rate            = calc_refund_rate(prev_orders_df)

    # ── GRUPO C: Productos ──
    product_margin_data, pm_avail = calc_product_margin(lines_df)

    # ── GRUPO D: Clientes ──
    unique_cust      = calc_unique_customers(orders_df)
    prev_unique_cust = calc_unique_customers(prev_orders_df)
    new_vs_ret, nvr_avail = calc_new_vs_returning(orders_df, all_orders_df)
    repeat_rate      = calc_repeat_purchase_rate(orders_df)
    avg_ltv          = calc_avg_ltv(orders_df)
    prev_avg_ltv     = calc_avg_ltv(prev_orders_df)

    # ── GRUPO E: Operación ──
    return_rate    = calc_return_rate(orders_df)
    prev_ret_rate  = calc_return_rate(prev_orders_df)
    returned_count = calc_returned_count(orders_df)
    avg_delivery   = calc_avg_delivery_days(orders_df)
    delayed_pct    = calc_delayed_orders_pct(orders_df)

    # ── KPI dict ──
    kpis = {
        # Ventas
        "total_revenue":   _make_kpi(revenue, prev_revenue),
        "order_count":     _make_kpi(float(orders) if orders else None,
                                     float(prev_orders) if prev_orders else None),
        "avg_order_value": _make_kpi(aov, prev_aov),
        "net_revenue":     _make_kpi(net_revenue, prev_net,
                                     availability=nr_avail,
                                     reason="Calculado con datos parciales"
                                            if nr_avail == "estimated" else None),
        "total_discounts": _make_kpi(discounts)
                           if discounts else _missing_kpi("Sin datos de descuentos"),
        "discount_rate":   _make_kpi(disc_rate)
                           if disc_rate else _missing_kpi("Sin datos de descuentos"),

        # Rentabilidad
        "gross_margin": _make_kpi(
            gross_margin, availability=gm_avail,
            reason="Sin datos de coste (COGS)" if gm_avail == "missing" else
                   "COGS parcialmente disponible" if gm_avail == "estimated" else None
        ),
        "gross_margin_pct": _make_kpi(
            gross_margin_pct, availability=gmp_avail,
            reason="Sin datos de coste (COGS)" if gmp_avail == "missing" else
                   "COGS parcialmente disponible" if gmp_avail == "estimated" else None
        ),
        "total_refunds": _make_kpi(total_refunds)
                         if total_refunds else _missing_kpi("Sin datos de reembolsos"),
        "refund_rate":   _make_kpi(refund_rate, prev_refund_rate)
                         if refund_rate is not None else _missing_kpi("Sin datos de reembolsos"),

        # Clientes
        "unique_customers": _make_kpi(
            float(unique_cust) if unique_cust is not None else None,
            float(prev_unique_cust) if prev_unique_cust is not None else None
        ) if coverage["has_customers"] else _missing_kpi("Sin datos de clientes"),

        "new_vs_returning": {
            "value":        new_vs_ret,
            "availability": nvr_avail,
            "reason":       "Calculado sin histórico previo"
                            if nvr_avail == "estimated" else None
        } if new_vs_ret else _missing_kpi("Sin datos de clientes"),

        "repeat_purchase_rate": _make_kpi(repeat_rate)
                                if repeat_rate is not None
                                else _missing_kpi("Sin datos de clientes"),
        "avg_customer_ltv": _make_kpi(avg_ltv, prev_avg_ltv)
                            if avg_ltv else _missing_kpi("Sin datos de clientes"),

        # Operación
        "return_rate": _make_kpi(return_rate, prev_ret_rate)
                       if return_rate is not None
                       else _missing_kpi("Sin datos de devoluciones"),
        "returned_orders": _make_kpi(float(returned_count) if returned_count else None)
                           if returned_count is not None
                           else _missing_kpi("Sin datos de devoluciones"),
        "avg_delivery_days": _make_kpi(avg_delivery)
                             if avg_delivery else _missing_kpi("Sin datos de entrega"),
        "delayed_orders_pct": _make_kpi(delayed_pct)
                              if delayed_pct else _missing_kpi("Sin datos de entrega"),
    }

    # ── Charts ──
    charts = {
        "revenue_over_time":    calc_revenue_over_time(orders_df, granularity),
        "orders_over_time":     calc_orders_over_time(orders_df, granularity),
        "revenue_by_channel":   calc_revenue_by_channel(orders_df),
        "revenue_by_country":   calc_revenue_by_country(orders_df),
        "orders_by_status":     calc_orders_by_status(orders_df),
        "top_products_revenue": calc_top_products_revenue(lines_df),
        "top_products_units":   calc_top_products_units(lines_df),
        "revenue_by_category":  calc_revenue_by_category(lines_df),
        "product_margin":       product_margin_data if pm_avail != "missing" else [],
        "new_vs_returning":     new_vs_ret if new_vs_ret else {"new": 0, "returning": 0},
    }
    return _make_serializable({
        "period":       p_label,
        "date_from":    p_start.isoformat(),
        "date_to":      p_end.isoformat(),
        "import_ids":   _clean_import_ids(import_ids),
        "data_coverage": coverage,
        "kpis":   kpis,
        "charts": charts,
    })