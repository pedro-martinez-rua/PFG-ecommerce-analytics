import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class KpiSnapshot(Base):
    """
    KPIs precalculados por tenant y período.
    El dashboard lee de esta tabla — no recalcula en cada carga.
    
    kpi_name identifica el KPI: total_revenue, order_count,
    avg_order_value, top_products_revenue, etc.
    
    kpi_value almacena el valor numérico principal.
    Para KPIs que son listas (top productos, ventas por país),
    kpi_value puede ser el total y kpi_metadata contiene el desglose:
    {"items": [{"name": "Producto A", "value": 1200}, ...]}
    """
    __tablename__ = "kpi_snapshots"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id     = Column(UUID(as_uuid=True), ForeignKey("tenants.id"),
                           nullable=False, index=True)
    period_start  = Column(Date, nullable=True)
    period_end    = Column(Date, nullable=True)
    kpi_name      = Column(String, nullable=False)
    kpi_value     = Column(Numeric, nullable=True)
    kpi_metadata  = Column(JSONB, nullable=False, default=dict)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())