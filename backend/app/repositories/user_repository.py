from sqlalchemy.orm import Session
from app.models.user import User
from app.models.tenant import Tenant


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Busca un usuario por email.
    Equivale a userRepository.findByEmail() en Spring Data JPA.
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id) -> User | None:
    """Busca un usuario por su UUID interno."""
    return db.query(User).filter(User.id == user_id).first()


def create_tenant_and_user(
    db: Session,
    company_name: str,
    sector: str | None,
    currency: str,
    email: str,
    hashed_password: str,
    full_name: str | None
) -> User:
    """
    Crea un Tenant y su User en una sola transacción.
    Si cualquiera falla, se hace rollback de ambos.
    Equivale a @Transactional en Spring.
    """
    # 1. Crear el tenant
    tenant = Tenant(
        name=company_name,
        sector=sector,
        currency=currency
    )
    db.add(tenant)
    db.flush()  # escribe en sesión sin commit — necesitamos tenant.id

    # 2. Crear el usuario vinculado al tenant
    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # recarga desde BD para tener todos los campos

    return user