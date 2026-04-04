from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.db.database import engine, Base
from app.models import *
from app.api.errors import http_exception_handler
from app.api.routes import auth, imports, kpis

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="E-Commerce Analytics API",
    version="0.1.0",
    description="Plataforma SaaS de analítica para e-commerce"
)

# CORS — permite llamadas desde el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(imports.router)
app.include_router(kpis.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}