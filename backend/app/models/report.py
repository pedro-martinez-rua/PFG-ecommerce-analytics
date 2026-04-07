import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class Report(Base):
    __tablename__ = "reports"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    created_by       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dashboard_id     = Column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=True)
    dashboard_name   = Column(String, nullable=False)
    date_from        = Column(String, nullable=True)
    date_to          = Column(String, nullable=True)
    kpi_snapshot     = Column(JSONB, nullable=True)
    charts_snapshot  = Column(JSONB, nullable=True)   # charts del dashboard
    insights         = Column(Text, nullable=True)
    shared_with_team = Column(Boolean, nullable=False, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())