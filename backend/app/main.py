from fastapi import FastAPI, HTTPException
from app.db.database import engine, Base
from app.models import *
from app.api.routes import auth
from app.api.errors import http_exception_handler

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Commerce Analytics API",
    version="0.1.0",
    description="Plataforma SaaS de analítica para e-commerce"
)

# Manejador global de errores
app.add_exception_handler(HTTPException, http_exception_handler)

# Registrar routers
app.include_router(auth.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}