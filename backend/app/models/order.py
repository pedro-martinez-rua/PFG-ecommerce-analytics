import uuid
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Order(Base):
    """
    Núcleo del sistema. Representa una transacción completa.
    Todos los KPIs financieros y temporales se calculan desde esta tabla.
    
    Índices en tenant_id y order_date porque todos los KPIs
    filtran por tenant y agrupan por fecha — sin índices
    cada cálculo haría un full scan de la tabla completa.
    
    Los campos de marketing (utm_source, utm_campaign, device_type)
    provienen del dataset Maven y son opcionales para el resto.
    """
    __tablename__ = "orders"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                              nullable=False, index=True)
    customer_id      = Column(UUID(as_uuid=True), ForeignKey("customers.id"),
                              nullable=True)
    external_id      = Column(String, nullable=True, index=True)

    # Campos temporales — obligatorios para cualquier KPI temporal
    order_date       = Column(Date, nullable=False, index=True)

    # Campos financieros
    total_amount     = Column(Numeric(12, 2), nullable=True)   # bruto antes de descuento
    discount_amount  = Column(Numeric(12, 2), nullable=True)
    net_amount       = Column(Numeric(12, 2), nullable=True)   # total_amount - discount_amount
    shipping_cost    = Column(Numeric(12, 2), nullable=True)
    refund_amount    = Column(Numeric(12, 2), nullable=True)
    cogs_amount      = Column(Numeric(12, 2), nullable=True)   # coste del pedido (COGS)

    # Campos operativos
    currency         = Column(String(3), nullable=True)
    channel          = Column(String, nullable=True)
    status           = Column(String, nullable=True)
    payment_method   = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)
    shipping_region  = Column(String, nullable=True)
    delivery_days    = Column(Integer, nullable=True)
    is_returned      = Column(Boolean, nullable=False, default=False)

    # Campos de marketing (Maven dataset)
    device_type      = Column(String, nullable=True)
    utm_source       = Column(String, nullable=True)
    utm_campaign     = Column(String, nullable=True)
    session_id       = Column(String, nullable=True)

    extra_attributes = Column(JSONB, nullable=False, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    tenant   = relationship("Tenant",    back_populates="orders")
    customer = relationship("Customer",  back_populates="orders")
    lines    = relationship("OrderLine", back_populates="order")