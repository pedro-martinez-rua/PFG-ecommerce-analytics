"""
test_kpi_calculator.py — Validacion del motor de calculo de KPIs.

Corresponde al Objetivo 2 del plan de validacion:
"Benchmark comparison: calcular KPIs manualmente y contrastar con el sistema."

Todos los valores esperados estan calculados a mano y son verificables
sin herramientas externas.
"""
import pytest
import pandas as pd
from app.services.kpi_calculator import (
    calc_total_revenue, calc_order_count, calc_avg_order_value,
    calc_total_discounts, calc_discount_rate, calc_growth_pct,
    calc_gross_margin, calc_gross_margin_pct, calc_net_revenue, calc_total_refunds,
    calc_refund_rate, calc_unique_customers,
    calc_return_rate, calc_returned_count, calc_avg_delivery_days,
    calc_delayed_orders_pct, calc_top_products_revenue, calc_revenue_by_category,
    calc_product_margin, check_data_coverage,
)


# fixtures
@pytest.fixture
def orders_basic():
    # 5 pedidos con valores conocidos — Revenue total = 1500
    return pd.DataFrame({
        "total_amount":    [100.0, 200.0, 300.0, 400.0, 500.0],
        "net_amount":      [90.0,  180.0, 220.0, 400.0, 500.0],
        "discount_amount": [10.0,  20.0,  30.0,  0.0,   0.0],
        "refund_amount":   [0.0,   0.0,   50.0,  0.0,   0.0],
        "cogs_amount":     [60.0,  120.0, 180.0, 240.0, 300.0],
        "customer_id":     ["c1",  "c2",  "c1",  "c3",  "c2"],
        "is_returned":     ["false","false","true","false","false"],
        "delivery_days":   [3.0,   5.0,   8.0,   2.0,   10.0],
        "channel":         ["web", "web",  "app", "web", "app"],
        "shipping_country":["ES",  "ES",   "FR",  "ES",  "DE"],
        "status":          ["completed"]*5,
    })


@pytest.fixture
def orders_empty():
    return pd.DataFrame()


@pytest.fixture
def lines_basic():
    return pd.DataFrame({
        "product_name": ["Producto A", "Producto B", "Producto A"],
        "category":     ["Ropa",       "Electronica","Ropa"],
        "quantity":     [2.0,          1.0,           3.0],
        "unit_price":   [50.0,         200.0,         50.0],
        "unit_cost":    [30.0,         120.0,         30.0],
        "line_total":   [100.0,        200.0,         150.0],
    })


# calc_total_revenue
class TestVentas:
    def test_total_revenue(self, orders_basic):
        # 100+200+300+400+500 = 1500
        assert calc_total_revenue(orders_basic) == 1500.0

    def test_total_revenue_empty(self, orders_empty):
        assert calc_total_revenue(orders_empty) is None

    def test_total_revenue_sin_columna(self):
        df = pd.DataFrame({"status": ["completed"]})
        assert calc_total_revenue(df) is None

    def test_order_count(self, orders_basic):
        assert calc_order_count(orders_basic) == 5

    def test_order_count_empty(self, orders_empty):
        assert calc_order_count(orders_empty) == 0

    def test_avg_order_value(self, orders_basic):
        # 1500 / 5 = 300
        assert calc_avg_order_value(orders_basic) == 300.0

    def test_avg_order_value_empty(self, orders_empty):
        assert calc_avg_order_value(orders_empty) is None

    def test_total_discounts(self, orders_basic):
        # 10+20+30 = 60
        assert calc_total_discounts(orders_basic) == 60.0

    def test_total_discounts_sin_datos(self):
        df = pd.DataFrame({"total_amount": [100.0]})
        assert calc_total_discounts(df) is None

    def test_discount_rate(self, orders_basic):
        # 60/1500 * 100 = 4.0%
        assert calc_discount_rate(orders_basic) == 4.0

    def test_growth_pct_positivo(self):
        assert calc_growth_pct(1200.0, 1000.0) == 20.0

    def test_growth_pct_negativo(self):
        assert calc_growth_pct(800.0, 1000.0) == -20.0

    def test_growth_pct_division_por_cero(self):
        assert calc_growth_pct(1000.0, 0.0) is None

    def test_growth_pct_ninguno(self):
        assert calc_growth_pct(None, 1000.0) is None


# calc_gross_margin, calc_net_revenue, calc_total_refunds
class TestRentabilidad:
    def test_gross_margin_real(self, orders_basic):
        coverage = {"has_cogs": True, "cogs_coverage": 1.0}
        # Revenue=1500, COGS=900 -> margin=600
        margin, avail = calc_gross_margin(orders_basic, coverage)
        assert margin == 600.0
        assert avail == "real"

    def test_gross_margin_estimado_baja_cobertura(self, orders_basic):
        coverage = {"has_cogs": True, "cogs_coverage": 0.5}
        margin, avail = calc_gross_margin(orders_basic, coverage)
        assert margin == 600.0
        assert avail == "estimated"

    def test_gross_margin_sin_cogs(self, orders_basic):
        coverage = {"has_cogs": False, "cogs_coverage": 0.0}
        margin, avail = calc_gross_margin(orders_basic, coverage)
        assert margin is None
        assert avail == "missing"

    def test_gross_margin_pct(self, orders_basic):
        coverage = {"has_cogs": True, "cogs_coverage": 1.0}
        # 600/1500 * 100 = 40.0%
        pct, avail = calc_gross_margin_pct(orders_basic, coverage)
        assert pct == 40.0
        assert avail == "real"

    def test_net_revenue_usa_net_amount_si_disponible(self, orders_basic):
        # net_amount = 90+180+220+400+500 = 1390, cobertura 100% -> usa net_amount
        net, avail = calc_net_revenue(orders_basic)
        assert net == 1390.0
        assert avail == "real"

    def test_net_revenue_fallback_sin_net_amount(self):
        # Sin net_amount -> fallback: revenue - refunds
        df = pd.DataFrame({
            "total_amount":  [1000.0],
            "refund_amount": [100.0],
        })
        net, avail = calc_net_revenue(df)
        assert net == 900.0
        assert avail == "estimated"

    def test_net_revenue_empty(self, orders_empty):
        net, avail = calc_net_revenue(orders_empty)
        assert net is None
        assert avail == "missing"

    def test_total_refunds(self, orders_basic):
        assert calc_total_refunds(orders_basic) == 50.0

    def test_total_refunds_sin_reembolsos(self):
        df = pd.DataFrame({"total_amount": [100.0], "refund_amount": [0.0]})
        assert calc_total_refunds(df) is None

    def test_refund_rate(self, orders_basic):
        # 50/1500 * 100 = 3.33%
        assert calc_refund_rate(orders_basic) == 3.33


# calc_unique_customers
class TestClientes:
    def test_unique_customers(self, orders_basic):
        # c1, c2, c3 -> 3 clientes unicos
        assert calc_unique_customers(orders_basic) == 3

    def test_unique_customers_sin_columna(self, orders_empty):
        assert calc_unique_customers(orders_empty) is None

    def test_unique_customers_con_nulos(self):
        df = pd.DataFrame({"customer_id": ["c1", None, "c1", "c2"]})
        assert calc_unique_customers(df) == 2

    def test_repeat_purchase_rate_inline(self, orders_basic):
        # c1: 2 pedidos, c2: 2 pedidos, c3: 1 pedido -> 2/3 = 66.67%
        customer_orders = orders_basic.groupby("customer_id").size()
        returning = (customer_orders > 1).sum()
        total = len(customer_orders)
        rate = round((returning / total) * 100, 2)
        assert rate == 66.67


# calc_return_rate, calc_avg_delivery_days, calc_delayed_orders_pct
class TestOperacion:
    def test_return_rate(self, orders_basic):
        # 1 de 5 devueltos -> 20%
        assert calc_return_rate(orders_basic) == 20.0

    def test_return_rate_sin_columna(self, orders_empty):
        assert calc_return_rate(orders_empty) is None

    def test_returned_count(self, orders_basic):
        assert calc_returned_count(orders_basic) == 1

    def test_return_rate_varios_formatos(self):
        df = pd.DataFrame({"is_returned": ["true", "1", "yes", "false", "no"]})
        assert calc_return_rate(df) == 60.0

    def test_avg_delivery_days(self, orders_basic):
        # (3+5+8+2+10)/5 = 5.6
        assert calc_avg_delivery_days(orders_basic) == 5.6

    def test_avg_delivery_days_todos_nulos(self):
        df = pd.DataFrame({"delivery_days": [None, None]})
        assert calc_avg_delivery_days(df) is None

    def test_delayed_orders_pct(self, orders_basic):
        # >7 dias: pedidos con 8 y 10 -> 2/5 = 40%
        assert calc_delayed_orders_pct(orders_basic, threshold_days=7) == 40.0

    def test_delayed_orders_umbral_diferente(self, orders_basic):
        # >3 dias: 5, 8, 10 -> 3/5 = 60%
        assert calc_delayed_orders_pct(orders_basic, threshold_days=3) == 60.0


# check_data_coverage
class TestCobertura:
    def test_cobertura_completa(self, orders_basic, lines_basic):
        cov = check_data_coverage(orders_basic, lines_basic)
        assert cov["has_cogs"] == True
        assert cov["has_customers"] == True
        assert cov["has_returns"] == True
        assert cov["has_products"] == True
        assert cov["has_channels"] == True
        assert cov["order_count"] == 5

    def test_cobertura_sin_datos(self, orders_empty):
        cov = check_data_coverage(orders_empty, pd.DataFrame())
        assert cov["has_cogs"] == False
        assert cov["has_customers"] == False
        assert cov["order_count"] == 0
        assert cov["cogs_coverage"] == 0.0

    def test_cobertura_umbral_20_pct(self):
        # Un campo con <20% de datos no se considera disponible
        df = pd.DataFrame({
            "total_amount": [100.0] * 10,
            "cogs_amount":  [60.0] + [None] * 9,  # 10% cobertura -> has_cogs=False
        })
        cov = check_data_coverage(df, pd.DataFrame())
        assert cov["has_cogs"] == False


# calc_top_products_revenue, calc_revenue_by_category, calc_product_margin
class TestProductos:
    def test_top_products_revenue_orden(self, lines_basic):
        result = calc_top_products_revenue(lines_basic)
        # Producto A: 100+150=250, Producto B: 200 -> A primero
        assert result[0]["label"] == "Producto A"
        assert result[0]["value"] == 250.0
        assert result[1]["label"] == "Producto B"
        assert result[1]["value"] == 200.0

    def test_revenue_by_category(self, lines_basic):
        result = calc_revenue_by_category(lines_basic)
        labels = [r["label"] for r in result]
        assert "Ropa" in labels
        assert "Electronica" in labels
        ropa = next(r for r in result if r["label"] == "Ropa")
        assert ropa["value"] == 250.0

    def test_product_margin(self, lines_basic):
        result, avail = calc_product_margin(lines_basic)
        assert avail in ("real", "estimated")
        assert len(result) > 0
        prod_b = next((r for r in result if r["label"] == "Producto B"), None)
        assert prod_b is not None
        # Producto B: (200-120)/200 * 100 = 40%
        assert prod_b["value"] == pytest.approx(40.0, abs=0.1)

    def test_top_products_sin_datos(self, orders_empty):
        assert calc_top_products_revenue(orders_empty) == []