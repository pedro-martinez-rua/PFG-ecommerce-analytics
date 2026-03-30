from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Conexión a PostgreSQL
    DATABASE_URL: str

    # JWT — clave secreta para firmar los tokens
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq — proveedor de IA para insights
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"  # lee las variables del fichero .env

settings = Settings()