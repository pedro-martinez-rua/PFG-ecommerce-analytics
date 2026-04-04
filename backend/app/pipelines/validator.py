"""
validator.py — Quinta capa del pipeline.

Usa Pandera para validación declarativa de schemas.
Clasifica cada fila como VALID / INVALID / REPAIRABLE / SKIPPED.

Tipos soportados: orders, order_lines, customers, products.
"""
import pandera as pa
from pandera import Column, DataFrameSchema, Check, errors as pa_errors
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RowStatus(str, Enum):
    VALID      = "valid"
    INVALID    = "invalid"
    REPAIRABLE = "repairable"
    SKIPPED    = "skipped"


@dataclass
class RowValidationResult:
    row_index: int
    status: RowStatus
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def _get_today():
    """
    Fecha actual en tiempo de ejecución.
    No usar constante global — si el servidor lleva días corriendo,
    la constante tendría la fecha del arranque.
    """
    return datetime.now().date()


# ─────────────────────────────────────────────
# SCHEMAS PANDERA
# strict=False → permite columnas extra (van a extra_attributes)
# coerce=False → NO convertir tipos — lo hace el transformer
# ─────────────────────────────────────────────

ORDERS_SCHEMA = DataFrameSchema(
    columns={
        "order_date": Column(
            pa.String, nullable=False, required=True,
            description="Fecha del pedido — obligatorio"
        ),
        "total_amount": Column(
            pa.String, nullable=True, required=False,
            checks=[Check(
                lambda s: s.isna() | s.str.replace(",", ".", regex=False)
                           .str.replace(r"[€$£\s]", "", regex=True)
                           .str.match(r"^-?[\d\.eE+]+$"),
                element_wise=True,
                error="total_amount debe ser un número válido"
            )]
        ),
        "discount_amount":  Column(pa.String, nullable=True, required=False),
        "shipping_cost":    Column(pa.String, nullable=True, required=False),
        "cogs_amount":      Column(pa.String, nullable=True, required=False),
        "currency":         Column(pa.String, nullable=True, required=False),
        "channel":          Column(pa.String, nullable=True, required=False),
        "status":           Column(pa.String, nullable=True, required=False),
        "payment_method":   Column(pa.String, nullable=True, required=False),
        "shipping_country": Column(pa.String, nullable=True, required=False),
        "shipping_region":  Column(pa.String, nullable=True, required=False),
        "delivery_days":    Column(pa.String, nullable=True, required=False),
        "is_returned":      Column(pa.String, nullable=True, required=False),
        "product_name":     Column(pa.String, nullable=True, required=False),
        "quantity":         Column(pa.String, nullable=True, required=False),
        "unit_price":       Column(pa.String, nullable=True, required=False),
        "category":         Column(pa.String, nullable=True, required=False),
        "brand":            Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

ORDER_LINES_SCHEMA = DataFrameSchema(
    columns={
        "external_id":     Column(pa.String, nullable=True, required=False),
        "product_name":    Column(pa.String, nullable=True, required=False),
        "sku":             Column(pa.String, nullable=True, required=False),
        "category":        Column(pa.String, nullable=True, required=False),
        "brand":           Column(pa.String, nullable=True, required=False),
        "quantity":        Column(pa.String, nullable=True, required=False),
        "unit_price":      Column(pa.String, nullable=True, required=False),
        "unit_cost":       Column(pa.String, nullable=True, required=False),
        "line_total":      Column(pa.String, nullable=True, required=False),
        "is_primary_item": Column(pa.String, nullable=True, required=False),
        "is_refunded":     Column(pa.String, nullable=True, required=False),
        "refund_amount":   Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

CUSTOMERS_SCHEMA = DataFrameSchema(
    columns={
        "customer_external_id": Column(pa.String, nullable=True, required=False),
        "customer_email": Column(
            pa.String, nullable=True, required=False,
            checks=[Check(
                lambda s: s.isna() | s.str.match(
                    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
                ),
                element_wise=True,
                error="customer_email debe ser un email válido"
            )]
        ),
        "customer_name":   Column(pa.String, nullable=True, required=False),
        "country":         Column(pa.String, nullable=True, required=False),
        "region":          Column(pa.String, nullable=True, required=False),
        "customer_rating": Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

PRODUCTS_SCHEMA = DataFrameSchema(
    columns={
        "product_name": Column(
            pa.String, nullable=False, required=True,
            description="Nombre del producto — obligatorio"
        ),
        "sku":          Column(pa.String, nullable=True, required=False),
        "category":     Column(pa.String, nullable=True, required=False),
        "brand":        Column(pa.String, nullable=True, required=False),
        "unit_price":   Column(pa.String, nullable=True, required=False),
        "unit_cost":    Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

SCHEMA_MAP = {
    "orders":      ORDERS_SCHEMA,
    "order_lines": ORDER_LINES_SCHEMA,
    "customers":   CUSTOMERS_SCHEMA,
    "products":    PRODUCTS_SCHEMA,
}

MINIMUM_REQUIRED_FIELDS = {
    "orders":      ["order_date"],
    "order_lines": [],
    "customers":   [],
    "products":    ["product_name"],
}


def validate_dataframe(
    df: pd.DataFrame,
    upload_type: str
) -> tuple[list[RowValidationResult], pd.DataFrame]:
    """
    Valida un DataFrame completo con Pandera en modo lazy.
    Devuelve (resultados por fila, DataFrame con filas procesables).
    """
    if df is None or df.empty:
        return [], df if df is not None else pd.DataFrame()

    results: list[RowValidationResult] = []
    schema         = SCHEMA_MAP.get(upload_type, ORDERS_SCHEMA)
    minimum_fields = MINIMUM_REQUIRED_FIELDS.get(upload_type, [])
    today          = _get_today()

    # Eliminar filas completamente vacías → SKIPPED
    empty_mask = df.isnull().all(axis=1) | (
        df.astype(str).replace("None", None).isnull().all(axis=1)
    )
    for idx in df[empty_mask].index:
        results.append(RowValidationResult(
            row_index=int(idx),
            status=RowStatus.SKIPPED,
            warnings=[{"message": "Fila completamente vacía — omitida"}]
        ))
    df = df[~empty_mask].copy()

    if df.empty:
        return results, df

    # Validación Pandera en modo lazy
    pandera_errors: dict[int, list[dict]] = {}
    try:
        schema.validate(df, lazy=True)
    except pa_errors.SchemaErrors as exc:
        for _, row in exc.failure_cases.iterrows():
            row_idx = int(row.get("index", -1)) if row.get("index") is not None else -1
            if row_idx not in pandera_errors:
                pandera_errors[row_idx] = []
            pandera_errors[row_idx].append({
                "field":      row.get("column", "unknown"),
                "error_type": row.get("check", "validation_error"),
                "value":      str(row.get("failure_case", "")),
                "message":    f"Validación fallida en '{row.get('column', '')}': {row.get('check', '')}"
            })

    # Clasificar cada fila
    valid_indices = []
    for idx, row in df.iterrows():
        row_errors = pandera_errors.get(int(idx), [])
        warnings   = []

        # Campos obligatorios mínimos
        missing_required = []
        for f in minimum_fields:
            val = row.get(f)
            if val is None or str(val).strip() in ("", "nan", "None", "NaT", "none"):
                missing_required.append(f)

        if missing_required:
            row_errors.append({
                "field":      ", ".join(missing_required),
                "error_type": "missing_required_field",
                "value":      None,
                "message":    f"Campo obligatorio ausente: {', '.join(missing_required)}"
            })

        # Customers: necesita al menos email o external_id
        if upload_type == "customers":
            has_email = bool(row.get("customer_email")) and \
                        str(row.get("customer_email", "")).strip() not in ("", "nan", "None")
            has_id    = bool(row.get("customer_external_id")) and \
                        str(row.get("customer_external_id", "")).strip() not in ("", "nan", "None")
            if not has_email and not has_id:
                row_errors.append({
                    "field":      "customer_email / customer_external_id",
                    "error_type": "missing_identifier",
                    "value":      None,
                    "message":    "Se necesita al menos email o ID de cliente"
                })

        # Validaciones de negocio para orders
        if upload_type in ("orders", "mixed"):
            qty_val = row.get("quantity")
            if qty_val is not None and str(qty_val).strip() not in ("", "nan", "None"):
                try:
                    qty = float(str(qty_val).replace(",", "."))
                    if qty < 0:
                        warnings.append({
                            "field":   "quantity",
                            "message": f"Cantidad negativa ({qty}) — puede indicar una devolución"
                        })
                except (ValueError, TypeError):
                    pass

            date_val = row.get("order_date")
            if date_val is not None and str(date_val).strip() not in ("", "nan", "None"):
                try:
                    from app.pipelines.transformer import parse_date
                    parsed_date = parse_date(str(date_val))
                    if parsed_date and parsed_date > today:
                        row_errors.append({
                            "field":      "order_date",
                            "error_type": "future_date",
                            "value":      str(date_val),
                            "message":    f"Fecha futura no permitida: {parsed_date}"
                        })
                except Exception:
                    pass

            amount_val  = row.get("total_amount")
            is_returned = str(row.get("is_returned", "")).lower() in (
                "yes", "true", "1", "returned", "devuelto", "si", "sí", "refunded"
            )
            if amount_val is not None and str(amount_val).strip() not in ("", "nan", "None"):
                try:
                    amount = float(
                        str(amount_val)
                        .replace(",", ".").replace("€", "")
                        .replace("$", "").replace("£", "").strip()
                    )
                    if amount < 0 and not is_returned:
                        warnings.append({
                            "field":   "total_amount",
                            "message": f"Importe negativo ({amount}) sin indicación de devolución"
                        })
                except (ValueError, TypeError):
                    pass

            if not row.get("total_amount") or \
               str(row.get("total_amount", "")).strip() in ("", "nan", "None"):
                warnings.append({
                    "field":   "total_amount",
                    "message": "Importe total ausente — KPIs financieros limitados para esta fila"
                })

        # Clasificar
        if not row_errors:
            status = RowStatus.VALID
            valid_indices.append(idx)
        elif missing_required or any(
            e.get("error_type") in ("missing_required_field", "future_date")
            for e in row_errors
        ):
            status = RowStatus.INVALID
        else:
            status = RowStatus.REPAIRABLE
            valid_indices.append(idx)

        results.append(RowValidationResult(
            row_index=int(idx),
            status=status,
            errors=row_errors,
            warnings=warnings
        ))

    processable_df = df.loc[df.index.isin(valid_indices)].copy()
    return results, processable_df


def build_validation_summary(results: list[RowValidationResult]) -> dict:
    """Resumen de validación para devolver al usuario."""
    total      = len(results)
    valid      = sum(1 for r in results if r.status == RowStatus.VALID)
    repairable = sum(1 for r in results if r.status == RowStatus.REPAIRABLE)
    invalid    = sum(1 for r in results if r.status == RowStatus.INVALID)
    skipped    = sum(1 for r in results if r.status == RowStatus.SKIPPED)

    error_counts: dict[str, int] = {}
    for r in results:
        for e in r.errors:
            key = f"{e['field']}: {e['error_type']}"
            error_counts[key] = error_counts.get(key, 0) + 1

    top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_rows":      total,
        "valid_rows":      valid,
        "repairable_rows": repairable,
        "invalid_rows":    invalid,
        "skipped_rows":    skipped,
        "processed_rows":  valid + repairable,
        "top_errors":      [{"error": k, "count": v} for k, v in top_errors],
        "has_warnings":    any(r.warnings for r in results),
    }