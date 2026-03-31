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
def me(current_user: User = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado.
    Endpoint protegido — requiere JWT válido.
    """
    return current_user