"""Endpoints de logs de actividad (auditoría) - datos almacenados en MongoDB."""

from fastapi import APIRouter, Query

from app.mongo import activity_logs

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@router.get("")
def list_activity_logs(
    action: str | None = Query(default=None, description="Filtro exacto, p.ej. task.created"),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    """Lista los eventos de auditoría registrados en MongoDB (más recientes primero).

    Ejemplos:
      /activity-logs
      /activity-logs?action=task.created
      /activity-logs?limit=10
    """
    query = {}
    if action is not None:
        query["action"] = action

    cursor = (
        activity_logs.find(query, {"_id": 0})  # _id es un ObjectId: no es JSON, lo excluimos
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)
