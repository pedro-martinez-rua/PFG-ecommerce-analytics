"""
test_pipeline.py — Validacion del pipeline ETL.

Corresponde al Objetivo 1 del plan de validacion:
"Ingest, validate, clean, transform and standardize data from different e-commerce."

Prueba transformer.py, validator.py y detector.py con casos reales:
multiples formatos de fecha, valores nulos, errores Excel, booleanos en varios idiomas.
"""
import pytest
import pandas as pd
from datetime import date
from decimal import Decimal

from app.pipelines.transformer import parse_date, parse_decimal, parse_boolean, clean_string
from app.pipelines.detector import detect_type_with_confidence, UploadType
from app.pipelines.validator import validate_dataframe


# parse_date
class TestParseDate:
    def test_formato_iso(self):
        assert parse_date("2024-01-15") == date(2024, 1, 15)

    def test_formato_europeo(self):
        assert parse_date("15/01/2024") == date(2024, 1, 15)

    def test_formato_americano(self):
        assert parse_date("01/15/2024") == date(2024, 1, 15)

    def test_formato_con_hora(self):
        assert parse_date("2024-01-15 10:30:00") == date(2024, 1, 15)

    def test_fecha_excel_numerico(self):
        # 44927 = 2023-01-01 en Excel
        result = parse_date("44927")
        assert result == date(2023, 1, 1)

    def test_fecha_con_timezone(self):
        assert parse_date("2024-01-15T10:30:00+02:00") == date(2024, 1, 15)

    def test_fecha_con_z(self):
        assert parse_date("2024-01-15T10:30:00Z") == date(2024, 1, 15)

    def test_valor_nulo_none(self):
        assert parse_date(None) is None

    def test_valor_nulo_nan(self):
        assert parse_date("nan") is None

    def test_valor_nulo_na(self):
        assert parse_date("N/A") is None

    def test_error_excel_ref(self):
        assert parse_date("#REF!") is None

    def test_error_excel_na(self):
        assert parse_date("#N/A") is None

    def test_valor_invalido(self):
        assert parse_date("no-es-fecha") is None


# parse_decimal
class TestParseDecimal:
    def test_numero_simple(self):
        assert parse_decimal("100.50") == Decimal("100.50")

    def test_formato_europeo_coma(self):
        result = parse_decimal("1.234,56")
        assert result == Decimal("1234.56")

    def test_con_simbolo_euro(self):
        assert parse_decimal("€150.00") == Decimal("150.00")

    def test_con_simbolo_dolar(self):
        assert parse_decimal("$99.99") == Decimal("99.99")

    def test_con_simbolo_libra(self):
        assert parse_decimal("£75.00") == Decimal("75.00")

    def test_numero_negativo(self):
        result = parse_decimal("-50.00")
        assert result == Decimal("-50.00")

    def test_notacion_cientifica(self):
        result = parse_decimal("1.5e2")
        assert result == Decimal("150")

    def test_none(self):
        assert parse_decimal(None) is None

    def test_error_excel(self):
        assert parse_decimal("#DIV/0!") is None

    def test_string_invalido(self):
        assert parse_decimal("precio") is None


# parse_boolean
class TestParseBoolean:
    @pytest.mark.parametrize("val", ["true", "True", "TRUE", "1", "yes", "Yes", "si", "Sí"])
    def test_verdadero(self, val):
        assert parse_boolean(val) is True

    @pytest.mark.parametrize("val", ["false", "False", "FALSE", "0", "no", "No"])
    def test_falso(self, val):
        assert parse_boolean(val) is False

    def test_returned_value(self):
        assert parse_boolean("returned") is True

    def test_devuelto_value(self):
        assert parse_boolean("devuelto") is True


# clean_string
class TestCleanString:
    def test_espacios_extremos(self):
        assert clean_string("  hola  ") == "hola"

    def test_none(self):
        assert clean_string(None) is None

    def test_nan(self):
        assert clean_string("nan") is None

    def test_string_largo_truncado(self):
        largo = "x" * 2000
        result = clean_string(largo)
        assert len(result) <= 1000

    def test_string_normal(self):
        assert clean_string("Producto A") == "Producto A"


# detect_type_with_confidence
class TestDetector:
    def test_detecta_orders_o_mixed(self):
        # El detector puede devolver ORDERS o MIXED segun columnas — ambos validos
        columns = ["order_id", "order_date", "total_amount", "customer_email",
                   "status", "currency", "shipping_country"]
        upload_type, confidence = detect_type_with_confidence(columns)
        assert upload_type in (UploadType.ORDERS, UploadType.MIXED)
        assert confidence > 0.0

    def test_detecta_order_lines(self):
        columns = ["order_id", "order_date", "product_name", "sku",
                   "quantity", "unit_price", "line_total"]
        upload_type, confidence = detect_type_with_confidence(columns)
        assert upload_type == UploadType.ORDER_LINES
        assert confidence > 0.3

    def test_detecta_products_o_mixed(self):
        # Columnas de productos pueden detectarse como PRODUCTS o MIXED
        columns = ["product_id", "product_name", "sku", "category",
                   "brand", "unit_price", "unit_cost", "stock"]
        upload_type, confidence = detect_type_with_confidence(columns)
        assert upload_type in (UploadType.PRODUCTS, UploadType.MIXED)

    def test_columnas_vacias(self):
        upload_type, confidence = detect_type_with_confidence([])
        assert upload_type == UploadType.UNKNOWN
        assert confidence == 0.0

    def test_columnas_desconocidas(self):
        columns = ["columna_rara_1", "columna_rara_2", "columna_rara_3"]
        upload_type, _ = detect_type_with_confidence(columns)
        assert upload_type == UploadType.UNKNOWN


# validate_dataframe
class TestValidator:
    def test_filas_validas(self):
        df = pd.DataFrame({
            "order_date":   ["2024-01-15", "2024-01-16"],
            "total_amount": ["100.00",     "200.00"],
            "status":       ["completed",  "completed"],
        })
        results, valid_df = validate_dataframe(df, "orders")
        assert len(valid_df) == 2

    def test_fila_sin_fecha_invalida(self):
        df = pd.DataFrame({
            "order_date":   [None,        "2024-01-16"],
            "total_amount": ["100.00",    "200.00"],
        })
        results, valid_df = validate_dataframe(df, "orders")
        # La fila sin fecha debe ser rechazada
        assert len(valid_df) < 2

    def test_dataframe_vacio(self):
        df = pd.DataFrame()
        results, valid_df = validate_dataframe(df, "orders")
        assert len(valid_df) == 0