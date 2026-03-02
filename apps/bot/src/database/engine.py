"""
database/engine.py — SQLAlchemy engine & session factory

Dev:  SQLite (zero config) — DATABASE_URL not set → uses ./data/mentor.db
Prod: PostgreSQL — set DATABASE_URL=postgresql+asyncpg://...

Sync engine is used (not async) for simplicity + compatibility with
existing sync code (analytics, session_manager). If needed later,
async can be added with create_async_engine + aiosqlite/asyncpg.
"""

import logging
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None


def _default_sqlite_url() -> str:
    """SQLite file in apps/bot/data/ — auto-created."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return f"sqlite:///{os.path.join(data_dir, 'mentor.db')}"


def get_engine(url: str | None = None):
    """Get or create the SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is not None:
        return _engine

    db_url = url or os.getenv("DATABASE_URL") or _default_sqlite_url()

    # Handle Railway-style postgres:// → postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    is_sqlite = db_url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}
    _engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
    )

    # Enable WAL mode for SQLite (better concurrent reads)
    if is_sqlite:
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("Database engine created | url=%s", db_url.split("@")[-1] if "@" in db_url else db_url)
    return _engine


def get_session() -> Session:
    """Get a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db(url: str | None = None) -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    logger.info("Database tables initialized")


def reset_engine() -> None:
    """Reset engine (for testing). Disposes connections and clears singleton."""
    global _engine, _SessionFactory
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
