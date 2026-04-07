from sqlalchemy.orm import Session
from app.repositories.user_repository import (
    get_user_by_email,
    get_tenant_by_company_name,
    tenant_has_admin,
    create_tenant_and_user,
    create_analyst_user,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, ChangePasswordRequest
from app.models.user import User


def register_user(db: Session, data: RegisterRequest) -> User:
    """
    Flujo de registro con roles:

    Admin:
      - Si ya existe un admin para ese nombre de empresa → error.
      - Si no existe la empresa → crea tenant + usuario admin.

    Analyst:
      - Si la empresa no existe → error (debe existir primero el admin).
      - Si existe → se une al tenant como analista (team_access=False hasta aprobación).
    """
    if get_user_by_email(db, data.email):
        raise ValueError("Ya existe una cuenta con ese email")

    role = (data.role or "admin").lower()

    if role == "admin":
        existing_tenant = get_tenant_by_company_name(db, data.company_name)
        if existing_tenant and tenant_has_admin(db, existing_tenant.id):
            raise ValueError(
                "Ya existe un administrador para esta empresa. "
                "Si formas parte de este equipo, regístrate como Analista."
            )
        # Crear nuevo tenant + admin
        return create_tenant_and_user(
            db=db,
            company_name=data.company_name,
            sector=data.sector,
            currency=data.currency,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

    elif role == "analyst":
        tenant = get_tenant_by_company_name(db, data.company_name)
        if not tenant:
            raise ValueError(
                "No existe ninguna empresa con ese nombre. "
                "Verifica el nombre exacto con tu administrador."
            )
        return create_analyst_user(
            db=db,
            tenant_id=tenant.id,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

    else:
        raise ValueError("Rol inválido. Usa 'admin' o 'analyst'.")


def login_user(db: Session, data: LoginRequest) -> TokenResponse | None:
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
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