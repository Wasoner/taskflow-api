"""Schemas Pydantic: definen la FORMA de los datos que entran y salen de la API.

- *Create: lo que el cliente envía (entrada)
- *Update: campos opcionales para PUT/PATCH
- *Out:    lo que la API devuelve (salida) - NUNCA expone password_hash

Pydantic valida automáticamente y devuelve errores 422 si los datos son
inválidos (FastAPI lo hace por nosotros).
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Enums: valores permitidos (heredan de str para serializar a JSON) ----------
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ---------- USERS ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # permite crear desde el objeto ORM

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime


# ---------- PROJECTS ----------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    owner_id: int  # sin JWT aún: el cliente indica quién crea el proyecto


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime


# ---------- TASKS ----------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    project_id: int
    assigned_to: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assigned_to: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    project_id: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime
