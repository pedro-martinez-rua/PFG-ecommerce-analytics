from fastapi import FastAPI
from app.db.database import engine, Base
from app.models import *  # registra todos los modelos antes del create_all

# create_all crea las tablas en PostgreSQL si no existen.
# Equivale a que Spring/Hibernate genere el DDL automáticamente.
# No modifica tablas que ya existen — es seguro ejecutarlo cada arranque.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Commerce Analytics API",
    version="0.1.0",
    description="Plataforma SaaS de analítica para e-commerce"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}