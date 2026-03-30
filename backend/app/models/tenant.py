import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Tenant(Base):
    """
    Representa una empresa registrada en la plataforma.
    Es la raíz de la jerarquía multi-tenant: todos los datos
    de negocio están vinculados a un tenant a través de tenant_id.
    """
    __tablename__ = "tenants"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String, nullable=False)
    sector     = Column(String, nullable=True)   # contexto para los insights de IA
    currency   = Column(String(3), nullable=False, default="EUR")
    is_active  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones — equivale a @OneToMany de JPA
    users     = relationship("User",         back_populates="tenant")
    orders    = relationship("Order",        back_populates="tenant")
    customers = relationship("Customer",     back_populates="tenant")
    products  = relationship("Product",      back_populates="tenant")