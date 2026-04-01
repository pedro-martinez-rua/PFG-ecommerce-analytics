from sqlalchemy.orm import Session
from app.repositories.user_repository import (
    get_user_by_email,
    create_tenant_and_user
)
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.models.user import User


def register_user(db: Session, data: RegisterRequest) -> User:
    """
    Registra una nueva empresa y su usuario.
    Lanza ValueError si el email ya existe.
    """
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
    """
    Valida credenciales y devuelve un JWT.
    Devuelve None si las credenciales son incorrectas.
    NO lanza HTTPException — eso es responsabilidad del router.
    """
    # 1. Buscar usuario
    user = get_user_by_email(db, data.email)
    if not user:
        return None

    # 2. Verificar contraseña
    if not verify_password(data.password, user.hashed_password):
        return None

    # 3. Verificar cuenta activa
    if not user.is_active:
        return None

    # 4. Generar JWT
    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id)
    })

    return TokenResponse(access_token=token)