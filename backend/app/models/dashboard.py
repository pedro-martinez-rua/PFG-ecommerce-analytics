import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base


class Dashboard(Base):
    __tablename__ = "dashboards"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id  = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"),   nullable=True,  index=True)
    name       = Column(String, nullable=False)
    date_from  = Column(Date, nullable=True)
    date_to    = Column(Date, nullable=True)
    import_ids = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())