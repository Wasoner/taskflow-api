"""Conexión a PostgreSQL y gestión de sesiones de base de datos."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Motor: crea y gestiona el "pool" de conexiones a PostgreSQL
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Fábrica de sesiones: cada petición HTTP usará una sesión independiente
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base de la que heredarán todos los modelos (tablas)."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: inyecta una sesión de BD y la cierra al terminar.

    Patrón "inyección de dependencias": el endpoint no abre ni cierra
    conexiones a mano, se lo indica FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
