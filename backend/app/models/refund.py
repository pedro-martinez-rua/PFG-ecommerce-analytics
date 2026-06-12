import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id            = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                                  nullable=False, index=True)
    import_id            = Column(UUID(as_uuid=True), ForeignKey("imports.id"),
                                  nullable=True, index=True)
    external_id          = Column(String, nullable=True, index=True)

    # Relaciones
    order_external_id    = Column(String, nullable=True, index=True)
    order_item_external_id = Column(String, nullable=True)

    # Importes
    refund_amount        = Column(Numeric(12, 2), nullable=True)
    refund_amount_usd    = Column(Numeric(12, 2), nullable=True)

    # Fechas
    refund_date          = Column(Date, nullable=True)
    return_date          = Column(Date, nullable=True)

    # Motivo
    refund_reason        = Column(String, nullable=True)
    return_reason        = Column(String, nullable=True)

    # Extra
    extra_attributes     = Column(JSONB, nullable=True, default=dict)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())