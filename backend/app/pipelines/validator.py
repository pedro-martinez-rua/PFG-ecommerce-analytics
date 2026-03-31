import pandera.pandas as pa
from pandera import Column, DataFrameSchema, Check, errors as pa_errors
import pandas as pd
from dataclasses import dataclass
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
    errors: list[dict]   # [{field, error_type, value, message}]
    warnings: list[dict] # campos opcionales con valores sospechosos


# ─────────────────────────────────────────────
# SCHEMAS PANDERA POR TIPO DE ENTIDAD
# Cada campo canónico tiene su tipo y sus checks.
# nullable=True significa que la columna puede no existir en el CSV
# o tener valores nulos — no bloquea la fila.
# ─────────────────────────────────────────────

ORDERS_SCHEMA = DataFrameSchema(
    columns={
        # OBLIGATORIOS — su ausencia invalida la fila
        "order_date": Column(
            pa.String,
            nullable=False,
            required=True,
            description="Fecha del pedido — campo obligatorio"
        ),

        # IMPORTANTES — su ausencia genera warning pero no invalida
        "total_amount": Column(
            pa.String,
            nullable=True,
            required=False,
            checks=[
                Check(
                    lambda s: s.isna() | s.str.replace(",", ".", regex=False)
                               .str.replace(r"[€$£\s]", "", regex=True)
                               .str.match(r"^-?[\d\.]+$"),
                    element_wise=True,
                    error="total_amount must be a valid number"
                )
            ],
            description="Importe total del pedido"
        ),

        # OPCIONALES — se procesan si existen, se ignoran si no
        "discount_amount": Column(pa.String, nullable=True, required=False),
        "shipping_cost":   Column(pa.String, nullable=True, required=False),
        "cogs_amount":     Column(pa.String, nullable=True, required=False),
        "currency":        Column(pa.String, nullable=True, required=False),
        "channel":         Column(pa.String, nullable=True, required=False),
        "status":          Column(pa.String, nullable=True, required=False),
        "payment_method":  Column(pa.String, nullable=True, required=False),
        "shipping_country":Column(pa.String, nullable=True, required=False),
        "shipping_region": Column(pa.String, nullable=True, required=False),
        "delivery_days":   Column(pa.String, nullable=True, required=False),
        "is_returned":     Column(pa.String, nullable=True, required=False),
        "product_name":    Column(pa.String, nullable=True, required=False),
        "quantity":        Column(pa.String, nullable=True, required=False),
        "unit_price":      Column(pa.String, nullable=True, required=False),
        "category":        Column(pa.String, nullable=True, required=False),
        "brand":           Column(pa.String, nullable=True, required=False),
    },
    strict=False,      # permite columnas extra — van a extra_attributes
    coerce=False,      # NO convertir tipos automáticamente — lo hace el transformer
)

CUSTOMERS_SCHEMA = DataFrameSchema(
    columns={
        "customer_external_id": Column(pa.String, nullable=True, required=False),
        "customer_email": Column(
            pa.String,
            nullable=True,
            required=False,
            checks=[
                Check(
                    lambda s: s.isna() | s.str.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$"),
                    element_wise=True,
                    error="customer_email must be a valid email address"
                )
            ]
        ),
        "customer_name":    Column(pa.String, nullable=True, required=False),
        "country":          Column(pa.String, nullable=True, required=False),
        "region":           Column(pa.String, nullable=True, required=False),
        "customer_rating":  Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

PRODUCTS_SCHEMA = DataFrameSchema(
    columns={
        "product_name": Column(
            pa.String,
            nullable=False,
            required=True,
            description="Nombre del producto — campo obligatorio"
        ),
        "sku":        Column(pa.String, nullable=True, required=False),
        "category":   Column(pa.String, nullable=True, required=False),
        "brand":      Column(pa.String, nullable=True, required=False),
        "unit_price": Column(pa.String, nullable=True, required=False),
        "unit_cost":  Column(pa.String, nullable=True, required=False),
    },
    strict=False,
    coerce=False,
)

SCHEMA_MAP = {
    "orders":    ORDERS_SCHEMA,
    "customers": CUSTOMERS_SCHEMA,
    "products":  PRODUCTS_SCHEMA,
}

# Campos mínimos requeridos por tipo para que la fila sea procesable
MINIMUM_REQUIRED_FIELDS = {
    "orders":    ["order_date"],
    "customers": [],            # al menos uno de los dos se comprueba en lógica
    "products":  ["product_name"],
}


def validate_dataframe(
    df: pd.DataFrame,
    upload_type: str
) -> tuple[list[RowValidationResult], pd.DataFrame]:
    """
    Valida un DataFrame completo usando Pandera.

    Devuelve:
    - list[RowValidationResult]: resultado por fila con errores detallados
    - pd.DataFrame: solo las filas válidas o reparables (para continuar el pipeline)

    Proceso:
    1. Renombrar columnas al schema canónico (ya mapeadas por mapper.py)
    2. Eliminar filas completamente vacías → SKIPPED
    3. Validar con Pandera el DataFrame completo
    4. Clasificar cada fila: VALID / INVALID / REPAIRABLE
    5. Devolver resultados + DataFrame limpio
    """
    results: list[RowValidationResult] = []
    schema = SCHEMA_MAP.get(upload_type, ORDERS_SCHEMA)
    minimum_fields = MINIMUM_REQUIRED_FIELDS.get(upload_type, [])

    # Paso 1 — Eliminar filas completamente vacías
    empty_mask = df.isnull().all(axis=1) | (df == "").all(axis=1)
    for idx in df[empty_mask].index:
        results.append(RowValidationResult(
            row_index=int(idx),
            status=RowStatus.SKIPPED,
            errors=[],
            warnings=[{"message": "Fila completamente vacía — omitida"}]
        ))
    df = df[~empty_mask].copy()

    # Paso 2 — Validar con Pandera (lazy=True recoge TODOS los errores, no para en el primero)
    pandera_errors: dict[int, list[dict]] = {}
    try:
        schema.validate(df, lazy=True)
    except pa_errors.SchemaErrors as exc:
        # exc.failure_cases es un DataFrame con todos los errores encontrados
        for _, row in exc.failure_cases.iterrows():
            row_idx = int(row.get("index", -1)) if row.get("index") is not None else -1
            if row_idx not in pandera_errors:
                pandera_errors[row_idx] = []
            pandera_errors[row_idx].append({
                "field":      row.get("column", "unknown"),
                "error_type": row.get("check", "validation_error"),
                "value":      str(row.get("failure_case", "")),
                "message":    f"Validation failed: {row.get('check', '')} on column '{row.get('column', '')}'"
            })

    # Paso 3 — Clasificar cada fila
    valid_indices = []
    for idx, row in df.iterrows():
        row_errors = pandera_errors.get(int(idx), [])
        warnings = []

        # Verificar campos mínimos obligatorios
        missing_required = []
        for field in minimum_fields:
            val = row.get(field)
            if val is None or str(val).strip() in ("", "nan", "None", "NaT"):
                missing_required.append(field)

        if missing_required:
            row_errors.append({
                "field":      ", ".join(missing_required),
                "error_type": "missing_required_field",
                "value":      None,
                "message":    f"Campo obligatorio ausente: {', '.join(missing_required)}"
            })

        # Lógica especial para customers: necesita al menos email o external_id
        if upload_type == "customers":
            has_email = bool(row.get("customer_email")) and str(row.get("customer_email")).strip() not in ("", "nan")
            has_id    = bool(row.get("customer_external_id")) and str(row.get("customer_external_id")).strip() not in ("", "nan")
            if not has_email and not has_id:
                row_errors.append({
                    "field":      "customer_email / customer_external_id",
                    "error_type": "missing_identifier",
                    "value":      None,
                    "message":    "Se necesita al menos email o ID de cliente"
                })

        # Warnings — campos importantes pero no obligatorios que están vacíos
        if upload_type == "orders":
            if not row.get("total_amount") or str(row.get("total_amount")).strip() in ("", "nan"):
                warnings.append({
                    "field":   "total_amount",
                    "message": "Importe total ausente — algunos KPIs financieros no estarán disponibles"
                })

        # Clasificar la fila
        if not row_errors:
            status = RowStatus.VALID
            valid_indices.append(idx)
        elif missing_required:
            # Tiene errores en campos obligatorios → INVALID
            status = RowStatus.INVALID
        else:
            # Tiene errores en campos opcionales → REPAIRABLE (se carga parcialmente)
            status = RowStatus.REPAIRABLE
            valid_indices.append(idx)

        results.append(RowValidationResult(
            row_index=int(idx),
            status=status,
            errors=row_errors,
            warnings=warnings
        ))

    # Devolver solo las filas válidas o reparables
    processable_df = df.loc[df.index.isin(valid_indices)].copy()

    return results, processable_df


def build_validation_summary(results: list[RowValidationResult]) -> dict:
    """
    Construye el resumen de validación para devolver al usuario.
    Este resumen va en el ImportResponse y en la tabla imports.
    """
    total     = len(results)
    valid     = sum(1 for r in results if r.status == RowStatus.VALID)
    repairable= sum(1 for r in results if r.status == RowStatus.REPAIRABLE)
    invalid   = sum(1 for r in results if r.status == RowStatus.INVALID)
    skipped   = sum(1 for r in results if r.status == RowStatus.SKIPPED)

    # Errores más frecuentes — útil para el usuario
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