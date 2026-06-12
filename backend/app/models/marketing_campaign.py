import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id            = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                                  nullable=False, index=True)
    import_id            = Column(UUID(as_uuid=True), ForeignKey("imports.id"),
                                  nullable=True, index=True)
    external_id          = Column(String, nullable=True, index=True)

    # Identificación
    campaign_name        = Column(String, nullable=True, index=True)
    campaign_id          = Column(String, nullable=True)
    campaign_date        = Column(Date, nullable=True, index=True)

    # UTM
    utm_source           = Column(String, nullable=True)
    utm_medium           = Column(String, nullable=True)
    utm_content          = Column(String, nullable=True)
    utm_term             = Column(String, nullable=True)

    # Métricas de alcance
    impressions          = Column(Integer, nullable=True)
    clicks               = Column(Integer, nullable=True)
    ctr                  = Column(Numeric(8, 4), nullable=True)
    reach                = Column(Integer, nullable=True)

    # Métricas de coste
    ad_spend             = Column(Numeric(12, 2), nullable=True)
    cost_per_click       = Column(Numeric(10, 4), nullable=True)
    cost_per_conversion  = Column(Numeric(10, 4), nullable=True)

    # Métricas de resultado
    conversions          = Column(Integer, nullable=True)
    roas                 = Column(Numeric(10, 4), nullable=True)
    revenue              = Column(Numeric(12, 2), nullable=True)

    # Extra
    extra_attributes     = Column(JSONB, nullable=True, default=dict)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())