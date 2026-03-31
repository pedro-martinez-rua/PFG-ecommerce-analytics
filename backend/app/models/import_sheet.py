import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class ImportSheet(Base):
    """
    Representa una hoja dentro de una importación.
    Para CSV: siempre hay exactamente un ImportSheet por Import.
    Para XLSX: hay un ImportSheet por cada hoja procesable.
    """
    __tablename__ = "import_sheets"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id            = Column(UUID(as_uuid=True), ForeignKey("imports.id"), nullable=False, index=True)
    tenant_id            = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    sheet_name           = Column(String, nullable=False)
    detected_type        = Column(String, nullable=True)
    detection_confidence = Column(Float, nullable=True)
    total_rows           = Column(Integer, default=0)
    valid_rows           = Column(Integer, default=0)
    invalid_rows         = Column(Integer, default=0)
    skipped_rows         = Column(Integer, default=0)
    status               = Column(String, default="pending")  # pending|processing|completed|failed
    created_at           = Column(DateTime(timezone=True), server_default=func.now())
