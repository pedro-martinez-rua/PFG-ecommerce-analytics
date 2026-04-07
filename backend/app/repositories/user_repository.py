from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.tenant import Tenant


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_users_by_tenant(db: Session, tenant_id) -> list[User]:
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.is_active == True)
        .order_by(User.created_at.asc())
        .all()
    )


def get_tenant_by_company_name(db: Session, company_name: str) -> Tenant | None:
    """Búsqueda insensible a mayúsculas por nombre de empresa."""
    return (
        db.query(Tenant)
        .filter(func.lower(Tenant.name) == company_name.strip().lower())
        .first()
    )


def tenant_has_admin(db: Session, tenant_id) -> bool:
    """Comprueba si ya existe un admin activo en el tenant."""
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.role == "admin", User.is_active == True)
        .count() > 0
    )


def create_tenant_and_user(
    db: Session,
    company_name: str,
    sector: str | None,
    currency: str,
    email: str,
    hashed_password: str,
    full_name: str | None,
) -> User:
    """Crea tenant + primer usuario admin. Siempre tiene team_access=True."""
    tenant = Tenant(name=company_name.strip(), sector=sector, currency=currency)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role="admin",
        team_access=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_analyst_user(
    db: Session,
    tenant_id,
    email: str,
    hashed_password: str,
    full_name: str | None,
) -> User:
    """Añade un analista a un tenant existente. team_access=False hasta que el admin lo apruebe."""
    user = User(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role="analyst",
        team_access=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user