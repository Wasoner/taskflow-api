"""TaskFlow API - aplicación FastAPI.

Punto de entrada del backend. Arranque local:
    uvicorn app.main:app --reload
Documentación interactiva autogenerada:
    http://127.0.0.1:8000/docs      (Swagger UI)
    http://127.0.0.1:8000/redoc     (ReDoc)
"""

from fastapi import FastAPI

from app.config import settings
from app.routers import projects, tasks, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST de gestión de proyectos y tareas - proyecto de práctica",
)

# Registro de routers: cada módulo aporta sus endpoints
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/", tags=["health"])
def health_check():
    """Endpoint de salud: lo usan los monitores para saber si la API está viva."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
