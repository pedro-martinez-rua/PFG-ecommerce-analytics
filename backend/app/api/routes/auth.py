from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address


from app.db.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    UpdateMeRequest  
)
from app.services.auth_service import register_user, login_user, change_password, update_me
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
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al registrar")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
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


@router.put("/me/password")
@limiter.limit("5/minute")
def update_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        change_password(db, current_user, data)
        return {"message": "Contraseña actualizada correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo actualizar la contraseña")
    
@router.put("/me", response_model=UserResponse)
def update_me_endpoint(
    data: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated_user = update_me(db, current_user, data.full_name)

        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter_by(id=updated_user.tenant_id).first()

        return {
            "id": updated_user.id,
            "tenant_id": updated_user.tenant_id,
            "email": updated_user.email,
            "full_name": updated_user.full_name,
            "is_active": updated_user.is_active,
            "role": updated_user.role,
            "company_name": tenant.name if tenant else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))