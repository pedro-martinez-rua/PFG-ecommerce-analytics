from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.db.database import engine, Base
from app.models import *
from app.api.errors import http_exception_handler
from app.api.routes import auth, imports

Base.metadata.create_all(bind=engine)

# Rate limiter global — identifica clientes por IP
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="E-Commerce Analytics API",
    version="0.1.0",
    description="Plataforma SaaS de analítica para e-commerce"
)

# Registrar el limiter en el estado de la app
app.state.limiter = limiter

# Handlers de errores
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(auth.router)
app.include_router(imports.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}