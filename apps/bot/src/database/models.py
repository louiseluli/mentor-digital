"""
database/models.py — SQLAlchemy ORM models for Mentor Digital

LGPD-compliant: user_id is always a pseudonymous hash.
No phone numbers, names, or PII stored.
"""

import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# ── Conversations ──────────────────────────────────────────────────────────────

class Conversation(Base):
    """Record of a conversation session (bot or web)."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pseudonymous_user_id: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(20))  # 'whatsapp' | 'telegram' | 'web'
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    final_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    transitioned_to_web: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    submissions: Mapped[list["Submission"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


# ── Submissions ────────────────────────────────────────────────────────────────

class Submission(Base):
    """Content submitted by a user for analysis."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=True)
    content_type: Mapped[str] = mapped_column(String(20))  # 'text' | 'link'
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256 for deduplication
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships
    conversation: Mapped["Conversation | None"] = relationship(back_populates="submissions")
    analysis: Mapped["AnalysisRecord | None"] = relationship(back_populates="submission", uselist=False)
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


# ── Analysis Results ───────────────────────────────────────────────────────────

class AnalysisRecord(Base):
    """Consolidated analysis results for a submission."""

    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), unique=True)
    content_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)  # UUID for web access

    # Risk scores
    risk_overall: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_verdict: Mapped[str | None] = mapped_column(String(30), nullable=True)
    risk_verdict_pt: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NLP scores
    urgency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    manipulation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    claim_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Coverage
    fact_check_count: Mapped[int] = mapped_column(Integer, default=0)
    gdelt_article_count: Mapped[int] = mapped_column(Integer, default=0)
    google_news_count: Mapped[int] = mapped_column(Integer, default=0)
    wikipedia_count: Mapped[int] = mapped_column(Integer, default=0)
    brazilian_fc_count: Mapped[int] = mapped_column(Integer, default=0)

    # FC verdict breakdown
    fc_false: Mapped[int] = mapped_column(Integer, default=0)
    fc_mixed: Mapped[int] = mapped_column(Integer, default=0)
    fc_true: Mapped[int] = mapped_column(Integer, default=0)

    # Full JSON result (for backward compatibility with Redis approach)
    full_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="analysis")


# ── Evidence ───────────────────────────────────────────────────────────────────

class Evidence(Base):
    """Individual evidence item (fact-check, news article, Wikipedia, etc.)."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"))

    source_type: Mapped[str] = mapped_column(String(30))  # 'fact_check' | 'gdelt' | 'google_news' | 'wikipedia' | 'brazilian_fc'
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    stance: Mapped[str] = mapped_column(String(20), default="neutral")  # 'supports' | 'contradicts' | 'neutral'
    credibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_fact_checker: Mapped[bool] = mapped_column(Boolean, default=False)
    fact_check_rating: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rating_value: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Google scale 1-7

    language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="evidence")


# ── Feedback ───────────────────────────────────────────────────────────────────

class Feedback(Base):
    """Anonymized user feedback on analysis usefulness."""

    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=True)
    content_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    feeling_after: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usefulness_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    would_recommend: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    free_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships
    conversation: Mapped["Conversation | None"] = relationship(back_populates="feedback")


# ── Learning ───────────────────────────────────────────────────────────────────

class LearningModule(Base):
    """Educational module content."""

    __tablename__ = "learning_modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title_pt: Mapped[str] = mapped_column(String(255))
    description_pt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[str] = mapped_column(Text)  # JSON with sections, quizzes, examples
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5)
    topic: Mapped[str] = mapped_column(String(50))  # 'bias' | 'sources' | 'deepfakes' | 'algorithms' | 'rights'
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Relationships
    progress: Mapped[list["UserLearningProgress"]] = relationship(back_populates="module", cascade="all, delete-orphan")


class UserLearningProgress(Base):
    """Track user progress through learning modules (anonymized)."""

    __tablename__ = "user_learning_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pseudonymous_user_id: Mapped[str] = mapped_column(String(64), index=True)
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_modules.id"))

    status: Mapped[str] = mapped_column(String(20), default="not_started")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quiz_answers_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    module: Mapped["LearningModule"] = relationship(back_populates="progress")
