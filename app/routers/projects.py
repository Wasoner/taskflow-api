"""Endpoints de proyectos: CRUD completo."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User
from app.mongo import log_activity
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Crea un proyecto. 404 si el dueño no existe."""
    if db.get(User, payload.owner_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario dueño no encontrado")

    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    log_activity("project.created", "project", project.id, {"name": project.name, "owner_id": project.owner_id})
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(owner_id: int | None = None, db: Session = Depends(get_db)):
    """Lista proyectos. Filtro opcional: ?owner_id=1"""
    stmt = select(Project)
    if owner_id is not None:
        stmt = stmt.where(Project.owner_id == owner_id)
    return db.execute(stmt.order_by(Project.id)).scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    """Actualización parcial: solo cambia los campos que llegan en el body."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Borra el proyecto. Sus tareas se eliminan en cascada (ON DELETE CASCADE)."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")

    db.delete(project)
    db.commit()
    log_activity("project.deleted", "project", project_id, {"name": project.name})
    # 204 = eliminado correctamente, sin cuerpo de respuesta
