"""
test_database.py — Tests for the persistence layer (database models, engine, repository)

Uses SQLite in-memory for test isolation — no disk I/O, no cleanup needed.
"""

import json
import pytest
from datetime import datetime, UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def repo(db_session):
    """Repository wired to the in-memory session."""
    return Repository(session=db_session)


def _sample_analysis() -> dict:
    """Minimal analysis result dict matching the structure from analysis_service."""
    return {
        "query": "Ivermectina cura COVID-19",
        "nlp": {
            "language": "pt",
            "word_count": 4,
            "urgency": {"score": 0.3, "matches": 1},
            "manipulation": {"score": 0.5, "matches": 3},
            "claim": {"score": 0.7, "strength": "strong"},
        },
        "risk_score": {
            "overall": 68,
            "level": "high",
            "verdict": "HIGH_RISK",
            "verdict_pt": "Alto risco de desinformação",
            "confidence": 0.72,
            "fc_verdict_breakdown": {"false": 2, "mixed": 1, "true": 0},
        },
        "fact_check": {
            "pt": {
                "results": [
                    {
                        "text": "Ivermectina cura COVID",
                        "reviews": [
                            {
                                "publisher_name": "Aos Fatos",
                                "publisher_site": "aosfatos.org",
                                "url": "https://aosfatos.org/check/1",
                                "title": "Falso: Ivermectina não cura COVID",
                                "text_rating": "Falso",
                                "rating_value": 1,
                                "review_date": "2024-03-01",
                            }
                        ],
                    }
                ]
            },
            "en": {
                "results": [
                    {
                        "text": "Ivermectin cures COVID",
                        "reviews": [
                            {
                                "publisher_name": "PolitiFact",
                                "publisher_site": "politifact.com",
                                "url": "https://politifact.com/check/1",
                                "title": "False: Ivermectin doesn't cure COVID",
                                "text_rating": "False",
                                "rating_value": 1,
                                "review_date": "2024-02-15",
                            }
                        ],
                    }
                ]
            },
        },
        "gdelt": {
            "por": {
                "articles": [
                    {
                        "title": "Estudo descarta ivermectina",
                        "url": "https://example.com/art1",
                        "domain": "example.com",
                        "language": "por",
                        "seen_date": "2024-03-10",
                    }
                ]
            },
            "en": {"articles": []},
        },
        "wikipedia": {
            "pt": {
                "results": [
                    {
                        "title": "Ivermectina",
                        "url": "https://pt.wikipedia.org/wiki/Ivermectina",
                        "extract": "A ivermectina é um antiparasitário...",
                    }
                ]
            },
            "en": {"results": []},
        },
        "brazilian_fc": {
            "results": [
                {
                    "title": "Ivermectina não cura COVID-19",
                    "url": "https://lupa.news/check/1",
                    "source": "Agência Lupa",
                    "snippet": "Não há evidências...",
                    "date": "2024-01-20",
                }
            ]
        },
    }


def _sample_modules() -> list[dict]:
    """Two sample learning modules for seeding."""
    return [
        {
            "slug": "test-module-one",
            "title": "Módulo de Teste 1",
            "description": "Primeiro módulo de teste",
            "difficulty": "beginner",
            "estimated_minutes": 5,
            "topic": "bias",
            "order_index": 0,
            "sections": [
                {"type": "explanation", "title": "O que é viés?", "content": "Vicariance..."},
                {"type": "quiz", "question": "Qual é um tipo de viés?", "options": ["Confirmação", "Ancoragem"], "correct": 0},
            ],
        },
        {
            "slug": "test-module-two",
            "title": "Módulo de Teste 2",
            "description": "Segundo módulo de teste",
            "difficulty": "intermediate",
            "estimated_minutes": 10,
            "topic": "sources",
            "order_index": 1,
            "sections": [
                {"type": "explanation", "title": "Fontes", "content": "Como avaliar..."},
            ],
        },
    ]


# ── Model Tests ────────────────────────────────────────────────────────────────


class TestModels:
    """Test ORM model creation and constraints."""

    def test_conversation_created_with_defaults(self, db_session):
        conv = Conversation(pseudonymous_user_id="abc123", platform="web")
        db_session.add(conv)
        db_session.commit()

        assert conv.id is not None
        assert len(conv.id) == 36  # UUID format
        assert conv.platform == "web"
        assert conv.interaction_count == 0
        assert conv.transitioned_to_web is False
        assert conv.started_at is not None

    def test_submission_linked_to_conversation(self, db_session):
        conv = Conversation(pseudonymous_user_id="user1", platform="telegram")
        db_session.add(conv)
        db_session.flush()

        sub = Submission(
            conversation_id=conv.id,
            content_type="text",
            content_hash="abcdef1234567890",
        )
        db_session.add(sub)
        db_session.commit()

        assert sub.conversation_id == conv.id
        assert sub.analysis_status == "pending"
        assert len(conv.submissions) == 1

    def test_analysis_record_stores_scores(self, db_session):
        sub = Submission(content_type="text", content_hash="hash1")
        db_session.add(sub)
        db_session.flush()

        record = AnalysisRecord(
            submission_id=sub.id,
            content_id="test-id-123",
            risk_overall=68.0,
            risk_level="high",
            confidence=0.72,
            urgency_score=0.3,
            manipulation_score=0.5,
        )
        db_session.add(record)
        db_session.commit()

        fetched = db_session.query(AnalysisRecord).filter_by(content_id="test-id-123").first()
        assert fetched is not None
        assert fetched.risk_overall == 68.0
        assert fetched.risk_level == "high"
        assert fetched.confidence == 0.72

    def test_evidence_linked_to_submission(self, db_session):
        sub = Submission(content_type="link", content_hash="hash2")
        db_session.add(sub)
        db_session.flush()

        ev = Evidence(
            submission_id=sub.id,
            source_type="fact_check",
            source_name="Aos Fatos",
            stance="contradicts",
            is_fact_checker=True,
            fact_check_rating="Falso",
        )
        db_session.add(ev)
        db_session.commit()

        assert len(sub.evidence) == 1
        assert sub.evidence[0].stance == "contradicts"
        assert sub.evidence[0].is_fact_checker is True

    def test_feedback_creation(self, db_session):
        fb = Feedback(
            usefulness_rating=4,
            feeling_after="empowered",
            would_recommend=True,
            content_id="test-fb-123",
        )
        db_session.add(fb)
        db_session.commit()

        assert fb.id is not None
        assert fb.usefulness_rating == 4
        assert fb.would_recommend is True
        assert fb.created_at is not None

    def test_learning_module_and_progress(self, db_session):
        mod = LearningModule(
            slug="test-mod",
            title_pt="Teste",
            content_json='[{"type":"explanation","title":"T","content":"C"}]',
            topic="bias",
        )
        db_session.add(mod)
        db_session.flush()

        progress = UserLearningProgress(
            pseudonymous_user_id="user1",
            module_id=mod.id,
            status="in_progress",
            started_at=datetime.now(UTC),
        )
        db_session.add(progress)
        db_session.commit()

        assert len(mod.progress) == 1
        assert mod.progress[0].status == "in_progress"

    def test_cascade_delete_conversation(self, db_session):
        """Deleting a conversation cascades to submissions and feedback."""
        conv = Conversation(pseudonymous_user_id="del-user", platform="web")
        db_session.add(conv)
        db_session.flush()

        sub = Submission(conversation_id=conv.id, content_type="text", content_hash="del-hash")
        fb = Feedback(conversation_id=conv.id, usefulness_rating=3)
        db_session.add_all([sub, fb])
        db_session.commit()

        assert db_session.query(Submission).count() == 1
        assert db_session.query(Feedback).count() == 1

        db_session.delete(conv)
        db_session.commit()

        assert db_session.query(Submission).count() == 0
        assert db_session.query(Feedback).count() == 0


# ── Repository: save_analysis ──────────────────────────────────────────────────


class TestSaveAnalysis:
    """Test Repository.save_analysis() persistence."""

    def test_persists_full_analysis(self, repo):
        record = repo.save_analysis("cid-001", _sample_analysis())

        assert record.content_id == "cid-001"
        assert record.risk_overall == 68
        assert record.risk_level == "high"
        assert record.confidence == 0.72
        assert record.urgency_score == 0.3
        assert record.manipulation_score == 0.5
        assert record.language == "pt"
        assert record.word_count == 4
        assert record.fc_false == 2
        assert record.fc_mixed == 1
        assert record.fc_true == 0

    def test_creates_submission_with_hash(self, repo):
        repo.save_analysis("cid-002", _sample_analysis())

        sub = repo.session.query(Submission).first()
        assert sub is not None
        assert sub.content_type == "text"
        assert len(sub.content_hash) == 64  # SHA-256
        assert sub.analysis_status == "completed"

    def test_creates_evidence_items(self, repo):
        repo.save_analysis("cid-003", _sample_analysis())

        evidence = repo.session.query(Evidence).all()
        # 2 FC reviews + 1 GDELT + 1 Wikipedia + 1 Brazilian FC = 5
        assert len(evidence) == 5

        fc_items = [e for e in evidence if e.source_type == "fact_check"]
        assert len(fc_items) == 2
        assert all(e.is_fact_checker for e in fc_items)
        assert all(e.stance == "contradicts" for e in fc_items)  # rating_value=1

        gdelt_items = [e for e in evidence if e.source_type == "gdelt"]
        assert len(gdelt_items) == 1

        wiki_items = [e for e in evidence if e.source_type == "wikipedia"]
        assert len(wiki_items) == 1

        br_items = [e for e in evidence if e.source_type == "brazilian_fc"]
        assert len(br_items) == 1

    def test_stores_full_json(self, repo):
        data = _sample_analysis()
        repo.save_analysis("cid-004", data)

        record = repo.session.query(AnalysisRecord).filter_by(content_id="cid-004").first()
        stored = json.loads(record.full_result_json)
        assert stored["query"] == data["query"]
        assert stored["risk_score"]["overall"] == 68

    def test_get_analysis_by_content_id(self, repo):
        repo.save_analysis("cid-005", _sample_analysis())

        result = repo.get_analysis_by_content_id("cid-005")
        assert result is not None
        assert result["query"] == "Ivermectina cura COVID-19"

    def test_get_analysis_not_found(self, repo):
        result = repo.get_analysis_by_content_id("nonexistent")
        assert result is None

    def test_rollback_on_error(self, repo):
        """Duplicate content_id raises and rolls back."""
        repo.save_analysis("cid-dup", _sample_analysis())
        with pytest.raises(Exception):
            repo.save_analysis("cid-dup", _sample_analysis())
        # Session should still be usable after rollback
        assert repo.session.query(AnalysisRecord).filter_by(content_id="cid-dup").count() == 1


# ── Repository: Balance of Evidence ───────────────────────────────────────────


class TestBalanceOfEvidence:
    """Test Repository.get_balance_data()."""

    def test_balance_data_structure(self, repo):
        repo.save_analysis("bal-001", _sample_analysis())
        balance = repo.get_balance_data("bal-001")

        assert balance is not None
        assert balance["content_id"] == "bal-001"
        assert "balance_score" in balance
        assert "supporting" in balance
        assert "contradicting" in balance
        assert "neutral" in balance
        assert "total_sources" in balance
        assert balance["total_sources"] == 5
        assert balance["risk_level"] == "high"

    def test_balance_score_negative_for_false_claims(self, repo):
        """When most FC reviews rate it false, balance should be negative."""
        repo.save_analysis("bal-002", _sample_analysis())
        balance = repo.get_balance_data("bal-002")

        # Both FC reviews have rating_value=1 (false) → stance="contradicts"
        assert balance["balance_score"] < 0
        assert len(balance["contradicting"]) == 2

    def test_balance_has_fact_checker_verdict(self, repo):
        repo.save_analysis("bal-003", _sample_analysis())
        balance = repo.get_balance_data("bal-003")

        assert balance["fact_checker_verdict"] is not None
        assert "Falso" in balance["fact_checker_verdict"]

    def test_balance_not_found(self, repo):
        result = repo.get_balance_data("nonexistent")
        assert result is None

    def test_evidence_item_fields(self, repo):
        repo.save_analysis("bal-004", _sample_analysis())
        balance = repo.get_balance_data("bal-004")

        # Check a contradicting item has the right structure
        c = balance["contradicting"][0]
        assert "source_name" in c
        assert "source_url" in c
        assert "stance" in c
        assert c["stance"] == "contradicts"
        assert c["is_fact_checker"] is True


# ── Repository: Feedback ──────────────────────────────────────────────────────


class TestFeedback:
    """Test feedback save and summary."""

    def test_save_feedback(self, repo):
        fb = repo.save_feedback(
            content_id="fb-001",
            usefulness_rating=5,
            feeling_after="empowered",
            would_recommend=True,
        )
        assert fb.id is not None
        assert fb.usefulness_rating == 5

    def test_feedback_summary_empty(self, repo):
        summary = repo.get_feedback_summary(days=30)
        assert summary["total"] == 0
        assert summary["avg_rating"] == 0

    def test_feedback_summary_with_data(self, repo):
        repo.save_feedback(content_id="fb-s1", usefulness_rating=4, feeling_after="empowered", would_recommend=True)
        repo.save_feedback(content_id="fb-s2", usefulness_rating=5, feeling_after="grateful", would_recommend=True)
        repo.save_feedback(content_id="fb-s3", usefulness_rating=2, feeling_after="confused", would_recommend=False)

        summary = repo.get_feedback_summary(days=30)
        assert summary["total"] == 3
        assert summary["avg_rating"] == pytest.approx(3.67, abs=0.01)
        assert summary["feeling_distribution"]["empowered"] == 1
        assert summary["feeling_distribution"]["grateful"] == 1
        assert summary["feeling_distribution"]["confused"] == 1
        assert summary["would_recommend_pct"] == pytest.approx(66.7, abs=0.1)

    def test_feedback_without_rating(self, repo):
        repo.save_feedback(feeling_after="relieved")
        summary = repo.get_feedback_summary()
        assert summary["total"] == 1
        assert summary["avg_rating"] == 0  # No ratings → 0


# ── Repository: Persistent Analytics ──────────────────────────────────────────


class TestPersistentAnalytics:
    """Test Repository.get_persistent_analytics()."""

    def test_analytics_empty(self, repo):
        result = repo.get_persistent_analytics(days=30)
        assert result["total_analyses"] == 0

    def test_analytics_after_saving(self, repo):
        repo.save_analysis("an-001", _sample_analysis())
        result = repo.get_persistent_analytics(days=30)

        assert result["total_analyses"] == 1
        assert result["by_risk_level"]["high"] == 1
        assert result["by_language"]["pt"] == 1
        assert result["avg_urgency"] == pytest.approx(0.3, abs=0.01)
        assert result["avg_manipulation"] == pytest.approx(0.5, abs=0.01)
        assert result["avg_confidence"] == pytest.approx(0.72, abs=0.01)
        assert result["fc_coverage"] == pytest.approx(1.0, abs=0.01)
        assert result["total_evidence_items"] > 0

    def test_analytics_multiple_analyses(self, repo):
        data1 = _sample_analysis()
        data2 = _sample_analysis()
        data2["risk_score"]["level"] = "critical"
        data2["risk_score"]["overall"] = 90
        data2["nlp"]["urgency"]["score"] = 0.8

        repo.save_analysis("an-002", data1)
        repo.save_analysis("an-003", data2)

        result = repo.get_persistent_analytics(days=30)
        assert result["total_analyses"] == 2
        assert result["by_risk_level"]["high"] == 1
        assert result["by_risk_level"]["critical"] == 1
        assert result["avg_urgency"] == pytest.approx(0.55, abs=0.01)  # (0.3 + 0.8) / 2


# ── Repository: Learning Modules ──────────────────────────────────────────────


class TestLearningModules:
    """Test learning module CRUD and user progress."""

    def test_seed_modules(self, repo):
        count = repo.seed_learning_modules(_sample_modules())
        assert count == 2

        modules = repo.get_all_modules()
        assert len(modules) == 2
        assert modules[0]["slug"] == "test-module-one"
        assert modules[0]["difficulty"] == "beginner"
        assert modules[1]["slug"] == "test-module-two"

    def test_seed_upserts(self, repo):
        """Seeding twice with same slugs updates instead of duplicates."""
        repo.seed_learning_modules(_sample_modules())
        updated = _sample_modules()
        updated[0]["title"] = "Título Atualizado"
        repo.seed_learning_modules(updated)

        modules = repo.get_all_modules()
        assert len(modules) == 2
        assert modules[0]["title"] == "Título Atualizado"

    def test_get_module_by_slug(self, repo):
        repo.seed_learning_modules(_sample_modules())
        mod = repo.get_module_by_slug("test-module-one")

        assert mod is not None
        assert mod["title"] == "Módulo de Teste 1"
        assert mod["topic"] == "bias"
        assert len(mod["content"]) == 2
        assert mod["content"][0]["type"] == "explanation"

    def test_get_module_not_found(self, repo):
        assert repo.get_module_by_slug("nonexistent") is None

    def test_get_all_modules_ordered(self, repo):
        repo.seed_learning_modules(_sample_modules())
        modules = repo.get_all_modules()
        assert modules[0]["order_index"] < modules[1]["order_index"]

    def test_inactive_module_hidden(self, repo):
        repo.seed_learning_modules(_sample_modules())
        # Deactivate first module
        mod = repo.session.query(LearningModule).filter_by(slug="test-module-one").first()
        mod.is_active = False
        repo.session.commit()

        modules = repo.get_all_modules(active_only=True)
        assert len(modules) == 1
        assert modules[0]["slug"] == "test-module-two"

    def test_update_user_progress(self, repo):
        repo.seed_learning_modules(_sample_modules())

        result = repo.update_user_progress(
            pseudonymous_user_id="user-test-1",
            module_slug="test-module-one",
            status="in_progress",
        )
        assert result["status"] == "in_progress"
        assert result["module_slug"] == "test-module-one"

    def test_complete_user_progress_with_score(self, repo):
        repo.seed_learning_modules(_sample_modules())

        repo.update_user_progress(
            pseudonymous_user_id="user-test-2",
            module_slug="test-module-one",
            status="in_progress",
        )
        result = repo.update_user_progress(
            pseudonymous_user_id="user-test-2",
            module_slug="test-module-one",
            status="completed",
            score=0.85,
            quiz_answers={"q1": 0},
        )
        assert result["status"] == "completed"
        assert result["score"] == 0.85

        # Check timestamps
        progress = repo.session.query(UserLearningProgress).filter_by(
            pseudonymous_user_id="user-test-2"
        ).first()
        assert progress.started_at is not None
        assert progress.completed_at is not None
        assert progress.quiz_answers_json is not None

    def test_update_progress_nonexistent_module(self, repo):
        with pytest.raises(ValueError, match="Module not found"):
            repo.update_user_progress("user1", "nonexistent-slug", "in_progress")

    def test_get_user_progress(self, repo):
        repo.seed_learning_modules(_sample_modules())
        repo.update_user_progress("user-p1", "test-module-one", "completed", score=1.0)
        repo.update_user_progress("user-p1", "test-module-two", "in_progress")

        progress = repo.get_user_progress("user-p1")
        assert len(progress) == 2
        statuses = {p["status"] for p in progress}
        assert "completed" in statuses
        assert "in_progress" in statuses


# ── Engine Tests ───────────────────────────────────────────────────────────────


class TestEngine:
    """Test engine configuration."""

    def test_reset_engine(self):
        from src.database.engine import get_engine, reset_engine

        engine1 = get_engine("sqlite:///:memory:")
        assert engine1 is not None
        reset_engine()
        # After reset, next call creates a new engine
        engine2 = get_engine("sqlite:///:memory:")
        assert engine2 is not engine1
        reset_engine()  # Cleanup

    def test_init_db(self):
        from src.database.engine import get_engine, init_db, reset_engine

        reset_engine()
        init_db("sqlite:///:memory:")
        engine = get_engine()
        # Tables should exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "conversations" in tables
        assert "submissions" in tables
        assert "analysis_results" in tables
        assert "evidence" in tables
        assert "feedback" in tables
        assert "learning_modules" in tables
        assert "user_learning_progress" in tables
        reset_engine()  # Cleanup
