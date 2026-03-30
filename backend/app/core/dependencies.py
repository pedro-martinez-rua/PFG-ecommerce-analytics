from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import get_user_by_id
from app.models.user import User

# HTTPBearer extrae el token del header "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia que protege los endpoints.
    Equivale a @PreAuthorize de Spring Security.

    Uso:
        @router.get("/orders")
        def get_orders(current_user: User = Depends(get_current_user)):
            # current_user.tenant_id disponible aquí

    Si el token es inválido devuelve 401 automáticamente.
    El tenant_id viene del JWT — el usuario no puede falsificarlo.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decodificar el JWT
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # 2. Extraer user_id del payload
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 3. Verificar que el usuario existe y está activo
    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user