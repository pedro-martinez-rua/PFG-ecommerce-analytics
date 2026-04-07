"""
team.py — Gestión de equipo e informes compartidos.

Flujo:
  - Admin y analistas se registran solos por /register con el mismo company_name.
  - Admin ve en /members todos los usuarios del tenant.
  - Admin activa/desactiva team_access por miembro.
  - Solo usuarios con team_access=True acceden a /api/team/reports.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.report import Report
from app.repositories.user_repository import get_users_by_tenant
from uuid import UUID

router = APIRouter(prefix="/api/team", tags=["team"])


class ToggleAccessRequest(BaseModel):
    team_access: bool


def _require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar esta acción")


def _serialize_member(u: User) -> dict:
    return {
        "id":          str(u.id),
        "email":       u.email,
        "full_name":   u.full_name,
        "role":        u.role,
        "is_active":   u.is_active,
        "team_access": u.team_access,
        "created_at":  u.created_at.isoformat(),
    }


def _serialize_report(r: Report, creator: User | None = None) -> dict:
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
        "created_by_name":  creator.full_name if creator else None,
        "created_by_email": creator.email if creator else None,
    }


# ── Miembros ──────────────────────────────────────────────────────────

@router.get("/members")
def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos los miembros activos del tenant. Solo admins."""
    _require_admin(current_user)
    members = get_users_by_tenant(db, current_user.tenant_id)
    return [_serialize_member(m) for m in members]


@router.patch("/members/{member_id}/access")
def toggle_team_access(
    member_id: str,
    data: ToggleAccessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activa o desactiva el acceso a la pantalla de Equipo para un miembro.
    Solo el admin puede hacerlo. No puede modificar su propio acceso.
    """
    _require_admin(current_user)

    if str(current_user.id) == member_id:
        raise HTTPException(status_code=400, detail="No puedes modificar tu propio acceso")

    member = db.query(User).filter_by(
        id=member_id,
        tenant_id=current_user.tenant_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    member.team_access = data.team_access
    db.commit()
    db.refresh(member)
    return _serialize_member(member)


@router.delete("/members/{member_id}", status_code=204)
def remove_member(
    member_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Desactiva un miembro del tenant (soft delete). Solo admin."""
    _require_admin(current_user)

    if str(current_user.id) == member_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    member = db.query(User).filter_by(
        id=member_id,
        tenant_id=current_user.tenant_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    member.is_active = False
    db.commit()


# ── Informes del equipo ───────────────────────────────────────────────

@router.get("/reports")
def list_team_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Informes compartidos del tenant.
    Requiere team_access=True.
    """
    if not current_user.team_access:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a la pantalla de equipo. Contacta con tu administrador."
        )

    reports = (
        db.query(Report)
        .filter_by(tenant_id=current_user.tenant_id, shared_with_team=True)
        .order_by(Report.created_at.desc())
        .all()
    )

    creator_ids = {r.created_by for r in reports if r.created_by}
    creators = {
        str(u.id): u
        for u in db.query(User).filter(User.id.in_(creator_ids)).all()
    } if creator_ids else {}

    return [_serialize_report(r, creators.get(str(r.created_by))) for r in reports]

@router.get("/reports/{report_id}")
def get_team_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.team_access:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a la pantalla de equipo. Contacta con tu administrador."
        )

    report = db.query(Report).filter_by(
        id=report_id,
        tenant_id=current_user.tenant_id,
        shared_with_team=True
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    creator = None
    if report.created_by:
        creator = db.query(User).filter_by(
            id=report.created_by,
            tenant_id=current_user.tenant_id
        ).first()

    payload = _serialize_report(report, creator)
    payload["updated_at"] = report.updated_at.isoformat() if getattr(report, "updated_at", None) else None
    return payload