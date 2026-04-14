"""
test_auth_service.py — Validacion de la logica de registro con roles.

Prueba el flujo de registro definido en auth_service.py:
- Admin crea nueva empresa
- Segundo admin para la misma empresa es rechazado
- Analista se une a empresa existente
- Analista con empresa inexistente es rechazado
- Email duplicado es rechazado
"""
import pytest
import uuid
from app.services.auth_service import register_user
from app.schemas.auth_schema import RegisterRequest


def _register(db, email, company, role="admin"):
    return register_user(db, RegisterRequest(
        email=email,
        password="Password123",
        full_name="Test User",
        company_name=company,
        role=role,
    ))


# Registro de admin
class TestRegistroAdmin:
    def test_admin_crea_tenant(self, db):
        user = _register(db, f"admin_{uuid.uuid4()}@test.com", f"Tienda {uuid.uuid4()}", role="admin")
        assert user.role == "admin"
        assert user.team_access == True
        db.rollback()

    def test_segundo_admin_misma_empresa_rechazado(self, db):
        company = f"Tienda {uuid.uuid4()}"
        _register(db, f"admin1_{uuid.uuid4()}@test.com", company, role="admin")
        db.commit()
        with pytest.raises(ValueError, match="Ya existe un administrador"):
            _register(db, f"admin2_{uuid.uuid4()}@test.com", company, role="admin")
        db.rollback()

    def test_admin_empresas_distintas_permitido(self, db):
        user_a = _register(db, f"admin_{uuid.uuid4()}@test.com", f"EmpresaA {uuid.uuid4()}", role="admin")
        db.commit()
        user_b = _register(db, f"admin_{uuid.uuid4()}@test.com", f"EmpresaB {uuid.uuid4()}", role="admin")
        db.commit()
        assert user_a.tenant_id != user_b.tenant_id
        db.rollback()

    def test_email_duplicado_rechazado(self, db):
        email = f"admin_{uuid.uuid4()}@test.com"
        _register(db, email, f"Tienda {uuid.uuid4()}", role="admin")
        db.commit()
        with pytest.raises(ValueError, match="Ya existe una cuenta"):
            _register(db, email, f"Tienda {uuid.uuid4()}", role="admin")
        db.rollback()


# Registro de analista
class TestRegistroAnalista:
    def test_analista_se_une_a_empresa_existente(self, db):
        company = f"Tienda {uuid.uuid4()}"
        admin = _register(db, f"admin_{uuid.uuid4()}@test.com", company, role="admin")
        db.commit()
        analyst = _register(db, f"analista_{uuid.uuid4()}@test.com", company, role="analyst")
        db.commit()
        assert analyst.role == "analyst"
        assert analyst.tenant_id == admin.tenant_id
        db.rollback()

    def test_analista_team_access_false_por_defecto(self, db):
        company = f"Tienda {uuid.uuid4()}"
        _register(db, f"admin_{uuid.uuid4()}@test.com", company, role="admin")
        db.commit()
        analyst = _register(db, f"analista_{uuid.uuid4()}@test.com", company, role="analyst")
        db.commit()
        assert analyst.team_access == False
        db.rollback()

    def test_analista_empresa_inexistente_rechazado(self, db):
        with pytest.raises(ValueError, match="No existe ninguna empresa"):
            _register(db, f"analista_{uuid.uuid4()}@test.com", f"EmpresaInexistente_{uuid.uuid4()}", role="analyst")
        db.rollback()

    def test_multiples_analistas_mismo_tenant(self, db):
        company = f"Tienda {uuid.uuid4()}"
        _register(db, f"admin_{uuid.uuid4()}@test.com", company, role="admin")
        db.commit()
        a1 = _register(db, f"ana1_{uuid.uuid4()}@test.com", company, role="analyst")
        db.commit()
        a2 = _register(db, f"ana2_{uuid.uuid4()}@test.com", company, role="analyst")
        db.commit()
        assert a1.tenant_id == a2.tenant_id
        db.rollback()

    def test_rol_invalido_rechazado(self, db):
        with pytest.raises(ValueError, match="Rol invalido|Rol inválido"):
            _register(db, f"x_{uuid.uuid4()}@test.com", f"Empresa {uuid.uuid4()}", role="superadmin")
        db.rollback()

    def test_nombre_empresa_insensible_mayusculas(self, db):
        # El analista puede unirse aunque escriba el nombre en distinto case
        company = f"Tienda {uuid.uuid4()}"
        _register(db, f"admin_{uuid.uuid4()}@test.com", company, role="admin")
        db.commit()
        analyst = _register(db, f"analista_{uuid.uuid4()}@test.com", company.lower(), role="analyst")
        db.commit()
        assert analyst is not None
        db.rollback()