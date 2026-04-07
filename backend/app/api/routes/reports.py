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
    date_from: Optional[str] = None
    date_to:   Optional[str] = None


class ShareReportRequest(BaseModel):
    shared: bool


def _serialize(r: Report) -> dict:
    return {
        "id":               str(r.id),
        "dashboard_id":     str(r.dashboard_id) if r.dashboard_id else None,
        "dashboard_name":   r.dashboard_name,
        "date_from":        r.date_from,
        "date_to":          r.date_to,
        "insights":         r.insights,
        "kpi_snapshot":     r.kpi_snapshot,
        "charts_snapshot":  r.charts_snapshot,
        "shared_with_team": r.shared_with_team,
        "created_at":       r.created_at.isoformat(),
    }


@router.post("/", status_code=201)
def create_report(
    data: CreateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboard = db.query(Dashboard).filter_by(
        id=data.dashboard_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

    effective_from = data.date_from or (str(dashboard.date_from) if dashboard.date_from else None)
    effective_to   = data.date_to   or (str(dashboard.date_to)   if dashboard.date_to   else None)

    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period="custom" if effective_from else "all",
        date_from=effective_from,
        date_to=effective_to,
        import_ids=[str(i) for i in (dashboard.import_ids or [])],
        user_id=str(current_user.id),
    )

    insights_text = generate_insights(
        kpis=kpi_data["kpis"],
        coverage=kpi_data["data_coverage"],
        period=kpi_data["period"],
        charts=kpi_data.get("charts", {}),
    )

    report = Report(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        dashboard_id=dashboard.id,
        dashboard_name=dashboard.name,
        date_from=effective_from,
        date_to=effective_to,
        kpi_snapshot=kpi_data["kpis"],
        charts_snapshot=kpi_data.get("charts", {}),
        insights=insights_text,
        shared_with_team=False,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _serialize(report)


@router.get("/")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = (
        db.query(Report)
        .filter_by(
            tenant_id=current_user.tenant_id,
            created_by=current_user.id
        )
        .order_by(Report.created_at.desc())
        .all()
    )
    return [_serialize(r) for r in reports]


@router.get("/{report_id}")
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return _serialize(report)


@router.patch("/{report_id}/share")
def share_report(
    report_id: str,
    data: ShareReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    #is_owner = str(report.created_by) == str(current_user.id)
    #if not is_owner and current_user.role != "admin":
    #    raise HTTPException(status_code=403, detail="Solo el creador o un administrador puede compartir este informe")

    report.shared_with_team = data.shared
    db.commit()
    db.refresh(report)
    return _serialize(report)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    db.delete(report)
    db.commit()