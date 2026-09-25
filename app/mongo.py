"""Conexión a MongoDB y registro de actividad (auditoría).

CASO DE USO NoSQL: los eventos de auditoría son documentos semiestructurados
- "task.created" lleva {title, project_id}, "task.updated" lleva {changed_fields}
- Cada evento puede tener campos distintos → documento flexible, no tabla rígida
- Son append-only (solo escritura) y no necesitan JOINs con el resto de datos

Principio importante: registrar logs NUNCA debe romper la operación principal.
Si MongoDB está caído, la API sigue funcionando (solo se emite un warning).
"""

import logging
from datetime import datetime, timezone

from pymongo import MongoClient

from app.config import settings

logger = logging.getLogger(__name__)

client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=3000)
mongo_db = client["proyecto_api"]
activity_logs = mongo_db["activity_logs"]

# Índice compuesto para las consultas típicas: filtrar por acción y ordenar por fecha
activity_logs.create_index([("action", 1), ("timestamp", -1)])


def log_activity(action: str, entity: str, entity_id: int | None = None, detail: dict | None = None) -> None:
    """Inserta un evento de auditoría en MongoDB. Silencioso ante fallos."""
    try:
        activity_logs.insert_one(
            {
                "action": action,             # p.ej. "task.created"
                "entity": entity,             # "task" | "project" | "user"
                "entity_id": entity_id,
                "detail": detail or {},
                "timestamp": datetime.now(timezone.utc),
                "source": settings.app_name,
            }
        )
    except Exception as exc:  # noqa: BLE001 - el log jamás debe tumbar la API
        logger.warning("No se pudo registrar la actividad en MongoDB: %s", exc)
