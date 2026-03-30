import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class FieldMapping(Base):
    """
    Memoria del sistema de mapeo por tenant.
    
    Cuando un tenant sube un CSV con columna 'f_pedido',
    el sistema detecta que corresponde a 'order_date' y guarda
    ese mapeo aquí. La próxima vez que suba datos, el mapeo
    se aplica automáticamente sin intervención del usuario.
    
    source_column  → nombre en el CSV del cliente
    canonical_field → nombre en nuestro schema (ej: order_date)
    transformation  → regla de conversión (date_parse, to_decimal, lowercase...)
    """
    __tablename__ = "field_mappings"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                             nullable=False, index=True)
    upload_type     = Column(String, nullable=False)    # orders | customers | products
    source_column   = Column(String, nullable=False)
    canonical_field = Column(String, nullable=False)
    transformation  = Column(String, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())