"""
file_parser.py — Primera capa del pipeline.

Responsabilidad: leer el fichero (CSV o XLSX) y devolver una lista de ParsedSheet.

Garantías de seguridad:
- El fichero NUNCA se escribe en disco — solo se trabaja con bytes en memoria
- Validación de magic bytes para detectar ficheros maliciosos renombrados
- Detección de XLSX con contraseña → mensaje claro

Edge cases manejados:
- XLSX con celdas combinadas (merged cells)
- XLSX con fórmulas en lugar de valores
- XLSX con filas/columnas ocultas
- XLSX con contraseña
- CSV con BOM UTF-8
- CSV con columnas duplicadas
- CSV/XLSX con columnas vacías o sin nombre
- CSV con columnas de nombre numérico
- CSV con solo cabecera y sin datos
- Encoding mixto o desconocido
"""
import io
import re
from dataclasses import dataclass
import pandas as pd


@dataclass
class ParsedSheet:
    sheet_name:    str
    dataframe:     pd.DataFrame
    source_format: str       # 'csv' o 'xlsx'
    row_count:     int
    column_count:  int
    columns:       list[str]
    warnings:      list[str]  # avisos no bloqueantes (columnas duplicadas, etc.)


# ─────────────────────────────────────────────
# VALIDACIÓN DE MAGIC BYTES
# ─────────────────────────────────────────────

def _validate_magic_bytes(content: bytes, filename: str) -> None:
    """
    Verifica que el contenido del fichero coincide con su extensión.
    Previene subida de ficheros maliciosos renombrados.

    Magic bytes conocidos:
    - XLSX/XLS: PK (ZIP format) → 50 4B
    - CSV: debe ser texto decodificable
    """
    filename_lower = filename.lower()

    if filename_lower.endswith((".xlsx", ".xls")):
        # XLSX es un ZIP — empieza con PK (0x50 0x4B)
        if not content[:2] == b"PK":
            raise ValueError(
                "El fichero no es un Excel válido. "
                "Asegúrate de que el fichero tiene formato .xlsx real."
            )
    elif filename_lower.endswith(".csv"):
        # CSV debe ser texto decodificable
        # Probar con los encodings más comunes
        sample = content[:2048]
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                sample.decode(encoding)
                return  # decodificable — es texto válido
            except (UnicodeDecodeError, Exception):
                continue
        raise ValueError(
            "El fichero no parece ser un CSV de texto válido. "
            "Verifica que el fichero no está corrupto o en formato binario."
        )


# ─────────────────────────────────────────────
# LIMPIEZA DE COLUMNAS
# ─────────────────────────────────────────────

def _clean_columns(df: pd.DataFrame, sheet_name: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Limpia los nombres de columna del DataFrame.

    Operaciones:
    1. Convertir a string y eliminar espacios extremos
    2. Eliminar columnas Unnamed (artefacto de pandas con Excel)
    3. Eliminar columnas completamente vacías
    4. Normalizar columnas con nombres numéricos
    5. Detectar y avisar sobre columnas duplicadas

    Returns: (df_limpio, lista_de_warnings)
    """
    warnings = []

    # 1. Limpiar nombres de columna
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Eliminar columnas Unnamed (artefacto de Excel/pandas)
    unnamed_cols = [c for c in df.columns if re.match(r"^Unnamed:\s*\d+", c)]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)
        warnings.append(
            f"Se eliminaron {len(unnamed_cols)} columna(s) sin nombre (Unnamed)"
        )

    # 3. Eliminar columnas completamente vacías
    before = len(df.columns)
    df = df.dropna(axis=1, how="all")
    after  = len(df.columns)
    if before != after:
        warnings.append(
            f"Se eliminaron {before - after} columna(s) completamente vacías"
        )

    # 4. Normalizar columnas con nombres numéricos o solo espacios
    renamed = {}
    for col in df.columns:
        if col.strip() == "":
            new_name = f"col_sin_nombre_{list(df.columns).index(col)}"
            renamed[col] = new_name
        elif re.match(r"^\d+$", col.strip()):
            new_name = f"col_{col.strip()}"
            renamed[col] = new_name

    if renamed:
        df = df.rename(columns=renamed)
        warnings.append(
            f"Se renombraron {len(renamed)} columna(s) con nombres numéricos o vacíos: "
            f"{list(renamed.values())}"
        )

    # 5. Detectar columnas duplicadas
    duplicated = df.columns[df.columns.duplicated()].tolist()
    if duplicated:
        warnings.append(
            f"Columnas duplicadas detectadas en '{sheet_name}': {duplicated}. "
            f"Se han renombrado automáticamente (col, col.1, col.2...)"
        )
        # pandas ya las renombra con .1, .2 — solo avisamos

    return df, warnings


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

    Maneja:
    - BOM UTF-8 (utf-8-sig)
    - Múltiples encodings (utf-8, latin-1, cp1252)
    - Múltiples separadores (coma, punto y coma, tabulador)
    - Fichero con solo cabecera → error claro
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

                # Una sola columna → separador incorrecto
                if len(df.columns) <= 1:
                    continue

                # Eliminar filas completamente vacías
                df = df.replace({"": None, "nan": None, "None": None})
                df = df.dropna(how="all")
                df = df.reset_index(drop=True)

                # Fichero con solo cabecera y sin datos
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
                raise  # re-lanzar errores de validación
            except Exception:
                continue

    raise ValueError(
        "No se pudo leer el CSV. "
        "Asegúrate de que el fichero es un CSV válido con columnas separadas "
        "por coma, punto y coma o tabulador, y que el encoding es UTF-8 o Latin-1."
    )


# ─────────────────────────────────────────────
# PARSER XLSX
# ─────────────────────────────────────────────

def _parse_xlsx(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee todas las hojas procesables de un XLSX.

    Maneja:
    - XLSX con contraseña → mensaje claro
    - Celdas combinadas → se tratan como NaN en pandas (comportamiento correcto)
    - Fórmulas → openpyxl con data_only=True lee el valor calculado
    - Filas/columnas ocultas → se incluyen (pandas no distingue)
    - Hojas vacías → se ignoran silenciosamente
    """
    try:
        xl = pd.ExcelFile(
            io.BytesIO(content),
            engine="openpyxl"
        )
    except Exception as e:
        error_str = str(e).lower()
        if "encrypted" in error_str or "password" in error_str or "decrypt" in error_str:
            raise ValueError(
                "El fichero Excel está protegido con contraseña. "
                "Elimina la protección antes de subir el fichero: "
                "Revisar → Proteger libro → Quitar protección."
            )
        raise ValueError(f"No se pudo abrir el fichero Excel: {str(e)}")

    sheets = []
    for sheet_name in xl.sheet_names:
        try:
            # data_only=True → leer valores calculados, no fórmulas
            df = xl.parse(
                sheet_name,
                dtype=str,
                keep_default_na=False
            )

            # Limpiar columnas
            df, col_warnings = _clean_columns(df, sheet_name)

            # Hoja con menos de 2 columnas → ignorar
            if len(df.columns) < 2:
                continue

            # Limpiar valores
            df = df.replace({"": None, "nan": None, "None": None})
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
            raise  # re-lanzar errores de validación
        except Exception:
            continue  # hoja con error de formato — ignorar y continuar

    if not sheets:
        raise ValueError(
            "El fichero Excel no contiene hojas con datos válidos. "
            "Asegúrate de que al menos una hoja tiene cabeceras y datos."
        )

    return sheets