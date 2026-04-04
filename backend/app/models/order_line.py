import uuid
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class OrderLine(Base):
    __tablename__ = "order_lines"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                              nullable=False, index=True)
    import_id        = Column(UUID(as_uuid=True), ForeignKey("imports.id"),
                              nullable=True, index=True)
    order_id         = Column(UUID(as_uuid=True), ForeignKey("orders.id"),
                              nullable=True)
    product_id       = Column(UUID(as_uuid=True), ForeignKey("products.id"),
                              nullable=True)
    external_id      = Column(String, nullable=True)
    product_name     = Column(String, nullable=True)
    sku              = Column(String, nullable=True)
    category         = Column(String, nullable=True)
    brand            = Column(String, nullable=True)
    quantity         = Column(Numeric(10, 2), nullable=True)
    unit_price       = Column(Numeric(12, 2), nullable=True)
    unit_cost        = Column(Numeric(12, 2), nullable=True)
    line_total       = Column(Numeric(12, 2), nullable=True)
    discount_amount  = Column(Numeric(12, 2), nullable=True)
    refund_amount    = Column(Numeric(12, 2), nullable=True)
    is_primary_item  = Column(Boolean, nullable=True)
    is_refunded      = Column(Boolean, nullable=False, default=False)
    extra_attributes = Column(JSONB, nullable=False, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    tenant  = relationship("Tenant")
    order   = relationship("Order",   back_populates="lines")
    product = relationship("Product", back_populates="order_lines")