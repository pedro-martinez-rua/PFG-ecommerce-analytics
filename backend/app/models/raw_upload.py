import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class RawUpload(Base):
    """
    Staging layer. Almacena cada fila del CSV exactamente como llegó,
    antes de cualquier transformación.
    
    Por qué existe:
    - Permite reprocesar un upload si cambia la lógica de transformación.
    - Permite auditar qué datos originales llegaron al sistema.
    - Permite detectar qué filas fallaron y por qué.
    
    upload_id agrupa todas las filas del mismo fichero. Permite
    ver el estado de un upload completo o borrarlo entero.
    
    upload_type indica si el fichero contiene orders, customers,
    products, o una mezcla (mixed) — detectado automáticamente.
    """
    __tablename__ = "raw_uploads"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                           nullable=False, index=True)
    upload_id     = Column(UUID(as_uuid=True), nullable=False, index=True)
    upload_type   = Column(String, nullable=True)    # orders|customers|products|mixed|unknown
    filename      = Column(String, nullable=True)
    row_index     = Column(Integer, nullable=True)
    raw_data      = Column(JSONB, nullable=False)    # fila original completa
    status        = Column(String, nullable=False, default="pending")  # pending|processed|error
    error_message = Column(Text, nullable=True)
    processed_at  = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())