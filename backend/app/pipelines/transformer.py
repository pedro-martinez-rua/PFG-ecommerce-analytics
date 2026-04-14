"""
transformer.py — Cuarta capa del pipeline.

Responsabilidad: convertir valores crudos al tipo correcto.
Opera sobre campos ya mapeados al schema canónico.

Maneja todos los edge cases reales de datos de e-commerce:
- Múltiples formatos de fecha (incluyendo fechas Excel como números)
- Fechas con timezone
- Números con formatos europeos, científicos, con símbolos de moneda
- Errores de Excel (#N/A, #REF!, etc.)
- Strings extremadamente largos
- Booleanos en múltiples idiomas y formatos
"""
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


# Formatos de fecha conocidos en datasets reales de e-commerce
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%y",
    "%m/%d/%y",
    "%Y-%m-%d %H:%M:%S UTC",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%d-%b-%Y",        # 15-Jan-2023
    "%d %b %Y",        # 15 Jan 2023
    "%B %d, %Y",       # January 15, 2023
]

# Valores que se interpretan como "devuelto = true"
RETURNED_TRUE_VALUES = {
    "yes", "true", "1", "returned", "devuelto", "si", "sí",
    "refunded", "yes returned", "return", "devuelta"
}

# Errores de Excel que deben convertirse a None
EXCEL_ERROR_VALUES = {
    "#n/a", "#ref!", "#div/0!", "#value!", "#name?",
    "#null!", "#num!", "#error!", "n/a", "na", "#na"
}

# Longitud máxima permitida para strings
MAX_STRING_LENGTH = 1000


def _is_excel_error(value_str: str) -> bool:
    """Detecta si un valor es un error de fórmula de Excel."""
    return value_str.lower().strip() in EXCEL_ERROR_VALUES


def _is_null_value(value_str: str) -> bool:
    """Detecta valores nulos en sus múltiples formas."""
    return value_str.lower().strip() in (
        "", "nan", "none", "null", "nat", "n/a", "na", "-", "—"
    )


def parse_date(value) -> date | None:
    """
    Parsea una fecha en cualquiera de los formatos conocidos.

    Casos especiales manejados:
    - Fechas Excel como números enteros (44927 = 01/01/2023)
    - Fechas con timezone (+02:00, Z, UTC)
    - Errores de Excel → None
    """
    if value is None:
        return None

    value_str = str(value).strip()

    if _is_null_value(value_str) or _is_excel_error(value_str):
        return None

    # Caso 1: fecha Excel como número entero (ej: 44927)
    try:
        numeric = float(value_str)
        if 1 < numeric < 100000:
            # Excel cuenta días desde 1899-12-30
            from datetime import timedelta
            excel_start = datetime(1899, 12, 30)
            return (excel_start + timedelta(days=int(numeric))).date()
    except (ValueError, TypeError):
        pass

    # Caso 2: fecha con timezone — extraer solo la parte de fecha
    tz_patterns = [
        r"(\d{4}-\d{2}-\d{2})[T ][\d:]+[+-]\d{2}:?\d{2}",  # ISO con offset
        r"(\d{4}-\d{2}-\d{2})[T ][\d:]+Z",                    # ISO con Z
        r"(\d{4}-\d{2}-\d{2})[T ][\d:]+ UTC",                 # ISO con UTC
        r"(\d{4}-\d{2}-\d{2})[T ][\d:]+\.\d+[+-]\d{2}:?\d{2}",  # con microsegundos
    ]
    for pattern in tz_patterns:
        match = re.match(pattern, value_str)
        if match:
            value_str = match.group(1)
            break

    # Caso 3: probar formatos conocidos
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value_str, fmt).date()
        except ValueError:
            continue

    # Caso 4: intentar pandas como último recurso
    try:
        import pandas as pd
        parsed = pd.to_datetime(value_str, errors="coerce")
        if parsed is not pd.NaT and parsed is not None:
            return parsed.date()
    except Exception:
        pass

    return None


def parse_decimal(value) -> Decimal | None:
    """
    Convierte un valor a Decimal.

    Casos especiales manejados:
    - Formato europeo: 1.234,56 → 1234.56
    - Formato anglosajón: 1,234.56 → 1234.56
    - Solo coma: 12,50 → 12.50
    - Símbolos de moneda: €, $, £
    - Notación científica: 1.5E+06 → 1500000
    - Errores de Excel → None
    """
    if value is None:
        return None

    value_str = str(value).strip()

    if _is_null_value(value_str) or _is_excel_error(value_str):
        return None

    # Eliminar símbolos de moneda y espacios
    value_str = re.sub(r"[€$£¥\s]", "", value_str)

    # Manejar notación científica (1.5E+06, 2.3e-4)
    if re.match(r"^-?[\d\.]+[eE][+-]?\d+$", value_str):
        try:
            return Decimal(str(float(value_str)))
        except (ValueError, InvalidOperation):
            return None

    # Determinar formato: europeo vs anglosajón
    if "," in value_str and "." in value_str:
        last_comma = value_str.rfind(",")
        last_dot   = value_str.rfind(".")
        if last_comma > last_dot:
            # Formato europeo: punto=miles, coma=decimal → 1.234,56
            value_str = value_str.replace(".", "").replace(",", ".")
        else:
            # Formato anglosajón: coma=miles, punto=decimal → 1,234.56
            value_str = value_str.replace(",", "")
    elif "," in value_str:
        # Solo coma — asumir decimal europeo: 12,50 → 12.50
        value_str = value_str.replace(",", ".")

    try:
        return Decimal(value_str)
    except InvalidOperation:
        return None


def parse_boolean(value) -> bool:
    """
    Convierte un valor a booleano.
    Maneja múltiples idiomas y formatos.
    """
    if value is None:
        return False
    return str(value).lower().strip() in RETURNED_TRUE_VALUES


def parse_int(value) -> int | None:
    """Convierte un valor a entero."""
    if value is None:
        return None
    value_str = str(value).strip()
    if _is_null_value(value_str) or _is_excel_error(value_str):
        return None
    try:
        return int(float(value_str))
    except (ValueError, TypeError):
        return None


def clean_string(value) -> str | None:
    """
    Limpia un string:
    - Elimina espacios extremos
    - Convierte valores nulos a None
    - Elimina errores de Excel
    - Trunca strings extremadamente largos
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    if _is_null_value(cleaned) or _is_excel_error(cleaned):
        return None

    # Truncar strings extremadamente largos
    if len(cleaned) > MAX_STRING_LENGTH:
        cleaned = cleaned[:MAX_STRING_LENGTH]

    return cleaned


# Mapa de campo canónico → función de transformación
FIELD_TRANSFORMATIONS: dict[str, callable] = {
    "order_date":         parse_date,
    "total_amount":       parse_decimal,
    "discount_amount":    parse_decimal,
    "net_amount":         parse_decimal,
    "shipping_cost":      parse_decimal,
    "cogs_amount":        parse_decimal,
    "refund_amount":      parse_decimal,
    "unit_price":         parse_decimal,
    "unit_cost":          parse_decimal,
    "line_total":         parse_decimal,
    "quantity":           parse_decimal,
    "customer_rating":    parse_decimal,
    "delivery_days":      parse_int,
    "is_returned":        parse_boolean,
    "is_refunded":        parse_boolean,
    "external_id":        clean_string,
    "product_name":       clean_string,
    "sku":                clean_string,
    "category":           clean_string,
    "brand":              clean_string,
    "channel":            clean_string,
    "status":             clean_string,
    "payment_method":     clean_string,
    "shipping_country":   clean_string,
    "shipping_region":    clean_string,
    "currency":           clean_string,
    "utm_source":         clean_string,
    "utm_campaign":       clean_string,
    "device_type":        clean_string,
    "session_id":         clean_string,
    "customer_name":      clean_string,
    "customer_email":     clean_string,
    "customer_external_id": clean_string,
    "product_external_id":  clean_string,
}


def transform_row(canonical: dict) -> dict:
    """
    Aplica transformaciones de tipo a cada campo canónico.
    Los campos sin transformación definida se limpian como string.

    Todos los errores por campo son silenciosos — un campo que no se puede
    transformar devuelve None en vez de romper la fila entera.
    """
    transformed = {}
    for field, value in canonical.items():
        try:
            if field in FIELD_TRANSFORMATIONS:
                transformed[field] = FIELD_TRANSFORMATIONS[field](value)
            else:
                # Campo sin transformación definida — limpiar como string
                transformed[field] = clean_string(value) if value is not None else None
        except Exception:
            # Nunca romper la fila por un campo individual
            transformed[field] = None
    return transformed