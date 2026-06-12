import uuid
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class WebSession(Base):
    __tablename__ = "web_sessions"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id         = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                               nullable=False, index=True)
    import_id         = Column(UUID(as_uuid=True), ForeignKey("imports.id"),
                               nullable=True, index=True)
    external_id       = Column(String, nullable=True, index=True)

    # Identificación de sesión
    session_date      = Column(Date, nullable=True, index=True)
    device_type       = Column(String, nullable=True)

    # UTM
    utm_source        = Column(String, nullable=True)
    utm_campaign      = Column(String, nullable=True)
    utm_medium        = Column(String, nullable=True)
    utm_content       = Column(String, nullable=True)
    utm_term          = Column(String, nullable=True)

    # Comportamiento
    landing_page      = Column(String, nullable=True)
    pageviews         = Column(Integer, nullable=True)
    is_bounce         = Column(Boolean, nullable=True)
    new_visitor       = Column(Boolean, nullable=True)
    sessions_to_order = Column(Integer, nullable=True)
    time_on_site      = Column(Integer, nullable=True)  # segundos

    # Extra
    extra_attributes  = Column(JSONB, nullable=True, default=dict)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())