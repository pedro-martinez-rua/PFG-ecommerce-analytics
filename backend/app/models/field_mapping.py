import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    upload_type     = Column(String, nullable=False)
    source_column   = Column(String, nullable=False)
    canonical_field = Column(String, nullable=False)
    transformation  = Column(String, nullable=True)
    confidence      = Column(Float, nullable=True, default=1.0)
    is_confirmed    = Column(Boolean, nullable=False, default=False)
    confirmed_at    = Column(DateTime(timezone=True), nullable=True)
    import_id       = Column(UUID(as_uuid=True), ForeignKey("imports.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())