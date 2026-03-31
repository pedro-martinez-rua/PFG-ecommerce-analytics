from pydantic import BaseModel
from typing import List, Optional


class SheetResult(BaseModel):
    sheet_name: str
    detected_type: str
    detection_confidence: float
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    top_errors: List[dict] = []
    note: Optional[str] = None


class ImportResponse(BaseModel):
    import_id: str
    filename: str
    file_format: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    sheets_processed: int
    sheets: List[SheetResult]
    detected_type: str
    detection_confidence: float
    error: Optional[str] = None