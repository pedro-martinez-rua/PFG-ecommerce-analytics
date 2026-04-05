from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.dashboard import Dashboard
from app.services.kpi_service import compute_kpis
from app.services.groq_service import generate_insights

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])


class CreateDashboardRequest(BaseModel):
    name:       str
    date_from:  Optional[str] = None
    date_to:    Optional[str] = None
    import_ids: List[str] = []


@router.post("/", status_code=201)
def create_dashboard(
    data: CreateDashboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboard = Dashboard(
        tenant_id=current_user.tenant_id,
        name=data.name,
        date_from=data.date_from,
        date_to=data.date_to,
        import_ids=data.import_ids,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return _serialize(dashboard)


@router.get("/")
def list_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboards = (
        db.query(Dashboard)
        .filter_by(tenant_id=current_user.tenant_id)
        .order_by(Dashboard.created_at.desc())
        .all()
    )
    return [_serialize(d) for d in dashboards]


@router.get("/{dashboard_id}")
def get_dashboard(
    dashboard_id: str,
    # Fechas opcionales para filtrar sin modificar el dashboard guardado
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to:   Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboard = db.query(Dashboard).filter_by(
        id=dashboard_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

    # Prioridad: query params > fechas del dashboard > all
    effective_from = date_from or (str(dashboard.date_from) if dashboard.date_from else None)
    effective_to   = date_to   or (str(dashboard.date_to)   if dashboard.date_to   else None)

    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period="custom" if effective_from else "all",
        date_from=effective_from,
        date_to=effective_to,
        import_ids=[str(i) for i in (dashboard.import_ids or [])],
    )
    return {**_serialize(dashboard), **kpi_data}


@router.get("/{dashboard_id}/insights")
def get_dashboard_insights(
    dashboard_id: str,
    # Mismos query params opcionales para coherencia con get_dashboard
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to:   Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboard = db.query(Dashboard).filter_by(
        id=dashboard_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

    effective_from = date_from or (str(dashboard.date_from) if dashboard.date_from else None)
    effective_to   = date_to   or (str(dashboard.date_to)   if dashboard.date_to   else None)

    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period="custom" if effective_from else "all",
        date_from=effective_from,
        date_to=effective_to,
        import_ids=[str(i) for i in (dashboard.import_ids or [])],
    )

    insights = generate_insights(
        kpis=kpi_data["kpis"],
        coverage=kpi_data["data_coverage"],
        period=kpi_data["period"],
        charts=kpi_data["charts"],
    )

    return {
        "dashboard_id": dashboard_id,
        "period":       kpi_data["period"],
        "date_from":    kpi_data["date_from"],
        "date_to":      kpi_data["date_to"],
        "import_ids":   kpi_data.get("import_ids", []),
        "insights":     insights,
        "data_coverage": kpi_data["data_coverage"],
    }


@router.delete("/{dashboard_id}", status_code=204)
def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dashboard = db.query(Dashboard).filter_by(
        id=dashboard_id,
        tenant_id=current_user.tenant_id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")

    db.execute(text("""
        UPDATE reports SET dashboard_id = NULL
        WHERE dashboard_id = :did
    """), {"did": dashboard_id})

    db.execute(text("""
        DELETE FROM dashboards WHERE id = :id AND tenant_id = :tid
    """), {"id": dashboard_id, "tid": str(current_user.tenant_id)})

    db.commit()


def _serialize(d: Dashboard) -> dict:
    return {
        "id":         str(d.id),
        "name":       d.name,
        "date_from":  str(d.date_from) if d.date_from else None,
        "date_to":    str(d.date_to)   if d.date_to   else None,
        "import_ids": d.import_ids or [],
        "created_at": d.created_at.isoformat(),
    }