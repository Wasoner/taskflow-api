"""Endpoints de tareas: CRUD completo con filtros y paginación."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task, User
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una tarea. Valida que el proyecto y el asignado existan (404)."""
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    if payload.assigned_to is not None and db.get(User, payload.assigned_to) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario asignado no encontrado")

    task = Task(
        **payload.model_dump(exclude={"status", "priority"}),
        status=payload.status.value,
        priority=payload.priority.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    project_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to: int | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Lista tareas con filtros y paginación.

    Ejemplos: /tasks?project_id=1  |  /tasks?status=done  |  /tasks?limit=10&offset=10
    La paginación es OBLIGATORIA en APIs profesionales: sin ella, una tabla
    con millones de filas bloquearía el servidor.
    """
    stmt = select(Task)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if assigned_to is not None:
        stmt = stmt.where(Task.assigned_to == assigned_to)

    stmt = stmt.order_by(Task.id).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualización parcial (PATCH): cambia solo los campos enviados."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    data = payload.model_dump(exclude_unset=True)

    if "assigned_to" in data and data["assigned_to"] is not None:
        if db.get(User, data["assigned_to"]) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario asignado no encontrado")

    for field, value in data.items():
        setattr(task, field, value)
    # updated_at se actualiza solo gracias a onupdate=func.now() del modelo

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    db.delete(task)
    db.commit()
