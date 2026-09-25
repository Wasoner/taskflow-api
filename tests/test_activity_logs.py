"""Tests del endpoint de logs de actividad (datos provenientes de MongoDB)."""


def test_activity_logs_devuelve_lista(client, project):
    """El fixture 'project' genera eventos de auditoría en MongoDB."""
    response = client.get("/activity-logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_evento_registrado_coincide_con_proyecto_creado(client, project):
    """Al crear un proyecto debe quedar un evento con su id en MongoDB."""
    logs = client.get("/activity-logs", params={"action": "project.created", "limit": 200}).json()
    assert any(log["entity_id"] == project["id"] for log in logs)


def test_filtro_por_accion(client, project):
    logs = client.get("/activity-logs", params={"action": "project.created"}).json()
    assert len(logs) >= 1
    assert all(item["action"] == "project.created" for item in logs)


def test_limit_invalido_devuelve_422(client):
    response = client.get("/activity-logs", params={"limit": 0})
    assert response.status_code == 422
