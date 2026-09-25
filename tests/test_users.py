"""Tests del endpoint de salud y de usuarios."""


def test_health_responde_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_crear_usuario_devuelve_201_sin_password(client):
    response = client.post(
        "/users",
        json={"email": "nuevo@example.com", "password": "Segura1234", "full_name": "Nuevo Usuario"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nuevo@example.com"
    # SEGURIDAD: la contraseña jamás debe aparecer en la respuesta
    assert "password" not in data
    assert "password_hash" not in data


def test_email_duplicado_devuelve_409(client, user):
    response = client.post(
        "/users",
        json={"email": user["email"], "password": "OtraClave123", "full_name": "Impostor"},
    )
    assert response.status_code == 409


def test_datos_invalidos_devuelven_422(client):
    response = client.post(
        "/users",
        json={"email": "no-es-email", "password": "123", "full_name": ""},
    )
    assert response.status_code == 422


def test_obtener_usuario_inexistente_devuelve_404(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_listar_usuarios_no_expone_hashes(client, user):
    response = client.get("/users")
    assert response.status_code == 200
    for item in response.json():
        assert "password_hash" not in item
