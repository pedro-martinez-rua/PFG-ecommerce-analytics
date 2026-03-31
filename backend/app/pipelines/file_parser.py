"""
file_parser.py — Primera capa del pipeline.

Responsabilidad única: leer el fichero (CSV o XLSX) y devolver
una lista de ParsedSheet. No detecta tipos, no mapea, no transforma.
Solo lee y devuelve DataFrames limpios con metadatos.

El fichero nunca se escribe en disco — trabaja siempre en memoria (bytes).
Esto garantiza que los datos del usuario no salen del servidor.
"""
import io
from dataclasses import dataclass
import pandas as pd


@dataclass
class ParsedSheet:
    """
    Resultado de parsear una hoja de un fichero.
    Una hoja = un DataFrame + metadatos de origen.
    """
    sheet_name: str          # nombre de la hoja o nombre del CSV
    dataframe: pd.DataFrame  # datos en bruto, todo como string
    source_format: str       # 'csv' o 'xlsx'
    row_count: int
    column_count: int
    columns: list[str]


def parse_file(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Detecta el formato por extensión y delega al parser correcto.
    Siempre devuelve una lista de ParsedSheet.
    Para CSV: lista de 1 elemento.
    Para XLSX: un elemento por hoja procesable.

    Lanza ValueError si el fichero no se puede leer en absoluto.
    """
    filename_lower = filename.lower().strip()

    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return _parse_xlsx(content, filename)
    elif filename_lower.endswith(".csv"):
        return _parse_csv(content, filename)
    else:
        raise ValueError(
            f"Formato no soportado: '{filename}'. "
            f"Se aceptan ficheros .csv y .xlsx"
        )


def _parse_csv(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee un CSV probando combinaciones de encoding y separador.
    Devuelve lista con un único ParsedSheet.

    Encodings probados: utf-8, utf-8-sig (BOM), latin-1, cp1252
    Separadores probados: coma, punto y coma, tabulador
    """
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    sep=sep,
                    dtype=str,            # todo como string — el transformer convierte
                    on_bad_lines="skip",  # salta filas malformadas sin abortar
                    keep_default_na=False # no convertir "" a NaN automáticamente
                )
                # Limpiar nombres de columna
                df.columns = [str(c).strip() for c in df.columns]

                # Una columna → probablemente separador incorrecto, seguir probando
                if len(df.columns) <= 1:
                    continue

                # Eliminar filas completamente vacías
                df = df.replace("", None)
                df = df.dropna(how="all")
                df = df.reset_index(drop=True)

                return [ParsedSheet(
                    sheet_name=filename,
                    dataframe=df,
                    source_format="csv",
                    row_count=len(df),
                    column_count=len(df.columns),
                    columns=list(df.columns)
                )]
            except Exception:
                continue

    raise ValueError(
        "No se pudo leer el CSV. "
        "Asegúrate de que el fichero es un CSV válido con columnas separadas por coma, punto y coma o tabulador."
    )


def _parse_xlsx(content: bytes, filename: str) -> list[ParsedSheet]:
    """
    Lee todas las hojas de un XLSX.
    Filtra hojas vacías o con menos de 2 columnas.
    Si ninguna hoja es procesable, lanza ValueError.
    """
    try:
        xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    except Exception as e:
        raise ValueError(f"No se pudo abrir el fichero Excel: {str(e)}")

    sheets = []
    for sheet_name in xl.sheet_names:
        try:
            df = xl.parse(
                sheet_name,
                dtype=str,
                keep_default_na=False
            )

            # Limpiar nombres de columna
            df.columns = [str(c).strip() for c in df.columns]

            # Filtrar hojas vacías o con contenido insuficiente
            df = df.replace("", None)
            df = df.dropna(how="all")
            df = df.reset_index(drop=True)

            if len(df.columns) < 2 or len(df) == 0:
                continue  # hoja vacía — ignorar silenciosamente

            sheets.append(ParsedSheet(
                sheet_name=sheet_name,
                dataframe=df,
                source_format="xlsx",
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns)
            ))
        except Exception:
            continue  # hoja con error de formato — ignorar y continuar

    if not sheets:
        raise ValueError(
            "El fichero Excel no contiene hojas con datos válidos. "
            "Asegúrate de que al menos una hoja tiene cabeceras y datos."
        )

    return sheets