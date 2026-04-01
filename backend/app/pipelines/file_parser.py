"""
file_parser.py — Primera capa del pipeline.

Responsabilidad: leer el fichero (CSV o XLSX) y devolver una lista de ParsedSheet.

Garantías de seguridad:
- El fichero NUNCA se escribe en disco — solo se trabaja con bytes en memoria
- Validación de magic bytes real contra ejecutables y binarios renombrados
- Detección de XLSX con contraseña → mensaje claro

Edge cases manejados:
- XLSX con celdas combinadas (merged cells)
- XLSX con fórmulas → se leen los valores calculados (openpyxl data_only=True)
- XLSX con filas/columnas ocultas
- XLSX con contraseña
- CSV con BOM UTF-8
- CSV con columnas duplicadas
- CSV/XLSX con columnas vacías o sin nombre
- CSV con columnas de nombre numérico
- CSV con solo cabecera y sin datos
- Encoding mixto o desconocido
- Ficheros binarios renombrados como CSV/XLSX
"""
import io
import re
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class ParsedSheet:
    sheet_name:    str
    dataframe:     pd.DataFrame
    source_format: str        # 'csv' o 'xlsx'
    row_count:     int
    column_count:  int
    columns:       list[str]
    warnings:      list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# FIRMAS DE FICHEROS PELIGROSOS
# Bytes que identifican ficheros binarios que no son CSV/XLSX
# ─────────────────────────────────────────────
DANGEROUS_SIGNATURES = [
    (b"\x4D\x5A",           "ejecutable Windows (EXE/DLL)"),
    (b"\x7FELF",            "ejecutable Linux (ELF)"),
    (b"\x89PNG\r\n\x1a\n",  "imagen PNG"),
    (b"\xFF\xD8\xFF",       "imagen JPEG"),
    (b"\x25\x50\x44\x46",  "documento PDF"),
    (b"GIF87a",             "imagen GIF"),
    (b"GIF89a",             "imagen GIF"),
    (b"\x00\x00\x01\x00",  "icono ICO"),
    (b"BM",                 "imagen BMP"),
    (b"\x1f\x8b",          "archivo GZIP"),
    (b"Rar!\x1a\x07",      "archivo RAR"),
]


# ─────────────────────────────────────────────
# VALIDACIÓN DE MAGIC BYTES
# ─────────────────────────────────────────────

def _validate_magic_bytes(content: bytes, filename: str) -> None:
    """
    Verifica que el contenido del fichero coincide con su extensión.
    Previene subida de ficheros maliciosos renombrados.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith((".xlsx", ".xls")):
        # XLSX es un ZIP — empieza con PK (0x50 0x4B)
        if content[:2] != b"PK":
            raise ValueError(
                "El fichero no es un Excel válido. "
                "Asegúrate de que el fichero tiene formato .xlsx real "
                "y no está renombrado desde otro formato."
            )

    elif filename_lower.endswith(".csv"):
        # Verificar que no es un binario peligroso renombrado
        for signature, description in DANGEROUS_SIGNATURES:
            if content[:len(signature)] == signature:
                raise ValueError(
                    f"El fichero no es un CSV válido — "
                    f"parece ser un {description} renombrado como .csv. "
                    f"Solo se aceptan ficheros de texto CSV reales."
                )

        # Verificar que es texto decodificable
        sample = content[:4096]
        decoded = False
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                sample.decode(encoding)
                decoded = True
                break
            except UnicodeDecodeError:
                continue

        if not decoded:
            raise ValueError(
                "El fichero no parece ser texto válido. "
                "Verifica que el fichero CSV no está corrupto o en formato binario."
            )


# ─────────────────────────────────────────────
# LIMPIEZA DE COLUMNAS
# ─────────────────────────────────────────────

def _clean_columns(df: pd.DataFrame, sheet_name: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Limpia los nombres de columna del DataFrame.

    Operaciones (en orden):
    1. Convertir a string y eliminar espacios extremos
    2. Eliminar columnas Unnamed (artefacto de pandas con Excel)
    3. Eliminar columnas completamente vacías
    4. Normalizar columnas con nombres numéricos o vacíos
    5. Detectar y avisar sobre columnas duplicadas
    """
    col_warnings = []

    # 1. Limpiar nombres de columna
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Eliminar columnas Unnamed (artefacto de Excel/pandas al exportar)
    unnamed_cols = [c for c in df.columns if re.match(r"^Unnamed:\s*\d+", c)]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)
        col_warnings.append(
            f"Se eliminaron {len(unnamed_cols)} columna(s) sin nombre (Unnamed) en '{sheet_name}'"
        )

    # 3. Eliminar columnas completamente vacías
    before = len(df.columns)
    df = df.dropna(axis=1, how="all")
    after = len(df.columns)
    if before != after:
        col_warnings.append(
            f"Se eliminaron {before - after} columna(s) completamente vacías en '{sheet_name}'"
        )

    # 4. Normalizar columnas con nombres numéricos o solo espacios
    # Usar enumerate para evitar list.index() que es O(n)
    renamed = {}
    for i, col in enumerate(df.columns):
        if col.strip() == "":
            renamed[col] = f"col_sin_nombre_{i}"
        elif re.match(r"^\d+$", col.strip()):
            renamed[col] = f"col_{col.strip()}"

    if renamed:
        df = df.rename(columns=renamed)
        col_warnings.append(
            f"Se renombraron {len(renamed)} columna(s) con nombres numéricos o vacíos "
            f"en '{sheet_name}': {list(renamed.values())}"
        )

    # 5. Detectar columnas duplicadas (pandas ya las renombra con .1, .2...)
    duplicated = df.columns[df.columns.duplicated()].tolist()
    if duplicated:
        col_warnings.append(
            f"Columnas duplicadas en '{sheet_name}': {duplicated}. "
            f"Se han renombrado automáticamente (nombre, nombre.1, nombre.2...)"
        )

    return df, col_warnings


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def parse_file(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee un fichero CSV o XLSX y devuelve una lista de ParsedSheet.

    Para CSV: lista con 1 elemento.
    Para XLSX: 1 elemento por hoja procesable.

    El fichero NUNCA se escribe en disco.
    """
    # Validar magic bytes antes de intentar parsear
    _validate_magic_bytes(content, filename)

    filename_lower = filename.lower().strip()

    if filename_lower.endswith((".xlsx", ".xls")):
        return _parse_xlsx(content, filename)
    elif filename_lower.endswith(".csv"):
        return _parse_csv(content, filename)
    else:
        raise ValueError(
            f"Formato no soportado: '{filename}'. "
            f"Se aceptan ficheros .csv y .xlsx"
        )


# ─────────────────────────────────────────────
# PARSER CSV
# ─────────────────────────────────────────────

def _parse_csv(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee un CSV probando combinaciones de encoding y separador.

    Encodings: utf-8-sig (BOM), utf-8, latin-1, cp1252
    Separadores: coma, punto y coma, tabulador
    """
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    sep=sep,
                    dtype=str,
                    on_bad_lines="skip",
                    keep_default_na=False
                )

                # Limpiar columnas
                df, col_warnings = _clean_columns(df, filename)

                # Una sola columna → separador incorrecto, probar siguiente
                if len(df.columns) <= 1:
                    continue

                # Limpiar valores nulos en sus múltiples formas
                df = df.replace({"": None, "nan": None, "None": None, "NaT": None})
                df = df.dropna(how="all")
                df = df.reset_index(drop=True)

                # Fichero con solo cabecera y sin datos → error claro
                if len(df) == 0:
                    raise ValueError(
                        f"El fichero '{filename}' contiene cabeceras pero ningún dato. "
                        f"Columnas encontradas: {list(df.columns)}. "
                        f"Añade al menos una fila de datos."
                    )

                return [ParsedSheet(
                    sheet_name=filename,
                    dataframe=df,
                    source_format="csv",
                    row_count=len(df),
                    column_count=len(df.columns),
                    columns=list(df.columns),
                    warnings=col_warnings
                )]

            except ValueError:
                raise  # re-lanzar errores de validación propios
            except Exception:
                continue  # probar siguiente combinación encoding/sep

    raise ValueError(
        "No se pudo leer el CSV. "
        "Asegúrate de que el fichero es un CSV válido con columnas separadas "
        "por coma, punto y coma o tabulador, y encoding UTF-8 o Latin-1."
    )


# ─────────────────────────────────────────────
# PARSER XLSX
# ─────────────────────────────────────────────

def _parse_xlsx(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee todas las hojas procesables de un XLSX.

    Usa openpyxl con data_only=True para leer valores calculados,
    no las fórmulas en bruto. Maneja:
    - XLSX con contraseña → mensaje claro
    - Celdas combinadas → pandas las trata como NaN (correcto)
    - Fórmulas → se leen los valores calculados, no =SUM(...)
    - Hojas vacías → se ignoran silenciosamente
    """
    import openpyxl

    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(content),
            data_only=True,   # leer valores calculados, NO fórmulas
            read_only=True    # no cargar todo en memoria
        )
    except Exception as e:
        error_str = str(e).lower()
        if any(kw in error_str for kw in ["encrypted", "password", "decrypt", "protected"]):
            raise ValueError(
                "El fichero Excel está protegido con contraseña. "
                "Elimina la protección antes de subir: "
                "Revisar → Proteger libro → Quitar protección."
            )
        raise ValueError(f"No se pudo abrir el fichero Excel: {str(e)}")

    sheets = []
    for sheet_name in wb.sheetnames:
        try:
            ws = wb[sheet_name]

            # Leer todas las filas como valores
            all_rows = list(ws.values)
            if not all_rows:
                continue

            # Primera fila = cabeceras
            headers = [
                str(c).strip() if c is not None else f"col_{i}"
                for i, c in enumerate(all_rows[0])
            ]

            # Resto de filas = datos
            data_rows = [
                [str(cell) if cell is not None else None for cell in row]
                for row in all_rows[1:]
            ]

            if not data_rows:
                continue

            df = pd.DataFrame(data_rows, columns=headers)

            # Limpiar columnas
            df, col_warnings = _clean_columns(df, sheet_name)

            # Hoja con menos de 2 columnas → ignorar
            if len(df.columns) < 2:
                continue

            # Limpiar valores nulos
            df = df.replace({"": None, "nan": None, "None": None, "NaT": None})
            df = df.dropna(how="all")
            df = df.reset_index(drop=True)

            # Hoja sin datos → ignorar silenciosamente
            if len(df) == 0:
                continue

            sheets.append(ParsedSheet(
                sheet_name=sheet_name,
                dataframe=df,
                source_format="xlsx",
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns),
                warnings=col_warnings
            ))

        except ValueError:
            raise
        except Exception:
            continue  # hoja con error de formato — ignorar y continuar

    wb.close()

    if not sheets:
        raise ValueError(
            "El fichero Excel no contiene hojas con datos válidos. "
            "Asegúrate de que al menos una hoja tiene cabeceras y datos."
        )

    return sheets