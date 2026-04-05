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
- Falta de encabezado (mas abajo)
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

def _infer_header_from_content(df: pd.DataFrame) -> pd.DataFrame:
    """
    Si el CSV no tiene cabecera real, intenta inferir nombres de columna
    analizando el tipo de dato de cada columna.
    Se activa cuando los nombres de columna son numéricos (0, 1, 2...)
    o cuando la primera fila parece datos reales, no cabeceras.
    """
    import re

    def _looks_like_date(series: pd.Series) -> bool:
        sample = series.dropna().head(10)
        date_pattern = re.compile(
            r'\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}'
        )
        return sample.astype(str).apply(lambda v: bool(date_pattern.search(v))).mean() > 0.7

    def _looks_like_big_int(series: pd.Series) -> bool:
        sample = series.dropna().head(10)
        return sample.astype(str).apply(
            lambda v: v.isdigit() and len(v) > 8
        ).mean() > 0.7

    def _looks_like_price(series: pd.Series) -> bool:
        sample = series.dropna().head(10)
        def is_price(v):
            try:
                f = float(v)
                return f > 0 and '.' in str(v)
            except:
                return False
        return sample.astype(str).apply(is_price).mean() > 0.7

    def _looks_like_small_int(series: pd.Series) -> bool:
        sample = series.dropna().head(10)
        def is_small_int(v):
            try:
                return float(v).is_integer() and 0 < float(v) < 1000
            except:
                return False
        return sample.astype(str).apply(is_small_int).mean() > 0.7

    def _looks_like_category(series: pd.Series) -> bool:
        sample = series.dropna().head(20)
        unique_ratio = sample.nunique() / max(len(sample), 1)
        return unique_ratio < 0.5 and sample.astype(str).apply(
            lambda v: bool(re.search(r'[a-zA-Z]', v))
        ).mean() > 0.7

    def _looks_like_boolean(series: pd.Series) -> bool:
        sample = series.dropna().head(20)
        values = set(sample.astype(str).str.lower().unique())
        return values.issubset({'0', '1', 'true', 'false', 'yes', 'no', 't', 'f', ''})

    # Detectar columnas numéricas (pandas las pone como 0, 1, 2...)
    col_names = [str(c) for c in df.columns]
    has_numeric_headers = all(c.isdigit() for c in col_names)
    if not has_numeric_headers:
        return df  # ya tiene cabecera real

    # Asignar nombres inferidos por columna
    inferred_names = {}
    used_names: set = set()

    date_assigned      = False
    order_id_assigned  = False
    customer_assigned  = False
    product_assigned   = False
    price_assigned     = False
    qty_assigned       = False
    category_assigned  = False
    session_assigned   = False
    return_assigned    = False

    for col in df.columns:
        series = df[col]
        name = None

        if _looks_like_date(series) and not date_assigned:
            name = 'order_date'
            date_assigned = True
        elif _looks_like_big_int(series):
            if not order_id_assigned:
                name = 'order_id'
                order_id_assigned = True
            elif not customer_assigned:
                name = 'user_id'
                customer_assigned = True
            elif not product_assigned:
                name = 'product_id'
                product_assigned = True
            elif not session_assigned:
                name = 'session_id'
                session_assigned = True
            else:
                name = f'id_{col}'
        elif _looks_like_price(series) and not price_assigned:
            name = 'price'
            price_assigned = True
        elif _looks_like_boolean(series) and not return_assigned:
            name = 'returned'
            return_assigned = True
        elif _looks_like_small_int(series) and not qty_assigned:
            name = 'quantity'
            qty_assigned = True
        elif _looks_like_category(series) and not category_assigned:
            name = 'category'
            category_assigned = True
        else:
            name = f'col_{col}'

        # Evitar nombres duplicados
        if name in used_names:
            name = f'{name}_{col}'
        used_names.add(name)
        inferred_names[col] = name

    df = df.rename(columns=inferred_names)
    return df

def _parse_csv(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee un CSV probando combinaciones de encoding y separador.
    Detecta automáticamente si el archivo no tiene cabecera.
    """
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        for sep in [",", ";", "\t"]:
            try:
                # Leer sin cabecera para analizar la primera fila
                df_raw = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    sep=sep,
                    dtype=str,
                    header=None,  # leer todo como datos primero
                    on_bad_lines="skip",
                    keep_default_na=False
                )

                # Eliminar filas completamente vacías
                df_raw = df_raw.dropna(how="all").reset_index(drop=True)

                if len(df_raw) == 0 or len(df_raw.columns) <= 1:
                    continue

                # Determinar si la primera fila es cabecera o datos
                first_row = df_raw.iloc[0].astype(str)
                has_header = _first_row_is_header(first_row)

                if has_header:
                    # Usar primera fila como cabecera
                    df = pd.read_csv(
                        io.BytesIO(content),
                        encoding=encoding,
                        sep=sep,
                        dtype=str,
                        on_bad_lines="skip",
                        keep_default_na=False
                    )
                    df = df.dropna(how="all").reset_index(drop=True)
                else:
                    # Sin cabecera — usar df_raw con columnas numéricas
                    df = df_raw.copy()
                    df.columns = [str(i) for i in range(len(df.columns))]
                    # Inferir nombres por contenido
                    df = _infer_header_from_content(df)

                # Limpiar columnas
                df, col_warnings = _clean_columns(df, filename)

                if len(df.columns) <= 1:
                    continue

                # Limpiar valores nulos
                df = df.replace({"": None, "nan": None, "None": None, "NaT": None})
                df = df.dropna(how="all")
                df = df.reset_index(drop=True)

                if len(df) == 0:
                    raise ValueError(
                        f"El fichero '{filename}' no contiene datos. "
                        f"Columnas encontradas: {list(df.columns)}."
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
                raise
            except Exception:
                continue

    raise ValueError(
        "No se pudo leer el CSV. "
        "Asegúrate de que el fichero es un CSV válido con columnas separadas "
        "por coma, punto y coma o tabulador, y encoding UTF-8 o Latin-1."
    )

def _first_row_is_header(first_row: pd.Series) -> bool:
    """
    Determina si la primera fila contiene nombres de columna o datos reales.
    Una fila es cabecera si:
    - Contiene texto alfabético (no solo números o fechas)
    - No contiene patrones de fecha/hora
    - No contiene IDs numéricos largos
    """
    import re
    date_pattern  = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}')
    bigint_pattern = re.compile(r'^\d{10,}$')

    text_count   = 0
    date_count   = 0
    bigint_count = 0

    for val in first_row:
        val_str = str(val).strip()
        if date_pattern.search(val_str):
            date_count += 1
        elif bigint_pattern.match(val_str):
            bigint_count += 1
        elif re.search(r'[a-zA-Z_]', val_str) and not val_str.replace('.', '').replace(',', '').isdigit():
            text_count += 1

    total = len(first_row)
    # Si más del 40% de los valores son texto alfabético → es cabecera
    # Si hay fechas o IDs largos → son datos, no cabecera
    if (date_count + bigint_count) > total * 0.3:
        return False
    return text_count > total * 0.4    
    
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