"""Tests de proyectos y tareas: CRUD, validaciones y cascada."""


def test_crear_y_obtener_proyecto(client, user):
    creado = client.post(
        "/projects",
        json={"name": "API REST", "description": "Práctica", "owner_id": user["id"]},
    )
    assert creado.status_code == 201
    project_id = creado.json()["id"]

    obtenido = client.get(f"/projects/{project_id}")
    assert obtenido.status_code == 200
    assert obtenido.json()["name"] == "API REST"


def test_proyecto_con_dueno_inexistente_devuelve_404(client):
    response = client.post(
        "/projects",
        json={"name": "Huérfano", "owner_id": 999999},
    )
    assert response.status_code == 404


def test_actualizar_proyecto_parcial(client, project):
    response = client.put(f"/projects/{project['id']}", json={"name": "Nombre Nuevo"})
    assert response.status_code == 200
    assert response.json()["name"] == "Nombre Nuevo"
    assert response.json()["description"] == project["description"]  # no cambió


def test_crear_tarea_y_filtrar_por_estado(client, project, user):
    creacion = client.post(
        "/tasks",
        json={
            "title": "Escribir documentación",
            "status": "in_progress",
            "priority": "high",
            "project_id": project["id"],
            "assigned_to": user["id"],
        },
    )
    assert creacion.status_code == 201

    filtradas = client.get("/tasks", params={"status": "in_progress", "project_id": project["id"]})
    assert filtradas.status_code == 200
    assert len(filtradas.json()) == 1
    assert filtradas.json()[0]["title"] == "Escribir documentación"


def test_tarea_en_proyecto_inexistente_devuelve_404(client):
    response = client.post(
        "/tasks",
        json={"title": "Sin proyecto", "project_id": 999999},
    )
    assert response.status_code == 404


def test_estado_invalido_devuelve_422(client, project):
    response = client.post(
        "/tasks",
        json={"title": "Mal estado", "status": "volando", "project_id": project["id"]},
    )
    assert response.status_code == 422  # el enum de Pydantic lo rechaza


def test_parchear_tarea_actualiza_solo_lo_enviado(client, project):
    creacion = client.post(
        "/tasks",
        json={"title": "Tarea a parchear", "project_id": project["id"]},
    )
    task_id = creacion.json()["id"]
    assert creacion.json()["status"] == "pending"  # valor por defecto

    parche = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert parche.status_code == 200
    assert parche.json()["status"] == "done"
    assert parche.json()["title"] == "Tarea a parchear"  # no cambió


def test_eliminar_proyecto_borra_tareas_en_cascada(client, project, user):
    creacion = client.post(
        "/tasks",
        json={"title": "Tarea huérfana", "project_id": project["id"]},
    )
    task_id = creacion.json()["id"]

    borrado = client.delete(f"/projects/{project['id']}")
    assert borrado.status_code == 204

    # La tarea debe haberse borrado con el proyecto (ON DELETE CASCADE)
    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.get(f"/projects/{project['id']}").status_code == 404
