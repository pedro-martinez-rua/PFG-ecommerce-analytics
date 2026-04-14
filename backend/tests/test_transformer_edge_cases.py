import pytest
from decimal import Decimal
from datetime import date
from app.pipelines.transformer import (
    parse_date, parse_decimal, parse_boolean, clean_string, transform_row
)


# Fechas reales problemáticas

class TestFechasEdgeCase:
    @pytest.mark.parametrize("valor,esperado", [
        ("44927",           date(2023, 1, 1)),    # Excel serial
        ("45292",           date(2024, 1, 1)),    # Excel serial 2024
        ("2023-01-01",      date(2023, 1, 1)),    # ISO
        ("01/01/2023",      date(2023, 1, 1)),    # DD/MM/YYYY
        ("1/1/23",          date(2023, 1, 1)),    # DD/M/YY
        ("January 1, 2023", date(2023, 1, 1)),    # nombre del mes
        ("01-Jan-2023",     date(2023, 1, 1)),    # abreviatura
        ("2023-01-01T00:00:00Z",       date(2023, 1, 1)),  # ISO con Z
        ("2023-01-01T00:00:00+01:00",  date(2023, 1, 1)),  # ISO con offset
    ])
    def test_formatos_varios(self, valor, esperado):
        assert parse_date(valor) == esperado

    @pytest.mark.parametrize("valor", [
        None, "", "nan", "NaN", "NULL", "null", "N/A", "n/a", "NA", "-", "—",
        "#N/A", "#REF!", "#DIV/0!", "#VALUE!", "#NAME?",
    ])
    def test_valores_nulos_y_errores(self, valor):
        assert parse_date(valor) is None


# Precios reales problemáticos

class TestPreciosEdgeCase:
    @pytest.mark.parametrize("valor,esperado", [
        ("100",          Decimal("100")),
        ("100.50",       Decimal("100.50")),
        ("100,50",       Decimal("100.50")),      # coma decimal europea
        ("1.234,56",     Decimal("1234.56")),      # separadores europeos
        ("1,234.56",     Decimal("1234.56")),      # separadores americanos
        ("€ 150.00",     Decimal("150.00")),       # euro con espacio
        ("€150",         Decimal("150")),          # euro sin espacio
        ("$99.99",       Decimal("99.99")),        # dólar
        ("£75.50",       Decimal("75.50")),        # libra
        ("-50.00",       Decimal("-50.00")),       # negativo
        ("1.5e2",        Decimal("150")),           # notación científica
        ("0",            Decimal("0")),
    ])
    def test_formatos_numericos(self, valor, esperado):
        result = parse_decimal(valor)
        assert result == esperado

    @pytest.mark.parametrize("valor", [
        None, "", "nan", "NULL", "N/A",
        "#N/A", "#REF!", "#DIV/0!", "#VALUE!",
        "precio", "n/d", "—",
    ])
    def test_valores_no_numericos(self, valor):
        assert parse_decimal(valor) is None


# Booleanos multilingual

class TestBooleanoEdgeCase:
    @pytest.mark.parametrize("valor", [
        "true", "True", "TRUE", "1", "yes", "Yes", "YES",
        "si", "sí", "Sí", "SÍ",
        "returned", "Returned", "RETURNED",
        "devuelto", "Devuelto", "DEVUELTO",
        "refunded", "yes returned",
    ])
    def test_true_variants(self, valor):
        assert parse_boolean(valor) is True

    @pytest.mark.parametrize("valor", [
        "false", "False", "FALSE", "0", "no", "No", "NO",
    ])
    def test_false_variants(self, valor):
        assert parse_boolean(valor) is False


# clean_string

class TestCleanStringEdgeCase:
    def test_espacios_multiples_internos_preservados(self):
        result = clean_string("  Producto   A  ")
        assert result == "Producto   A"

    def test_string_solo_espacios(self):
        result = clean_string("   ")
        # espacios solo → string vacío o None
        assert result is None or result == ""

    def test_string_muy_largo_truncado(self):
        largo = "a" * 5000
        result = clean_string(largo)
        assert len(result) <= 1000

    @pytest.mark.parametrize("valor", [None, "nan", "none", "null", "NULL", "NaN"])
    def test_valores_nulos(self, valor):
        assert clean_string(valor) is None


# transform_row
class TestTransformRow:
    def test_transforma_fila_completa(self):
        canonical = {
            "order_date":    "15/01/2024",
            "total_amount":  "€1.250,00",
            "is_returned":   "no",
            "delivery_days": "5",
            "status":        "  completed  ",
        }
        result = transform_row(canonical)
        assert result["order_date"] == date(2024, 1, 15)
        assert result["total_amount"] == Decimal("1250.00")
        assert result["is_returned"] is False
        assert result["delivery_days"] == 5
        assert result["status"] == "completed"

    def test_fila_con_errores_excel(self):
        canonical = {
            "order_date":   "#REF!",
            "total_amount": "#N/A",
            "status":       "completed",
        }
        result = transform_row(canonical)
        assert result["order_date"] is None
        assert result["total_amount"] is None

    def test_fila_con_fecha_excel_serial(self):
        canonical = {
            "order_date":   "44927",   # 2023-01-01
            "total_amount": "500",
        }
        result = transform_row(canonical)
        assert result["order_date"] == date(2023, 1, 1)

    def test_fila_vacia(self):
        result = transform_row({})
        assert isinstance(result, dict)