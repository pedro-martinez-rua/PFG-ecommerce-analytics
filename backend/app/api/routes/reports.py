from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.report import Report
from app.models.dashboard import Dashboard
from app.services.kpi_service import compute_kpis
from app.services.groq_service import generate_insights

router = APIRouter(prefix="/api/reports", tags=["reports"])


class CreateReportRequest(BaseModel):
    dashboard_id: str
    # Fechas opcionales: si se pasan, sobreescriben las del dashboard guardado.
    # Permite guardar informes de rangos filtrados distintos al rango original.
    date_from: Optional[str] = None
    date_to:   Optional[str] = None


@router.post("/", status_code=201)
def create_report(
    data: CreateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera un snapshot del dashboard con KPIs e insights de Groq.
    Si se pasan date_from/date_to, se usan en lugar de las fechas del dashboard.
    """
    dashboard = db.query(Dashboard).filter_by(
        id=data.dashboard_id,
        tenant_id=current_user.tenant_id
    ).first()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

    # Prioridad: fechas del request > fechas del dashboard > all
    effective_from = data.date_from or (str(dashboard.date_from) if dashboard.date_from else None)
    effective_to   = data.date_to   or (str(dashboard.date_to)   if dashboard.date_to   else None)

    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period="custom" if effective_from else "all",
        date_from=effective_from,
        date_to=effective_to,
    )

    insights_text = generate_insights(
        kpis=kpi_data["kpis"],
        coverage=kpi_data["data_coverage"],
        period=kpi_data["period"],
        charts=kpi_data.get("charts", {}),
    )

    report = Report(
        tenant_id=current_user.tenant_id,
        dashboard_id=dashboard.id,
        dashboard_name=dashboard.name,
        date_from=effective_from,
        date_to=effective_to,
        kpi_snapshot=kpi_data["kpis"],
        insights=insights_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "id":             str(report.id),
        "dashboard_id":   str(report.dashboard_id),
        "dashboard_name": report.dashboard_name,
        "date_from":      report.date_from,
        "date_to":        report.date_to,
        "insights":       report.insights,
        "kpi_snapshot":   report.kpi_snapshot,
        "created_at":     report.created_at.isoformat(),
    }


@router.get("/")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = (
        db.query(Report)
        .filter_by(tenant_id=current_user.tenant_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [
        {
            "id":             str(r.id),
            "dashboard_id":   str(r.dashboard_id) if r.dashboard_id else None,
            "dashboard_name": r.dashboard_name,
            "date_from":      r.date_from,
            "date_to":        r.date_to,
            "insights":       r.insights,
            "kpi_snapshot":   r.kpi_snapshot,
            "created_at":     r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return {
        "id":             str(report.id),
        "dashboard_id":   str(report.dashboard_id) if report.dashboard_id else None,
        "dashboard_name": report.dashboard_name,
        "date_from":      report.date_from,
        "date_to":        report.date_to,
        "insights":       report.insights,
        "kpi_snapshot":   report.kpi_snapshot,
        "created_at":     report.created_at.isoformat(),
    }


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    db.delete(report)
    db.commit()