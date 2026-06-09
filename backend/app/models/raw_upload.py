import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class RawUpload(Base):
    __tablename__ = "raw_uploads"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    upload_id         = Column(UUID(as_uuid=True), nullable=False)
    import_id         = Column(UUID(as_uuid=True), ForeignKey("imports.id"), nullable=True)
    sheet_id          = Column(UUID(as_uuid=True), ForeignKey("import_sheets.id"), nullable=True)
    upload_type       = Column(String, nullable=True)
    filename          = Column(String, nullable=True)
    row_index         = Column(Integer, nullable=True)
    raw_data          = Column(JSONB, nullable=False)
    mapped_data       = Column(JSONB, nullable=False, default=dict)
    transformed_data  = Column(JSONB, nullable=False, default=dict)
    validation_errors = Column(JSONB, nullable=False, default=list)
    status            = Column(String, nullable=False, default="pending")
    error_message     = Column(Text, nullable=True)
    skip_reason       = Column(Text, nullable=True)
    processed_at      = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_raw_uploads_lookup",
            "tenant_id", "import_id", "sheet_id", "row_index",
        ),
    )