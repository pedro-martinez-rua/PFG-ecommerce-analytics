from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.kpi_service import compute_kpis
from app.services.groq_service import generate_insights

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("/")
def get_kpis(
    period: Optional[str] = Query(default="last_30", description="last_30|last_90|ytd|last_year|all|custom"),
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    import_ids: Optional[List[str]] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period=period,
        date_from=date_from,
        date_to=date_to,
        import_ids=import_ids,
    )


@router.get("/insights")
def get_insights(
    period: Optional[str] = Query(default="last_30"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    import_ids: Optional[List[str]] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kpi_data = compute_kpis(
        db=db,
        tenant_id=str(current_user.tenant_id),
        period=period,
        date_from=date_from,
        date_to=date_to,
        import_ids=import_ids,
    )

    insights = generate_insights(
        kpis=kpi_data["kpis"],
        coverage=kpi_data["data_coverage"],
        period=kpi_data["period"],
        charts=kpi_data["charts"],
    )

    return {
        "period": kpi_data["period"],
        "date_from": kpi_data["date_from"],
        "date_to": kpi_data["date_to"],
        "import_ids": kpi_data.get("import_ids", []),
        "insights": insights,
        "data_coverage": kpi_data["data_coverage"],
    }