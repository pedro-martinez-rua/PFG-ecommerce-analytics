import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Customer(Base):
    """
    Representa un comprador del tenant. Es opcional: algunos datasets
    no tienen datos de cliente más allá de un ID externo.
    Los campos total_orders, total_spent y avg_order_value son
    desnormalizados — se calculan y actualizan en cada ingesta
    para evitar recalcularlos en cada consulta de KPIs.
    """
    __tablename__ = "customers"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                              nullable=False, index=True)
    external_id      = Column(String, nullable=True, index=True)  # ID en el sistema origen
    email            = Column(String, nullable=True, index=True)
    full_name        = Column(String, nullable=True)
    country          = Column(String, nullable=True)
    region           = Column(String, nullable=True)
    first_seen_at    = Column(Date, nullable=True)     # calculado del primer pedido
    last_order_at    = Column(Date, nullable=True)     # calculado del último pedido
    total_orders     = Column(Integer, nullable=False, default=0)
    total_spent      = Column(Numeric(12, 2), nullable=False, default=0)
    avg_order_value  = Column(Numeric(12, 2), nullable=True)
    customer_rating  = Column(Numeric(3, 2), nullable=True)  # presente en ecommerce_sales
    extra_attributes = Column(JSONB, nullable=False, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="customers")
    orders = relationship("Order",  back_populates="customer")