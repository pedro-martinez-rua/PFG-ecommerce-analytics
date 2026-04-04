from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.kpi_service import compute_kpis
from app.services.groq_service import generate_insights

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("/")
def get_kpis(
    period:    Optional[str] = Query(default="last_30",
                                     description="last_30|last_90|ytd|last_year|all|custom"),
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to:   Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    """
    KPIs + datos para gráficas del periodo seleccionado.
    Analiza todos los datos del tenant de forma acumulada.
    Cada KPI incluye availability: real | estimated | missing.
    """
    return compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period=period,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/insights")
def get_insights(
    period:    Optional[str] = Query(default="last_30"),
    date_from: Optional[str] = Query(default=None),
    date_to:   Optional[str] = Query(default=None),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    """
    Análisis en lenguaje natural generado por Groq.
    Solo recibe métricas agregadas — nunca datos personales.
    """
    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period=period,
        date_from=date_from,
        date_to=date_to
    )

    insights = generate_insights(
        kpis=kpi_data["kpis"],
        coverage=kpi_data["data_coverage"],
        period=kpi_data["period"]
    )

    return {
        "period":        kpi_data["period"],
        "date_from":     kpi_data["date_from"],
        "date_to":       kpi_data["date_to"],
        "insights":      insights,
        "data_coverage": kpi_data["data_coverage"]
    }