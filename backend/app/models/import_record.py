import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class Import(Base):
    """
    Representa una importación completa de fichero.
    Una importación puede contener múltiples hojas (XLSX)
    o una sola (CSV). Cada hoja genera un ImportSheet.

    El ciclo de vida de un import:
    processing → completed | completed_with_errors | failed
    """
    __tablename__ = "imports"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id            = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    filename             = Column(String, nullable=False)
    file_format          = Column(String, nullable=False, default="csv")  # csv | xlsx
    file_size_bytes      = Column(Integer, nullable=True)
    status               = Column(String, nullable=False, default="processing")
    detected_type        = Column(String, nullable=True)   # orders|customers|products|mixed|unknown
    detection_confidence = Column(Float, nullable=True)
    total_rows           = Column(Integer, default=0)
    valid_rows           = Column(Integer, default=0)
    invalid_rows         = Column(Integer, default=0)
    skipped_rows         = Column(Integer, default=0)
    error_message        = Column(Text, nullable=True)     # solo si status=failed
    mapping_confirmed    = Column(Boolean, default=False)
    started_at           = Column(DateTime(timezone=True), server_default=func.now())
    completed_at         = Column(DateTime(timezone=True), nullable=True)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())