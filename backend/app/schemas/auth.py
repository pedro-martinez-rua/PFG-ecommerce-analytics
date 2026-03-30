from pydantic import BaseModel, EmailStr
from uuid import UUID


class RegisterRequest(BaseModel):
    """
    Datos para registrar una nueva empresa.
    Crea simultáneamente un Tenant y un User.
    """
    company_name: str
    sector: str | None = None
    currency: str = "EUR"
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    """
    Credenciales de acceso.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Respuesta al login. El frontend guarda este token
    y lo envía en el header Authorization de cada request.
    """
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Datos del usuario autenticado. Nunca incluye la contraseña.
    """
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    is_active: bool

    class Config:
        from_attributes = True