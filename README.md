# TaskFlow API

API REST de gestión de proyectos y tareas, construida como proyecto de práctica para demostrar competencias en desarrollo backend, bases de datos y **documentación técnica**.

## 📋 Contenido

- [Stack tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Modelo de datos (Diagrama ER)](#-modelo-de-datos-diagrama-er)
- [Instalación y puesta en marcha](#-instalación-y-puesta-en-marcha)
- [Endpoints (Guía de la API)](#-endpoints-guía-de-la-api)
- [Pruebas automatizadas](#-pruebas-automatizadas)
- [Seguridad (ISO 27001)](#-seguridad-iso-27001)
- [Estructura del proyecto](#-estructura-del-proyecto)

---

## 🛠 Stack tecnológico

| Capa | Tecnología | Versión | Propósito |
|---|---|---|---|
| Lenguaje | Python | 3.12 | Lenguaje del backend |
| Framework | FastAPI | 0.141 | Framework web + OpenAPI automático |
| Validación | Pydantic | v2 | Validación de entrada/salida |
| ORM | SQLAlchemy | 2.1 | Mapeo objeto-relacional |
| BD relacional | PostgreSQL | 16 | Almacenamiento persistente (SQL) |
| Driver | psycopg2 | — | Comunicación Python ↔ PostgreSQL |
| Servidor | Uvicorn | — | Servidor ASGI |
| Pruebas | pytest + httpx | — | Tests de integración |
| Contenedores | Docker | — | Aislamiento de la BD |
| Cliente BD | DBeaver | — | Consulta y gestión de datos |

---

## 🏗 Arquitectura

Patrón **por capas** (separation of concerns): cada capa tiene una única responsabilidad.

```mermaid
flowchart TB
    Client["Cliente<br/>(Swagger UI / Navegador / DBeaver)"]
    Router["Routers (app/routers/)<br/>📌 Definen rutas HTTP y códigos de estado"]
    Schema["Schemas Pydantic (app/schemas.py)<br/>✅ Validan los datos de entrada/salida"]
    Model["Models SQLAlchemy (app/models.py)<br/>🗄 Clases Python ↔ tablas SQL"]
    DB["database.py<br/>🔌 Sesiones y conexión"]
    PG[("PostgreSQL 16<br/>(contenedor Docker)")]

    Client -->|"JSON + HTTP"| Router
    Router --> Schema
    Schema --> Model
    Model --> DB
    DB --> PG
    PG -->|"Respuesta"| Client
```

**Flujo de una petición** (`POST /tasks`):

1. El cliente envía JSON → el **router** recibe la petición.
2. **Pydantic** valida: ¿campos correctos? Si no → `422` con detalle del error.
3. El **modelo ORM** traduce la operación a SQL (`INSERT INTO tasks ...`).
4. **SQLAlchemy** ejecuta en PostgreSQL y devuelve el objeto.
5. El router responde `201` con el JSON (sin datos sensibles).

---

## 🗄 Modelo de datos (Diagrama ER)

Base de datos `proyecto_api` — 3 tablas con relaciones 1:N y restricciones integridad.

```mermaid
erDiagram
    users ||--o{ projects : "owner_id (posee)"
    projects ||--o{ tasks : "project_id (contiene)"
    users ||--o{ tasks : "assigned_to (ejecuta)"

    users {
        serial id PK
        varchar email UK "UNIQUE - login"
        varchar password_hash "bcrypt, jamás texto plano"
        varchar full_name
        boolean is_active
        timestamptz created_at
    }
    projects {
        serial id PK
        varchar name
        text description
        int owner_id FK "→ users.id (CASCADE)"
        timestamptz created_at
    }
    tasks {
        serial id PK
        varchar title
        text description
        varchar status "CHECK: pending/in_progress/done"
        varchar priority "CHECK: low/medium/high"
        date due_date
        int project_id FK "→ projects.id (CASCADE)"
        int assigned_to FK "→ users.id (SET NULL)"
        timestamptz created_at
        timestamptz updated_at "se actualiza solo"
    }
```

**Decisiones de diseño**:

| Decisión | Motivo |
|---|---|
| `ON DELETE CASCADE` en `projects` | Al borrar un proyecto, sus tareas se borran con él (integridad referencial) |
| `ON DELETE SET NULL` en `assigned_to` | Si se borra un usuario, sus tareas quedan *sin asignar*, no desaparecen |
| `CHECK` en `status`/`priority` | La BD rechaza valores inválidos aunque alguien borre la API (defensa en profundidad) |
| Índices en `owner_id`, `project_id`, `assigned_to` | Aceleran las consultas filtradas (rendimiento) |
| `password_hash` en lugar de `password` | Imposible recuperar la contraseña: solo se almacena su hash bcrypt |

Script SQL completo: [`database/schema.sql`](database/schema.sql)

---

## 🚀 Instalación y puesta en marcha

**Requisitos**: Python 3.12+, Docker Desktop, DBeaver (opcional pero recomendado).

### 1. Base de datos (Docker)

```bash
docker run --name proyectoapi-postgres \
  -e POSTGRES_USER=appuser \
  -e POSTGRES_PASSWORD=DevPass2026 \
  -e POSTGRES_DB=proyecto_api \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres:16
```

> Los datos persisten en el volumen `pgdata`: puedes borrar el contenedor y recrearlo sin perder nada.

### 2. Esquema y datos de prueba

Ejecutar [`database/schema.sql`](database/schema.sql) en DBeaver (conexión → `proyecto_api` → New SQL Editor → Execute).

### 3. Entorno virtual y dependencias

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

### 4. Variables de entorno

Crear un archivo `.env` en la raíz (está en `.gitignore`: **nunca se sube a Git**):

```env
DATABASE_URL=postgresql+psycopg2://appuser:DevPass2026@localhost:5432/proyecto_api
```

### 5. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

### 6. Base de datos de pruebas (solo para tests)

```bash
docker exec proyectoapi-postgres psql -U appuser -d postgres -c "CREATE DATABASE proyecto_api_test;"
```

---

## 📡 Endpoints (Guía de la API)

Base URL: `http://127.0.0.1:8000`

### Usuarios

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `POST` | `/users` | Registrar usuario (contraseña hasheada con bcrypt) | `201`, `409` email duplicado, `422` datos inválidos |
| `GET` | `/users` | Listar usuarios (nunca expone hashes) | `200` |
| `GET` | `/users/{id}` | Detalle de usuario | `200`, `404` |

```json
POST /users
{ "email": "ana@example.com", "password": "Segura1234", "full_name": "Ana García" }
```

### Proyectos

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `POST` | `/projects` | Crear proyecto | `201`, `404` dueño inexistente, `422` |
| `GET` | `/projects?owner_id=1` | Listar (filtro opcional por dueño) | `200` |
| `GET` | `/projects/{id}` | Detalle | `200`, `404` |
| `PUT` | `/projects/{id}` | Actualizar parcial (solo campos enviados) | `200`, `404` |
| `DELETE` | `/projects/{id}` | Eliminar (borra tareas en cascada) | `204`, `404` |

### Tareas

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `POST` | `/tasks` | Crear tarea | `201`, `404` proyecto/usuario inexistente, `422` |
| `GET` | `/tasks?status=done&project_id=1&limit=50&offset=0` | Listar con filtros **y paginación** | `200` |
| `GET` | `/tasks/{id}` | Detalle | `200`, `404` |
| `PATCH` | `/tasks/{id}` | Actualización parcial | `200`, `404` |
| `DELETE` | `/tasks/{id}` | Eliminar | `204`, `404` |

### Códigos de estado utilizados

| Código | Significado | Cuándo |
|---|---|---|
| `200` | OK | Lectura o actualización exitosa |
| `201` | Created | Recurso creado correctamente |
| `204` | No Content | Eliminación exitosa (sin cuerpo) |
| `404` | Not Found | El recurso solicitado no existe |
| `409` | Conflict | Violación de unicidad (email duplicado) |
| `422` | Unprocessable Entity | Datos que no superan la validación de Pydantic |

---

## 🧪 Pruebas automatizadas

```bash
pytest -v
```

**14 tests de integración** que verifican:

- ✅ Flujo completo de cada endpoint (CRUD)
- ✅ Códigos de estado correctos (`201`, `404`, `409`, `422`, `204`)
- ✅ **Seguridad**: la contraseña nunca aparece en respuestas HTTP
- ✅ Integridad referencial: borrar un proyecto elimina sus tareas (cascada)
- ✅ Los tests usan una BD separada (`proyecto_api_test`): jamás tocan datos de desarrollo

---

## 🔒 Seguridad (ISO 27001)

| Medida | Implementación |
|---|---|
| Credenciales fuera del código | Variables en `.env` + `.gitignore` |
| Contraseñas | Hash **bcrypt** con salt (irrecuperables) |
| Mínima exposición | `password_hash` nunca sale en respuestas HTTP |
| Validación de entrada | Pydantic rechaza datos malformados (`422`) antes de tocar la BD |
| Integridad | Restricciones `CHECK`, `UNIQUE` y FK también en la BD (defensa en profundidad) |
| Dependencias | Versiones fijadas en `requirements.txt` (control de vulnerabilidades) |

---

## 📁 Estructura del proyecto

```
proyectoAPI/
├── app/
│   ├── main.py          # Punto de entrada: crea la app FastAPI
│   ├── config.py        # Lectura de .env (configuración)
│   ├── database.py      # Conexión y sesiones (pool)
│   ├── models.py        # Modelos ORM (tablas)
│   ├── schemas.py       # Schemas Pydantic (validación)
│   ├── security.py      # Hash y verificación de contraseñas
│   └── routers/
│       ├── users.py     # Endpoints de usuarios
│       ├── projects.py  # Endpoints de proyectos
│       └── tasks.py     # Endpoints de tareas
├── tests/
│   ├── conftest.py      # Fixtures: cliente de test + BD de prueba
│   ├── test_users.py
│   └── test_projects_tasks.py
├── database/
│   └── schema.sql       # Esquema SQL (ejecutable en DBeaver)
├── .env                 # Configuración local (NO versionado)
├── requirements.txt     # Dependencias fijadas
└── pytest.ini           # Configuración de pytest
```

---

## 🗺 Roadmap

- [x] Fase 1: PostgreSQL en Docker + esquema SQL
- [x] Fase 2: API REST con FastAPI (CRUD completo)
- [x] Fase 3: Tests con pytest + documentación
- [ ] Fase 4: MongoDB (logs de actividad NoSQL) + frontend HTML5/CSS3/TypeScript
