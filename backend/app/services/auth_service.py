from sqlalchemy.orm import Session
from app.repositories.user_repository import (
    get_user_by_email,
    create_tenant_and_user
)
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, ChangePasswordRequest
from app.models.user import User


def register_user(db: Session, data: RegisterRequest) -> User:
    existing = get_user_by_email(db, data.email)
    if existing:
        raise ValueError("Ya existe una cuenta con ese email")

    hashed = hash_password(data.password)

    return create_tenant_and_user(
        db=db,
        company_name=data.company_name,
        sector=data.sector,
        currency=data.currency,
        email=data.email,
        hashed_password=hashed,
        full_name=data.full_name
    )


def login_user(db: Session, data: LoginRequest) -> TokenResponse | None:
    user = get_user_by_email(db, data.email)
    if not user:
        return None

    if not verify_password(data.password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id)
    })

    return TokenResponse(access_token=token)


def change_password(db: Session, user: User, data: ChangePasswordRequest) -> None:
    """
    Cambia la contraseña del usuario autenticado.
    Reglas:
    - current_password debe ser correcta
    - new_password no puede ser igual a la actual
    - confirm_password debe coincidir
    """
    if not verify_password(data.current_password, user.hashed_password):
        raise ValueError("La contraseña actual no es correcta")

    if data.current_password == data.new_password:
        raise ValueError("La nueva contraseña no puede ser igual a la actual")

    if data.new_password != data.confirm_password:
        raise ValueError("La confirmación de la nueva contraseña no coincide")

    user.hashed_password = hash_password(data.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)

def update_me(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name.strip()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user