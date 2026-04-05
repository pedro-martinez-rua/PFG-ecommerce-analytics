from __future__ import annotations

from collections import Counter
from typing import Any
import pandas as pd


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def profile_dataframe(df: pd.DataFrame) -> dict:
    if df is None:
        df = pd.DataFrame()

    columns = [str(c) for c in df.columns]
    row_count = int(len(df))
    column_count = int(len(columns))
    null_ratio = {}
    inferred_types = {}

    for col in columns:
        series = df[col] if col in df.columns else pd.Series(dtype="object")
        cleaned = series.replace({"": None, "nan": None, "None": None})
        null_ratio[col] = round(float(cleaned.isna().mean()) if len(cleaned) else 0.0, 2)

        sample = cleaned.dropna().head(25).astype(str)
        if sample.empty:
            inferred_types[col] = "empty"
            continue

        numeric_ratio = sample.apply(lambda x: x.replace(",", ".", 1).replace("-", "", 1).replace("%", "").replace("$", "").replace("€", "").replace("£", "").replace(" ", "").replace(".", "", 1).isdigit()).mean()
        date_ratio = pd.to_datetime(sample, errors="coerce").notna().mean()
        if date_ratio >= 0.6:
            inferred_types[col] = "date"
        elif numeric_ratio >= 0.7:
            inferred_types[col] = "number"
        else:
            inferred_types[col] = "string"

    warnings: list[str] = []
    if row_count == 0:
        warnings.append("El archivo no contiene filas de datos legibles.")

    max_fields = column_count
    min_fields = column_count
    # When data comes from dict rows, exact field width is not recoverable, but sparse rows still show as NaN.
    if row_count > 0:
        filled_counts = df.notna().sum(axis=1)
        if len(filled_counts):
            max_fields = int(filled_counts.max())
            min_fields = int(filled_counts.min())
            if max_fields != min_fields:
                warnings.append("Las filas no tienen una estructura uniforme; algunas contienen más valores que otras.")

    duplicate_like = [c for c, n in Counter([c.lower() for c in columns]).items() if n > 1]
    if duplicate_like:
        warnings.append("Se detectaron cabeceras potencialmente duplicadas.")

    unresolved_candidates = []
    for col in columns:
        if inferred_types.get(col) in {"date", "number", "string"}:
            unresolved_candidates.append({
                "column": col,
                "inferred_type": inferred_types.get(col),
                "null_ratio": null_ratio.get(col, 0),
            })

    return {
        "row_count": row_count,
        "column_count": column_count,
        "columns": columns,
        "null_ratio": null_ratio,
        "inferred_types": inferred_types,
        "max_fields_in_row": max_fields,
        "min_fields_in_row": min_fields,
        "warnings": warnings,
        "column_candidates": unresolved_candidates,
    }


def dataframe_from_raw_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)
