"""Robust file parser for CSV/XLSX imports."""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ParsedSheet:
    sheet_name: str
    dataframe: pd.DataFrame
    source_format: str
    row_count: int
    column_count: int
    columns: list[str]
    warnings: list[str] = field(default_factory=list)


DANGEROUS_SIGNATURES = [
    (b"\x4D\x5A", "ejecutable Windows (EXE/DLL)"),
    (b"\x7FELF", "ejecutable Linux (ELF)"),
    (b"\x89PNG\r\n\x1a\n", "imagen PNG"),
    (b"\xFF\xD8\xFF", "imagen JPEG"),
    (b"\x25\x50\x44\x46", "documento PDF"),
]


HEADER_LIKE_RE = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúñÑ_]")
DATE_LIKE_RE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")


def _validate_magic_bytes(content: bytes, filename: str) -> None:
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")) and content[:2] != b"PK":
        raise ValueError("El fichero no es un Excel válido.")
    if name.endswith(".csv"):
        for signature, description in DANGEROUS_SIGNATURES:
            if content[: len(signature)] == signature:
                raise ValueError(f"El fichero no es un CSV válido; parece un {description} renombrado.")


def _decode_text(content: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo decodificar el fichero como texto válido.")


def _normalize_headers(headers: list[str]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    normalized: list[str] = []
    seen: dict[str, int] = {}
    unnamed_count = 0

    for idx, header in enumerate(headers):
        raw = "" if header is None else str(header).strip()
        if not raw or raw.lower().startswith("unnamed"):
            unnamed_count += 1
            raw = f"extra_{idx + 1}"
        raw = re.sub(r"\s+", " ", raw)
        candidate = raw
        if candidate in seen:
            seen[candidate] += 1
            candidate = f"{candidate}_{seen[candidate]}"
        else:
            seen[candidate] = 0
        normalized.append(candidate)

    if unnamed_count:
        warnings.append(f"Se detectaron {unnamed_count} columna(s) sin nombre y se renombraron automáticamente.")
    return normalized, warnings


def _first_row_looks_like_header(values: list[str]) -> bool:
    non_empty = [_v for _v in values if _v]
    if not non_empty:
        return False
    textish = sum(1 for v in non_empty if HEADER_LIKE_RE.search(v))
    dateish = sum(1 for v in non_empty if DATE_LIKE_RE.search(v))
    mostly_numeric = sum(1 for v in non_empty if v.replace(",", "", 1).replace(".", "", 1).isdigit())
    return textish >= max(1, len(non_empty) // 2) and dateish == 0 and mostly_numeric < len(non_empty)


def _parse_csv(content: bytes, filename: str) -> list[ParsedSheet]:
    text, encoding = _decode_text(content)
    sample = text[:8192]
    warnings: list[str] = []

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
        counts = {sep: sample.count(sep) for sep in [",", ";", "\t", "|"]}
        best_sep, best_count = max(counts.items(), key=lambda item: item[1])
        if best_count > 0:
            delimiter = best_sep
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [row for row in reader]
    rows = [row for row in rows if any(str(cell).strip() for cell in row)]
    if not rows:
        raise ValueError(f"El fichero '{filename}' está vacío o no contiene filas legibles.")

    max_len = max(len(r) for r in rows)
    min_len = min(len(r) for r in rows)
    if max_len <= 1:
        raise ValueError("No se han detectado columnas separadas correctamente. Revisa el delimitador del CSV.")
    if max_len != min_len:
        warnings.append(
            f"La cabecera y/o las filas no tienen el mismo número de columnas (mínimo {min_len}, máximo {max_len})."
        )

    first = [str(v).strip() for v in rows[0]]
    has_header = _first_row_looks_like_header(first)
    if has_header:
        headers = first
        data_rows = rows[1:]
    else:
        headers = [f"column_{i + 1}" for i in range(max_len)]
        data_rows = rows
        warnings.append("No se detectó una cabecera clara; se generaron nombres de columna temporales.")

    normalized_headers, header_warnings = _normalize_headers(headers + [f"extra_{i+1}" for i in range(max_len - len(headers))])
    warnings.extend(header_warnings)

    normalized_rows = []
    extra_rows = 0
    short_rows = 0
    for row in data_rows:
        current = [None if str(v).strip() == "" else str(v).strip() for v in row]
        if len(current) < max_len:
            current = current + [None] * (max_len - len(current))
            short_rows += 1
        elif len(current) > max_len:
            current = current[:max_len]
            extra_rows += 1
        normalized_rows.append(current)

    if short_rows:
        warnings.append(f"{short_rows} fila(s) tenían menos columnas que el máximo detectado.")
    if extra_rows:
        warnings.append(f"{extra_rows} fila(s) tenían más columnas de las esperadas y se truncaron al ancho máximo.")

    df = pd.DataFrame(normalized_rows, columns=normalized_headers)
    df = df.replace({"": None, "nan": None, "None": None, "NaT": None})
    df = df.dropna(how="all").reset_index(drop=True)
    if df.empty:
        raise ValueError(f"El fichero '{filename}' contiene cabecera pero no filas de datos válidas.")

    warnings.append(f"CSV leído con delimitador '{delimiter}' y encoding '{encoding}'.")
    return [ParsedSheet(filename, df, "csv", len(df), len(df.columns), list(df.columns), warnings)]


def _parse_xlsx(content: bytes, filename: str) -> list[ParsedSheet]:
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    except Exception as exc:
        raise ValueError(f"No se pudo abrir el fichero Excel: {exc}") from exc

    sheets: list[ParsedSheet] = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.values)
        rows = [list(r) for r in rows if r and any(v not in (None, "") for v in r)]
        if not rows:
            continue
        first = ["" if v is None else str(v).strip() for v in rows[0]]
        has_header = _first_row_looks_like_header(first)
        if has_header:
            headers = first
            data_rows = rows[1:]
        else:
            headers = [f"column_{i + 1}" for i in range(len(first))]
            data_rows = rows
        normalized_headers, warnings = _normalize_headers(headers)
        df = pd.DataFrame(data_rows, columns=normalized_headers)
        df = df.where(pd.notna(df), None).dropna(how="all").reset_index(drop=True)
        if df.empty:
            continue
        sheets.append(ParsedSheet(sheet_name, df, "xlsx", len(df), len(df.columns), list(df.columns), warnings))
    if not sheets:
        raise ValueError("El Excel no contiene hojas procesables con datos.")
    return sheets


def parse_file(content: bytes, filename: str) -> list[ParsedSheet]:
    _validate_magic_bytes(content, filename)
    lower = filename.lower().strip()
    if lower.endswith((".xlsx", ".xls")):
        return _parse_xlsx(content, filename)
    if lower.endswith(".csv"):
        return _parse_csv(content, filename)
    raise ValueError("Formato no soportado. Se aceptan ficheros .csv y .xlsx.")
