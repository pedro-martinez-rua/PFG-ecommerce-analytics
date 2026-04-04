import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class KpiSnapshot(Base):
    """
    Caché de KPIs calculados por tenant y periodo.
    Evita recalcular en cada request — se invalida tras una nueva ingesta
    o cuando el snapshot tiene más de 1 hora.

    Cada fila representa un KPI individual para un periodo concreto.
    Las series temporales para gráficas van en metadata (JSONB).
    """
    __tablename__ = "kpi_snapshots"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id      = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                            nullable=False, index=True)
    period_label   = Column(String, nullable=False, index=True)  # last_30|last_90|ytd|custom
    period_start   = Column(Date, nullable=True)
    period_end     = Column(Date, nullable=True)
    metric_name    = Column(String, nullable=False)              # revenue|order_count|etc
    value          = Column(Numeric(20, 4), nullable=True)       # valor numérico principal
    availability   = Column(String, nullable=False, default="real")  # real|estimated|missing
    kpi_metadata       = Column(JSONB, nullable=False, default=dict) # series para gráficas
    compared_to    = Column(JSONB, nullable=False, default=dict) # valor periodo anterior
    computed_at    = Column(DateTime(timezone=True), server_default=func.now())
    created_at     = Column(DateTime(timezone=True), server_default=func.now())