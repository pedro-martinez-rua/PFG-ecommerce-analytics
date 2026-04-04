import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                              nullable=False, index=True)
    import_id        = Column(UUID(as_uuid=True), ForeignKey("imports.id"),
                              nullable=True, index=True)
    external_id      = Column(String, nullable=True, index=True)
    name             = Column(String, nullable=False)
    sku              = Column(String, nullable=True)
    category         = Column(String, nullable=True)
    brand            = Column(String, nullable=True)
    unit_cost        = Column(Numeric(12, 2), nullable=True)
    unit_price       = Column(Numeric(12, 2), nullable=True)
    extra_attributes = Column(JSONB, nullable=False, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    tenant      = relationship("Tenant")
    order_lines = relationship("OrderLine", back_populates="product")