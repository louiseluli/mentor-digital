"""
database — Persistence layer (SQLAlchemy + SQLite/PostgreSQL)

Dev: SQLite (zero config, free)
Prod: PostgreSQL (set DATABASE_URL env var)
"""

from src.database.engine import get_engine, get_session, init_db
from src.database.models import (
    AnalysisRecord,
    Base,
    Conversation,
    Evidence,
    Feedback,
    LearningModule,
    Submission,
    UserLearningProgress,
)
from src.database.repository import Repository

__all__ = [
    "Base",
    "AnalysisRecord",
    "Conversation",
    "Evidence",
    "Feedback",
    "LearningModule",
    "Submission",
    "UserLearningProgress",
    "Repository",
    "get_engine",
    "get_session",
    "init_db",
]
