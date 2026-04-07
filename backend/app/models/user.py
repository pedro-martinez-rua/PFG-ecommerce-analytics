import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email           = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String, nullable=True)
    role            = Column(String, default="admin", nullable=False)   # "admin" | "analyst"
    is_active       = Column(Boolean, nullable=False, default=True)
    team_access     = Column(Boolean, nullable=False, default=False)    # admin aprueba el acceso al equipo
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")