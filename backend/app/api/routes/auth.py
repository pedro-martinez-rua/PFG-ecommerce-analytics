from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user
from app.core.dependencies import get_current_user
from app.models.user import User

router  = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra una nueva empresa y su usuario administrador.
    Crea tenant + user en una sola operación atómica.
    Rate limit: 5 registros por minuto por IP.
    """
    try:
        user = register_user(db, data)
        return {
            "message": "Empresa registrada correctamente",
            "tenant_id": str(user.tenant_id),
            "user_id":   str(user.id),
            "email":     user.email,
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al registrar")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario y devuelve un JWT.
    Rate limit: 10 intentos por minuto por IP — protección contra fuerza bruta.
    """
    token = login_user(db, data)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas"
        )
    return token

@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter_by(id=current_user.tenant_id).first()
    return {
        "id":           current_user.id,
        "tenant_id":    current_user.tenant_id,
        "email":        current_user.email,
        "full_name":    current_user.full_name,
        "is_active":    current_user.is_active,
        "role":         current_user.role,
        "company_name": tenant.name if tenant else None
    }