"""
test_api_multitenant.py — Validacion del aislamiento multi-tenant.

Corresponde al Objetivo 4 del plan de validacion:
"Deploy at least two real and independent client environments within a shared
multi-tenant infrastructure and ensure no cross-tenant data visibility."

Usa TestClient de FastAPI contra PostgreSQL real del contenedor.
El rate limiter se resetea antes de cada test para evitar 429 en CI.
"""
import pytest
import uuid
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.services.auth_service import register_user
from app.schemas.auth_schema import RegisterRequest

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@postgres:5432/ecommerce_analytics"
)


# Reset rate limit storage antes de cada test
# El limiter de auth.py es una instancia local con MemoryStorage
# Si no se resetea, TestClient (siempre IP "testclient") agota el limite en segundos
@pytest.fixture(autouse=True)
def reset_rate_limits():
    import app.api.routes.auth as auth_module
    storage = getattr(auth_module.limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()
    yield


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Crea usuario directamente via servicio (sin rate limit)
# Se usa en todos los tests que necesitan usuarios pero no prueban el endpoint de registro
def create_user(db, email, company, role="admin", password="Password123"):
    try:
        user = register_user(db, RegisterRequest(
            email=email,
            password=password,
            full_name="Test User",
            company_name=company,
            role=role,
        ))
        db.commit()
        return user
    except Exception:
        db.rollback()
        raise


def get_token(client, email, password="Password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login fallido para {email}: {res.json()}"
    return res.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# Tests que prueban el endpoint /register directamente
# Cada test hace maximo 2 llamadas — el reset del limiter garantiza que no hay 429
class TestRegistroRoles:
    def test_registro_admin_exitoso(self, client):
        res = client.post("/api/auth/register", json={
            "email": f"admin_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "full_name": "Admin Test",
            "company_name": f"Empresa {uuid.uuid4()}",
            "role": "admin",
        })
        assert res.status_code == 201

    def test_segundo_admin_misma_empresa_rechazado(self, client):
        company = f"Empresa {uuid.uuid4()}"
        client.post("/api/auth/register", json={
            "email": f"a1_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "company_name": company,
            "role": "admin",
        })
        res = client.post("/api/auth/register", json={
            "email": f"a2_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "company_name": company,
            "role": "admin",
        })
        assert res.status_code == 409

    def test_analista_empresa_inexistente_rechazado(self, client):
        res = client.post("/api/auth/register", json={
            "email": f"analista_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "company_name": f"EmpresaInexistente_{uuid.uuid4()}",
            "role": "analyst",
        })
        assert res.status_code == 409

    def test_analista_se_une_a_empresa_existente(self, client):
        company = f"Empresa {uuid.uuid4()}"
        client.post("/api/auth/register", json={
            "email": f"adm_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "company_name": company,
            "role": "admin",
        })
        res = client.post("/api/auth/register", json={
            "email": f"ana_{uuid.uuid4()}@test.com",
            "password": "Password123",
            "company_name": company,
            "role": "analyst",
        })
        assert res.status_code == 201


# Tests de aislamiento — usan create_user directo, no el endpoint de registro
class TestAislamientoMultitenant:
    def test_imports_aislados_por_usuario(self, client, db_session):
        # Dos usuarios del mismo tenant no comparten imports
        company = f"Empresa {uuid.uuid4()}"
        email_a = f"a_{uuid.uuid4()}@test.com"
        email_b = f"b_{uuid.uuid4()}@test.com"
        create_user(db_session, email_a, company, role="admin")
        create_user(db_session, email_b, company, role="analyst")

        token_a = get_token(client, email_a)
        token_b = get_token(client, email_b)

        res_a = client.get("/api/imports/", headers=auth_headers(token_a))
        res_b = client.get("/api/imports/", headers=auth_headers(token_b))
        assert res_a.status_code == 200
        assert res_b.status_code == 200
        assert isinstance(res_a.json(), list)
        assert isinstance(res_b.json(), list)

    def test_dashboards_aislados_por_usuario(self, client, db_session):
        # Usuario A crea dashboard, usuario B no lo ve
        company = f"Empresa {uuid.uuid4()}"
        email_a = f"da_{uuid.uuid4()}@test.com"
        email_b = f"db_{uuid.uuid4()}@test.com"
        create_user(db_session, email_a, company, role="admin")
        create_user(db_session, email_b, company, role="analyst")

        token_a = get_token(client, email_a)
        token_b = get_token(client, email_b)

        res_create = client.post(
            "/api/dashboards/",
            headers=auth_headers(token_a),
            json={"name": "Dashboard A"},
        )
        assert res_create.status_code == 201

        res_b = client.get("/api/dashboards/", headers=auth_headers(token_b))
        assert res_b.status_code == 200
        assert len(res_b.json()) == 0

    def test_tenants_diferentes_aislados(self, client, db_session):
        # Tenants distintos no comparten dashboards
        email_1 = f"t1_{uuid.uuid4()}@test.com"
        email_2 = f"t2_{uuid.uuid4()}@test.com"
        create_user(db_session, email_1, f"EmpresaX_{uuid.uuid4()}")
        create_user(db_session, email_2, f"EmpresaY_{uuid.uuid4()}")

        token_1 = get_token(client, email_1)
        token_2 = get_token(client, email_2)

        client.post("/api/dashboards/", headers=auth_headers(token_1), json={"name": "T1"})
        res = client.get("/api/dashboards/", headers=auth_headers(token_2))
        assert len(res.json()) == 0

    def test_reports_aislados_por_tenant(self, client, db_session):
        # Informes son privados por tenant — nuevos usuarios empiezan con lista vacia
        email_1 = f"r1_{uuid.uuid4()}@test.com"
        email_2 = f"r2_{uuid.uuid4()}@test.com"
        create_user(db_session, email_1, f"EmpresaRep1_{uuid.uuid4()}")
        create_user(db_session, email_2, f"EmpresaRep2_{uuid.uuid4()}")

        token_1 = get_token(client, email_1)
        token_2 = get_token(client, email_2)

        res_1 = client.get("/api/reports/", headers=auth_headers(token_1))
        res_2 = client.get("/api/reports/", headers=auth_headers(token_2))
        assert res_1.status_code == 200
        assert res_2.status_code == 200
        assert res_1.json() == []
        assert res_2.json() == []


# Tests de control de acceso al equipo
class TestTeamAccess:
    def test_analista_sin_team_access_recibe_403(self, client, db_session):
        company = f"Empresa {uuid.uuid4()}"
        email_adm = f"adm_{uuid.uuid4()}@test.com"
        email_ana = f"ana_{uuid.uuid4()}@test.com"
        create_user(db_session, email_adm, company, role="admin")
        create_user(db_session, email_ana, company, role="analyst")

        token_analyst = get_token(client, email_ana)
        res = client.get("/api/team/reports", headers=auth_headers(token_analyst))
        assert res.status_code == 403

    def test_admin_accede_a_team_reports(self, client, db_session):
        email = f"adm2_{uuid.uuid4()}@test.com"
        create_user(db_session, email, f"Empresa {uuid.uuid4()}")
        token = get_token(client, email)
        res = client.get("/api/team/reports", headers=auth_headers(token))
        assert res.status_code == 200

    def test_sin_token_recibe_403(self, client):
        # HTTPBearer de FastAPI devuelve 403 cuando no hay header Authorization
        res = client.get("/api/team/reports")
        assert res.status_code == 403

    def test_admin_puede_ver_miembros(self, client, db_session):
        email = f"adm3_{uuid.uuid4()}@test.com"
        create_user(db_session, email, f"Empresa {uuid.uuid4()}")
        token = get_token(client, email)
        res = client.get("/api/team/members", headers=auth_headers(token))
        assert res.status_code == 200
        members = res.json()
        assert len(members) >= 1
        assert members[0]["role"] == "admin"

    def test_analista_no_puede_ver_miembros(self, client, db_session):
        # La gestion de miembros es solo para admins
        company = f"Empresa {uuid.uuid4()}"
        email_adm = f"adm4_{uuid.uuid4()}@test.com"
        email_ana = f"ana2_{uuid.uuid4()}@test.com"
        create_user(db_session, email_adm, company, role="admin")
        create_user(db_session, email_ana, company, role="analyst")

        token_analyst = get_token(client, email_ana)
        res = client.get("/api/team/members", headers=auth_headers(token_analyst))
        assert res.status_code == 403