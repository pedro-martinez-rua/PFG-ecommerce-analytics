"""
conftest.py — Fixtures compartidos por todos los tests.

Usa PostgreSQL real (mismo contenedor que el backend) para tests
que necesitan BD. SQLite no soporta JSONB que usa el proyecto.
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import hash_password

# Usa la misma BD del proyecto — los tests generan datos únicos con uuid
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@postgres:5432/ecommerce_analytics"
)

@pytest.fixture(scope="function")
def db():
    # Fixtures de BD para test_auth_service
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def make_tenant(db, name="Tienda Test"):
    import uuid
    tenant = Tenant(id=uuid.uuid4(), name=name, currency="EUR")
    db.add(tenant)
    db.flush()
    return tenant


def make_user(db, tenant_id, email="admin@test.com", role="admin", team_access=True):
    import uuid
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=email,
        hashed_password=hash_password("Password123"),
        role=role,
        team_access=team_access,
    )
    db.add(user)
    db.flush()
    return user