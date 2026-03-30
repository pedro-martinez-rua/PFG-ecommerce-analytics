from pydantic import BaseModel
from typing import List


class UploadResponse(BaseModel):
    """Respuesta del endpoint de upload de CSV."""
    upload_id: str
    upload_type: str
    total_rows: int
    processed: int
    errors: int
    error_details: List[str] = []