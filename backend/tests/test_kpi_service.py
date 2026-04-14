"""
test_kpi_service.py — Aislamiento de datos por usuario en el KPI engine.

Prueba que get_user_import_ids filtra correctamente y que las funciones
de calculo de clientes del kpi_service producen resultados correctos.
Sin HTTP — prueba el servicio directamente con mocks y DataFrames en memoria.
"""
import pytest
import uuid
from unittest.mock import MagicMock
import pandas as pd
from datetime import date

from app.services.kpi_service import (
    get_user_import_ids,
    _calc_new_vs_returning_comparable,
    _calc_repeat_purchase_rate_historical,
    _calc_avg_customer_ltv_until_date,
    _with_parsed_order_date,
    resolve_period,
    resolve_previous_period,
    _resolve_adaptive_previous_period,
)


# get_user_import_ids
class TestGetUserImportIds:
    def test_devuelve_imports_del_usuario(self):
        import_a = str(uuid.uuid4())
        db_mock = MagicMock()
        db_mock.execute.return_value.fetchall.return_value = [(import_a,)]
        result = get_user_import_ids(db_mock, str(uuid.uuid4()), str(uuid.uuid4()))
        assert import_a in result

    def test_devuelve_lista_vacia_sin_imports(self):
        db_mock = MagicMock()
        db_mock.execute.return_value.fetchall.return_value = []
        result = get_user_import_ids(db_mock, str(uuid.uuid4()), str(uuid.uuid4()))
        assert result == []

    def test_devuelve_multiples_imports(self):
        ids = [str(uuid.uuid4()) for _ in range(3)]
        db_mock = MagicMock()
        db_mock.execute.return_value.fetchall.return_value = [(i,) for i in ids]
        result = get_user_import_ids(db_mock, str(uuid.uuid4()), str(uuid.uuid4()))
        assert len(result) == 3
        for i in ids:
            assert i in result


# _calc_new_vs_returning_comparable
class TestNewVsReturning:
    def test_clientes_nuevos_y_recurrentes(self):
        current = pd.DataFrame({"customer_id": ["c1", "c2", "c3"]})
        prev    = pd.DataFrame({"customer_id": ["c1", "c4"]})
        result, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "real"
        assert result["returning"] == 1
        assert result["new"] == 2

    def test_todos_nuevos(self):
        current = pd.DataFrame({"customer_id": ["c1", "c2"]})
        prev    = pd.DataFrame({"customer_id": ["c99"]})
        result, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "real"
        assert result["returning"] == 0
        assert result["new"] == 2

    def test_todos_recurrentes(self):
        current = pd.DataFrame({"customer_id": ["c1", "c2"]})
        prev    = pd.DataFrame({"customer_id": ["c1", "c2", "c3"]})
        result, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "real"
        assert result["returning"] == 2
        assert result["new"] == 0

    def test_sin_periodo_previo_missing(self):
        current = pd.DataFrame({"customer_id": ["c1"]})
        prev    = pd.DataFrame()
        _, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "missing"

    def test_sin_customer_id_missing(self):
        current = pd.DataFrame({"total_amount": [100]})
        prev    = pd.DataFrame({"customer_id": ["c1"]})
        _, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "missing"

    def test_prev_customers_vacios_missing(self):
        current = pd.DataFrame({"customer_id": ["c1"]})
        prev    = pd.DataFrame({"customer_id": pd.Series([], dtype=str)})
        _, avail = _calc_new_vs_returning_comparable(current, prev)
        assert avail == "missing"


# _calc_repeat_purchase_rate_historical
class TestRepeatPurchaseRate:
    def test_tasa_correcta(self):
        # 3 clientes actuales, 2 ya habian comprado antes
        current = pd.DataFrame({"customer_id": ["c1", "c2", "c3"]})
        prior   = pd.DataFrame({"customer_id": ["c1", "c2", "c99"]})
        rate, avail = _calc_repeat_purchase_rate_historical(current, prior)
        assert avail == "real"
        assert rate == pytest.approx(66.67, abs=0.01)

    def test_tasa_cero(self):
        current = pd.DataFrame({"customer_id": ["c1", "c2"]})
        prior   = pd.DataFrame({"customer_id": ["c99", "c100"]})
        rate, avail = _calc_repeat_purchase_rate_historical(current, prior)
        assert avail == "real"
        assert rate == 0.0

    def test_tasa_cien_pct(self):
        current = pd.DataFrame({"customer_id": ["c1", "c2"]})
        prior   = pd.DataFrame({"customer_id": ["c1", "c2", "c3"]})
        rate, avail = _calc_repeat_purchase_rate_historical(current, prior)
        assert avail == "real"
        assert rate == 100.0

    def test_sin_historico_missing(self):
        current = pd.DataFrame({"customer_id": ["c1"]})
        prior   = pd.DataFrame()
        _, avail = _calc_repeat_purchase_rate_historical(current, prior)
        assert avail == "missing"

    def test_current_vacio_missing(self):
        current = pd.DataFrame()
        prior   = pd.DataFrame({"customer_id": ["c1"]})
        _, avail = _calc_repeat_purchase_rate_historical(current, prior)
        assert avail == "missing"


# _calc_avg_customer_ltv_until_date
class TestAvgLTV:
    def test_ltv_calculado_correctamente(self):
        # Revenue=1500, 3 clientes unicos -> LTV=500
        df = pd.DataFrame({
            "customer_id":  ["c1",   "c2",   "c3"],
            "total_amount": [500.0,  600.0,  400.0],
            "order_date":   ["2024-01-01", "2024-01-02", "2024-01-03"],
        })
        df = _with_parsed_order_date(df)
        result = _calc_avg_customer_ltv_until_date(df, date(2024, 12, 31))
        assert result == pytest.approx(500.0, abs=0.01)

    def test_ltv_con_cutoff_excluye_pedidos_posteriores(self):
        df = pd.DataFrame({
            "customer_id":  ["c1",   "c2"],
            "total_amount": [300.0,  700.0],
            "order_date":   ["2024-01-01", "2024-06-01"],
        })
        df = _with_parsed_order_date(df)
        result = _calc_avg_customer_ltv_until_date(df, date(2024, 3, 31))
        assert result == 300.0

    def test_ltv_cliente_con_multiples_pedidos(self):
        # c1 tiene 2 pedidos: 200+300=500 -> LTV=500 (1 cliente)
        df = pd.DataFrame({
            "customer_id":  ["c1",   "c1"],
            "total_amount": [200.0,  300.0],
            "order_date":   ["2024-01-01", "2024-02-01"],
        })
        df = _with_parsed_order_date(df)
        result = _calc_avg_customer_ltv_until_date(df, date(2024, 12, 31))
        assert result == 500.0

    def test_dataframe_vacio_devuelve_none(self):
        assert _calc_avg_customer_ltv_until_date(pd.DataFrame(), date(2024, 1, 1)) is None

    def test_sin_customer_id_devuelve_none(self):
        df = pd.DataFrame({
            "total_amount": [100.0],
            "order_date":   ["2024-01-01"],
        })
        df = _with_parsed_order_date(df)
        result = _calc_avg_customer_ltv_until_date(df, date(2024, 12, 31))
        assert result is None


# resolve_period
class TestResolvePeriod:
    def test_last_30(self):
        start, end, label = resolve_period("last_30", None, None)
        assert label == "last_30"
        assert (end - start).days == 30

    def test_last_90(self):
        start, end, label = resolve_period("last_90", None, None)
        assert label == "last_90"
        assert (end - start).days == 90

    def test_custom_dates(self):
        start, end, label = resolve_period("custom", "2024-01-01", "2024-12-31")
        assert label == "custom"
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_ytd_empieza_en_enero(self):
        from datetime import datetime
        start, end, label = resolve_period("ytd", None, None)
        assert label == "ytd"
        assert start.month == 1
        assert start.day == 1
        assert start.year == datetime.now().year

    def test_last_year(self):
        from datetime import datetime
        start, end, label = resolve_period("last_year", None, None)
        assert label == "last_year"
        assert start.year == datetime.now().year - 1
        assert end.year == datetime.now().year - 1

    def test_default_es_last_30(self):
        start, end, label = resolve_period(None, None, None)
        assert label == "last_30"

    def test_all(self):
        start, end, label = resolve_period("all", None, None)
        assert label == "all"
        assert start.year == 2000


# resolve_previous_period
class TestResolvePreviousPeriod:
    def test_mismo_numero_de_dias(self):
        p_start = date(2024, 2, 1)
        p_end   = date(2024, 2, 29)
        prev_s, prev_e = resolve_previous_period(p_start, p_end, "custom")
        assert (prev_e - prev_s).days == (p_end - p_start).days
        assert prev_e == date(2024, 1, 31)

    def test_periodo_previo_no_solapado(self):
        p_start = date(2024, 4, 1)
        p_end   = date(2024, 4, 30)
        prev_s, prev_e = resolve_previous_period(p_start, p_end, "custom")
        assert prev_e == date(2024, 3, 31)

    def test_ytd_apunta_a_ano_anterior(self):
        p_start = date(2024, 1, 1)
        p_end   = date(2024, 6, 30)
        prev_s, prev_e = resolve_previous_period(p_start, p_end, "ytd")
        assert prev_s.year == 2023
        assert prev_e.year == 2023
        assert prev_s.month == 1
        assert prev_s.day == 1


# _resolve_adaptive_previous_period
class TestAdaptivePreviousPeriod:
    def test_periodo_completo(self):
        orders_df = pd.DataFrame({
            "order_date": ["2024-01-01", "2024-01-15", "2024-01-31"],
            "total_amount": [100.0, 200.0, 300.0],
        })
        orders_df = _with_parsed_order_date(orders_df)
        prev_s, prev_e = _resolve_adaptive_previous_period(
            orders_df, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert prev_s is not None
        assert prev_e is not None
        assert prev_e == date(2023, 12, 31)

    def test_dataframe_vacio_devuelve_none(self):
        prev_s, prev_e = _resolve_adaptive_previous_period(
            pd.DataFrame(), date(2024, 1, 1), date(2024, 12, 31)
        )
        assert prev_s is None
        assert prev_e is None

    def test_datos_parciales_adapta_el_periodo(self):
        # Con datos solo hasta abril, el previo se adapta al mismo tramo del ano anterior
        orders_df = pd.DataFrame({
            "order_date": ["2024-01-01", "2024-04-30"],
            "total_amount": [100.0, 200.0],
        })
        orders_df = _with_parsed_order_date(orders_df)
        prev_s, prev_e = _resolve_adaptive_previous_period(
            orders_df, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert prev_e is not None
        assert prev_e < date(2024, 1, 1)