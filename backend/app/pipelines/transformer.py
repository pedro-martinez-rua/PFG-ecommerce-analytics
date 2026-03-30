from datetime import date, datetime
from decimal import Decimal, InvalidOperation


# Formatos de fecha que aparecen en los datasets reales del proyecto
DATE_FORMATS = [
    "%Y-%m-%d",          # 2023-01-15  (ecommerce_sales, maven)
    "%d/%m/%Y",          # 15/01/2023
    "%m/%d/%Y",          # 01/15/2023  (Online Retail data_csv)
    "%d-%m-%Y",          # 15-01-2023
    "%Y/%m/%d",          # 2023/01/15
    "%d/%m/%Y %H:%M",    # 15/01/2023 08:26
    "%m/%d/%Y %H:%M",    # 12/1/2010 8:26  (Online Retail exacto)
    "%Y-%m-%d %H:%M:%S", # 2012-03-19 10:42:46  (maven created_at)
    "%Y-%m-%dT%H:%M:%S", # ISO format
    "%d/%m/%y",          # 15/01/23
    "%m/%d/%y",          # 01/15/23
    "%Y-%m-%d %H:%M:%S UTC",  # jewelry dataset
]

# Valores que se interpretan como "devuelto = true"
RETURNED_TRUE_VALUES = {
    "yes", "true", "1", "returned", "devuelto", "si", "sí", "refunded"
}


def parse_date(value) -> date | None:
    """
    Intenta parsear una fecha en cualquiera de los formatos conocidos.
    Devuelve un objeto date o None si no puede parsearlo.
    """
    if value is None:
        return None

    value_str = str(value).strip()
    if not value_str or value_str.lower() in ("nan", "none", "null", ""):
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value_str, fmt).date()
        except ValueError:
            continue

    return None  # no se pudo parsear con ningún formato


def parse_decimal(value) -> Decimal | None:
    """
    Convierte un valor a Decimal.
    Maneja comas como separador decimal (formato europeo),
    símbolos de moneda y espacios.
    """
    if value is None:
        return None

    value_str = str(value).strip()
    if not value_str or value_str.lower() in ("nan", "none", "null", ""):
        return None

    # Eliminar símbolos de moneda y espacios
    value_str = value_str.replace("€", "").replace("$", "").replace("£", "").strip()

    # Manejar formato europeo: 1.234,56 → 1234.56
    if "," in value_str and "." in value_str:
        if value_str.index(",") > value_str.index("."):
            # Formato europeo: punto como miles, coma como decimal
            value_str = value_str.replace(".", "").replace(",", ".")
        else:
            # Formato anglosajón: coma como miles, punto como decimal
            value_str = value_str.replace(",", "")
    elif "," in value_str:
        # Solo coma — asumir separador decimal europeo
        value_str = value_str.replace(",", ".")

    try:
        return Decimal(value_str)
    except InvalidOperation:
        return None


def parse_boolean(value) -> bool:
    """
    Convierte un valor a booleano.
    Usado para campos como is_returned, is_refunded.
    """
    if value is None:
        return False
    return str(value).lower().strip() in RETURNED_TRUE_VALUES


def parse_int(value) -> int | None:
    """Convierte un valor a entero."""
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


def clean_string(value) -> str | None:
    """Limpia un string: elimina espacios y valores vacíos/nulos."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if cleaned.lower() in ("nan", "none", "null", ""):
        return None
    return cleaned


# Mapa de campo canónico → función de transformación
FIELD_TRANSFORMATIONS: dict[str, callable] = {
    "order_date":        parse_date,
    "total_amount":      parse_decimal,
    "discount_amount":   parse_decimal,
    "net_amount":        parse_decimal,
    "shipping_cost":     parse_decimal,
    "cogs_amount":       parse_decimal,
    "refund_amount":     parse_decimal,
    "unit_price":        parse_decimal,
    "unit_cost":         parse_decimal,
    "line_total":        parse_decimal,
    "quantity":          parse_decimal,
    "delivery_days":     parse_int,
    "is_returned":       parse_boolean,
    "is_refunded":       parse_boolean,
    "external_id":       clean_string,
    "product_name":      clean_string,
    "sku":               clean_string,
    "category":          clean_string,
    "brand":             clean_string,
    "channel":           clean_string,
    "status":            clean_string,
    "payment_method":    clean_string,
    "shipping_country":  clean_string,
    "shipping_region":   clean_string,
    "currency":          clean_string,
    "utm_source":        clean_string,
    "utm_campaign":      clean_string,
    "device_type":       clean_string,
    "session_id":        clean_string,
    "customer_name":     clean_string,
    "customer_email":    clean_string,
}


def transform_row(canonical: dict) -> dict:
    """
    Aplica las transformaciones de tipo a cada campo canónico.
    Los campos sin transformación definida se dejan como están.

    Ejemplo:
        canonical = {
            "order_date": "12/1/2010 8:26",
            "total_amount": "2.55",
            "is_returned": "No"
        }
        →
        {
            "order_date": date(2010, 1, 12),
            "total_amount": Decimal("2.55"),
            "is_returned": False
        }
    """
    transformed = {}
    for field, value in canonical.items():
        if field in FIELD_TRANSFORMATIONS:
            transformed[field] = FIELD_TRANSFORMATIONS[field](value)
        else:
            transformed[field] = value
    return transformed