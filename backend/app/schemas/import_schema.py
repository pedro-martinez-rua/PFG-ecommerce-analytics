from pydantic import BaseModel, Field
from typing import List, Optional, Any


class IssueSummary(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    suggestion: Optional[str] = None
    count: int = 0
    error: Optional[str] = None
    warning: Optional[str] = None


class SheetResult(BaseModel):
    sheet_name: str
    detected_type: str
    detection_confidence: float
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    top_errors: List[dict[str, Any]] = Field(default_factory=list)
    top_warnings: List[dict[str, Any]] = Field(default_factory=list)
    note: Optional[str] = None
    columns_found: Optional[List[str]] = None
    diagnosis: Optional[str] = None
    file_warnings: Optional[List[str]] = None
    main_reason_code: Optional[str] = None
    main_reason: Optional[str] = None
    user_message: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    user_explanations: List[dict[str, Any]] = Field(default_factory=list)


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
    relations_resolved: Optional[dict] = None
    main_reason_code: Optional[str] = None
    main_reason: Optional[str] = None
    user_message: Optional[str] = None
    top_errors: List[dict[str, Any]] = Field(default_factory=list)
    top_warnings: List[dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
