from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
import re


class RegisterRequest(BaseModel):
    company_name: str
    sector: str | None = None
    currency: str = "EUR"
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "admin"       # "admin" | "analyst"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    is_active: bool
    role: str = "admin"
    team_access: bool = False
    company_name: str | None = None

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("La nueva contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", value):
            raise ValueError("La nueva contraseña debe incluir al menos una mayúscula")
        if not re.search(r"[a-z]", value):
            raise ValueError("La nueva contraseña debe incluir al menos una minúscula")
        if not re.search(r"\d", value):
            raise ValueError("La nueva contraseña debe incluir al menos un número")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Debes confirmar la nueva contraseña")
        return value

class UpdateMeRequest(BaseModel):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("El nombre completo debe tener al menos 2 caracteres")
        if len(value) > 120:
            raise ValueError("El nombre completo es demasiado largo")
        return value