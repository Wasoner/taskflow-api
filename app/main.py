"""TaskFlow API - aplicación FastAPI.

Punto de entrada del backend. Arranque local:
    uvicorn app.main:app --reload
Documentación interactiva autogenerada:
    http://127.0.0.1:8000/docs      (Swagger UI)
    http://127.0.0.1:8000/redoc     (ReDoc)
Frontend (HTML/CSS/TypeScript):
    http://127.0.0.1:8000/
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import activity, projects, tasks, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST de gestión de proyectos y tareas - proyecto de práctica",
)

# Registro de routers: cada módulo aporta sus endpoints
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(activity.router)


@app.get("/health", tags=["health"])
def health_check():
    """Endpoint de salud: lo usan los monitores para saber si la API está viva."""
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


# Frontend estático (HTML/CSS/TypeScript compilado).
# IMPORTANTE: debe registrarse EL ÚLTIMO: las rutas de la API tienen prioridad.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
