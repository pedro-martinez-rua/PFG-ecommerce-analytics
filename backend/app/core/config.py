from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        weak_defaults = {
            "cambia_esto_por_una_clave_segura_larga_aleatoria",
            "secret",
            "mysecret",
            "changeme",
            "your-secret-key",
        }
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY debe tener al menos 32 caracteres. "
                "Genera una con: openssl rand -hex 32"
            )
        if v.lower() in weak_defaults:
            raise ValueError(
                "SECRET_KEY no puede ser el valor por defecto. "
                "Genera una con: openssl rand -hex 32"
            )
        return v


settings = Settings()