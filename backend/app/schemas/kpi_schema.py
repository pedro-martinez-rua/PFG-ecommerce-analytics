from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class DataAvailability(str, Enum):
    REAL      = "real"
    ESTIMATED = "estimated"
    MISSING   = "missing"


class KpiValue(BaseModel):
    """Un KPI individual con su valor y metadata de disponibilidad."""
    value:        Optional[float] = None
    vs_previous:  Optional[float] = None   # valor del periodo anterior
    growth_pct:   Optional[float] = None   # % de cambio vs anterior
    availability: DataAvailability = DataAvailability.REAL
    reason:       Optional[str]   = None   # explicación si missing/estimated


class DataCoverage(BaseModel):
    """Qué datos tiene este tenant — determina qué KPIs son calculables."""
    has_cogs:       bool = False
    has_customers:  bool = False
    has_channels:   bool = False
    has_categories: bool = False
    has_returns:    bool = False
    has_discounts:  bool = False
    has_delivery:   bool = False
    has_refunds:    bool = False
    has_products:   bool = False
    order_count:    int  = 0


class ChartPoint(BaseModel):
    """Punto de dato para gráficas de línea o barras."""
    label: str
    value: float


class KpiResponse(BaseModel):
    """Response completo del endpoint de KPIs."""
    period:      str
    date_from:   str
    date_to:     str
    data_coverage: DataCoverage

    # KPI cards — métricas individuales
    kpis: dict[str, KpiValue]

    # Datos para gráficas
    charts: dict[str, Any]