"""Configuración compartida de los tests.

Principios clave:
- Los tests NUNCA tocan la BD de desarrollo ("proyecto_api"):
  usamos una BD separada ("proyecto_api_test") que se limpia al
  empezar y al terminar la sesión de pruebas.
- "dependency_overrides" sustituye la conexión real por la de test
  solo durante los tests: el código de producción no cambia.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = settings.database_url.replace("/proyecto_api", "/proyecto_api_test")

test_engine = create_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP de prueba con BD limpia al inicio y al final."""
    Base.metadata.drop_all(bind=test_engine)   # por si quedó basura de una ejecución anterior
    Base.metadata.create_all(bind=test_engine)  # crea las tablas desde los modelos

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def user(client):
    """Crea un usuario único para cada test (evita duplicados entre tests)."""
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/users",
        json={"email": email, "password": "ClaveSegura123", "full_name": "Usuario Test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def project(client, user):
    """Crea un proyecto perteneciente al usuario del fixture anterior."""
    response = client.post(
        "/projects",
        json={"name": "Proyecto Test", "description": "Creado por pytest", "owner_id": user["id"]},
    )
    assert response.status_code == 201, response.text
    return response.json()
