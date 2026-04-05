from pydantic import BaseModel, Field
from typing import Optional, List


class MappingSuggestionItem(BaseModel):
    source_column: str
    canonical_field: Optional[str] = None
    confidence: float = 0.0
    method: str = "unresolved"
    inferred_type: Optional[str] = None
    null_ratio: Optional[float] = None


class MappingSuggestionResponse(BaseModel):
    import_id: str
    sheet_name: str
    upload_type: str
    confidence: float
    requires_review: bool
    required_fields_missing: List[str] = Field(default_factory=list)
    suggestions: List[MappingSuggestionItem] = Field(default_factory=list)
    raw_columns: List[str] = Field(default_factory=list)
    profiler_warnings: List[str] = Field(default_factory=list)


class MappingAssignment(BaseModel):
    source_column: str
    canonical_field: Optional[str] = None


class MappingApplyRequest(BaseModel):
    sheet_name: Optional[str] = None
    upload_type: Optional[str] = None
    assignments: List[MappingAssignment] = Field(default_factory=list)


class MappingApplyResponse(BaseModel):
    import_id: str
    sheet_name: str
    status: str
    valid_rows: int
    invalid_rows: int
    skipped_rows: int
    detected_type: str
