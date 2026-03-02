"""
database/repository.py — Data access layer for Mentor Digital

All queries go through this class. Keeps business logic clean.
Handles both read and write operations with proper session management.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, UTC

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from src.database.engine import get_session
from src.database.models import (
    AnalysisRecord,
    Conversation,
    Evidence,
    Feedback,
    LearningModule,
    Submission,
    UserLearningProgress,
)

logger = logging.getLogger(__name__)


class Repository:
    """Data access layer — wraps SQLAlchemy session operations."""

    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self):
        if self._session:
            self._session.close()

    # ── Analyses ───────────────────────────────────────────────────────────────

    def save_analysis(self, content_id: str, results: dict, platform: str = "web") -> AnalysisRecord:
        """Persist full analysis results to the database.

        Creates Submission + AnalysisRecord + Evidence items.
        Returns the AnalysisRecord.
        """
        try:
            query_text = results.get("query", "")
            content_hash = hashlib.sha256(query_text.encode("utf-8")).hexdigest()

            # Create submission
            submission = Submission(
                content_type="text",
                content_hash=content_hash,
                analysis_status="completed",
            )
            self.session.add(submission)
            self.session.flush()  # Get submission.id

            # Extract scores
            nlp = results.get("nlp", {})
            risk = results.get("risk_score", {})
            fc = results.get("fact_check", {})
            gdelt = results.get("gdelt", {})
            wiki = results.get("wikipedia", {})
            br_fc = results.get("brazilian_fc", {})

            fc_breakdown = risk.get("fc_verdict_breakdown", {})

            # Count evidence items
            fc_pt = fc.get("pt", {}).get("results", [])
            fc_en = fc.get("en", {}).get("results", [])
            gdelt_por = gdelt.get("por", {}).get("articles", [])
            gdelt_en = gdelt.get("en", {}).get("articles", [])
            wiki_pt = (wiki.get("pt", {}) or {}).get("results", [])
            wiki_en = (wiki.get("en", {}) or {}).get("results", [])
            br_fc_results = (br_fc or {}).get("results", [])

            # Create analysis record
            record = AnalysisRecord(
                submission_id=submission.id,
                content_id=content_id,
                risk_overall=risk.get("overall"),
                risk_level=risk.get("level"),
                risk_verdict=risk.get("verdict"),
                risk_verdict_pt=risk.get("verdict_pt"),
                confidence=risk.get("confidence"),
                urgency_score=float(nlp.get("urgency", {}).get("score", 0)),
                manipulation_score=float(nlp.get("manipulation", {}).get("score", 0)),
                claim_score=float(nlp.get("claim", {}).get("score", 0)),
                language=nlp.get("language", ""),
                word_count=int(nlp.get("word_count", 0)),
                fact_check_count=len(fc_pt) + len(fc_en),
                gdelt_article_count=len(gdelt_por) + len(gdelt_en),
                google_news_count=0,  # Counted from GDELT articles with google_news source
                wikipedia_count=len(wiki_pt) + len(wiki_en),
                brazilian_fc_count=len(br_fc_results),
                fc_false=fc_breakdown.get("false", 0),
                fc_mixed=fc_breakdown.get("mixed", 0),
                fc_true=fc_breakdown.get("true", 0),
                full_result_json=json.dumps(results, ensure_ascii=False),
            )
            self.session.add(record)

            # Save evidence items
            self._save_evidence_items(submission.id, results)

            self.session.commit()
            logger.info("Analysis persisted | content_id=%s", content_id)
            return record

        except Exception as exc:
            self.session.rollback()
            logger.error("Failed to persist analysis | content_id=%s | error=%s", content_id, exc)
            raise

    def _save_evidence_items(self, submission_id: str, results: dict) -> None:
        """Extract and save individual evidence items from analysis results."""
        fc = results.get("fact_check", {})
        gdelt = results.get("gdelt", {})
        wiki = results.get("wikipedia", {})
        br_fc = results.get("brazilian_fc", {})

        # Fact-check evidence
        for lang_key in ("pt", "en"):
            for claim in fc.get(lang_key, {}).get("results", []):
                for review in claim.get("reviews", []):
                    rating_val = review.get("rating_value", 0)
                    if rating_val <= 2:
                        stance = "contradicts"
                    elif rating_val >= 6:
                        stance = "supports"
                    else:
                        stance = "neutral"

                    self.session.add(Evidence(
                        submission_id=submission_id,
                        source_type="fact_check",
                        source_name=review.get("publisher_name", ""),
                        source_url=review.get("url", ""),
                        source_domain=review.get("publisher_site", ""),
                        title=claim.get("text", ""),
                        excerpt=review.get("title", ""),
                        stance=stance,
                        is_fact_checker=True,
                        fact_check_rating=review.get("text_rating", ""),
                        rating_value=rating_val,
                        language=lang_key,
                        published_date=review.get("review_date", ""),
                    ))

        # GDELT/Google News articles
        for lang_key in ("por", "en"):
            for article in gdelt.get(lang_key, {}).get("articles", []):
                self.session.add(Evidence(
                    submission_id=submission_id,
                    source_type="gdelt",
                    source_name=article.get("domain", ""),
                    source_url=article.get("url", ""),
                    source_domain=article.get("domain", ""),
                    title=article.get("title", ""),
                    stance="neutral",  # No stance detection yet for news
                    language=article.get("language", lang_key),
                    published_date=article.get("seen_date", ""),
                ))

        # Wikipedia
        for lang_key in ("pt", "en"):
            wiki_data = (wiki or {}).get(lang_key, {})
            if wiki_data:
                for result in wiki_data.get("results", []):
                    self.session.add(Evidence(
                        submission_id=submission_id,
                        source_type="wikipedia",
                        source_name="Wikipedia",
                        source_url=result.get("url", ""),
                        title=result.get("title", ""),
                        excerpt=result.get("extract", "")[:500],
                        stance="neutral",
                        language=lang_key,
                    ))

        # Brazilian fact-checkers
        for result in (br_fc or {}).get("results", []):
            self.session.add(Evidence(
                submission_id=submission_id,
                source_type="brazilian_fc",
                source_name=result.get("source", ""),
                source_url=result.get("url", ""),
                title=result.get("title", ""),
                excerpt=result.get("snippet", ""),
                stance="neutral",
                is_fact_checker=True,
                published_date=result.get("date", ""),
            ))

    def get_analysis_by_content_id(self, content_id: str) -> dict | None:
        """Retrieve full analysis JSON by content_id."""
        record = self.session.query(AnalysisRecord).filter_by(content_id=content_id).first()
        if record and record.full_result_json:
            return json.loads(record.full_result_json)
        return None

    # ── Balance of Evidence ────────────────────────────────────────────────────

    def get_balance_data(self, content_id: str) -> dict | None:
        """Get evidence items organized for the Balance of Evidence view."""
        record = self.session.query(AnalysisRecord).filter_by(content_id=content_id).first()
        if not record:
            return None

        evidence_items = (
            self.session.query(Evidence)
            .filter_by(submission_id=record.submission_id)
            .all()
        )

        supporting = []
        contradicting = []
        neutral = []

        for e in evidence_items:
            item = {
                "source_name": e.source_name,
                "source_url": e.source_url,
                "source_domain": e.source_domain,
                "source_type": e.source_type,
                "title": e.title,
                "excerpt": e.excerpt,
                "stance": e.stance,
                "credibility_score": e.credibility_score or 0.5,
                "is_fact_checker": e.is_fact_checker,
                "fact_check_rating": e.fact_check_rating,
                "language": e.language,
                "published_date": e.published_date,
            }
            if e.stance == "supports":
                supporting.append(item)
            elif e.stance == "contradicts":
                contradicting.append(item)
            else:
                neutral.append(item)

        # Compute balance score: weighted by credibility
        total_cred = sum(e.credibility_score or 0.5 for e in evidence_items)
        if total_cred > 0:
            stance_values = {"supports": 1.0, "contradicts": -1.0, "neutral": 0.0}
            numerator = sum(
                stance_values.get(e.stance, 0) * (e.credibility_score or 0.5)
                for e in evidence_items
            )
            balance_score = max(-1.0, min(1.0, numerator / total_cred))
        else:
            balance_score = 0.0

        # Fact-checker verdict
        fc_verdict = None
        fc_items = [e for e in evidence_items if e.is_fact_checker and e.fact_check_rating]
        if fc_items:
            ratings = [e.fact_check_rating for e in fc_items]
            fc_verdict = "; ".join(ratings[:3])

        return {
            "content_id": content_id,
            "balance_score": round(balance_score, 3),
            "supporting": supporting,
            "contradicting": contradicting,
            "neutral": neutral,
            "total_sources": len(evidence_items),
            "fact_checker_verdict": fc_verdict,
            "risk_level": record.risk_level,
            "risk_overall": record.risk_overall,
        }

    # ── Feedback ───────────────────────────────────────────────────────────────

    def save_feedback(
        self,
        content_id: str | None = None,
        usefulness_rating: int | None = None,
        feeling_after: str | None = None,
        would_recommend: bool | None = None,
        free_text: str | None = None,
    ) -> Feedback:
        """Save anonymized user feedback."""
        feedback = Feedback(
            content_id=content_id,
            usefulness_rating=usefulness_rating,
            feeling_after=feeling_after,
            would_recommend=would_recommend,
            free_text=free_text,
        )
        self.session.add(feedback)
        self.session.commit()
        return feedback

    def get_feedback_summary(self, days: int = 30) -> dict:
        """Get aggregated feedback metrics."""
        cutoff = datetime.now(UTC).timestamp() - days * 86400
        cutoff_dt = datetime.fromtimestamp(cutoff, tz=UTC)

        feedbacks = (
            self.session.query(Feedback)
            .filter(Feedback.created_at >= cutoff_dt)
            .all()
        )

        if not feedbacks:
            return {
                "total": 0,
                "avg_rating": 0,
                "feeling_distribution": {},
                "would_recommend_pct": 0,
                "period_days": days,
            }

        total = len(feedbacks)
        ratings = [f.usefulness_rating for f in feedbacks if f.usefulness_rating is not None]
        feelings: dict[str, int] = {}
        recommend_yes = 0
        recommend_total = 0

        for f in feedbacks:
            if f.feeling_after:
                feelings[f.feeling_after] = feelings.get(f.feeling_after, 0) + 1
            if f.would_recommend is not None:
                recommend_total += 1
                if f.would_recommend:
                    recommend_yes += 1

        return {
            "total": total,
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "feeling_distribution": feelings,
            "would_recommend_pct": round(recommend_yes / recommend_total * 100, 1) if recommend_total else 0,
            "period_days": days,
        }

    # ── Analytics ──────────────────────────────────────────────────────────────

    def get_persistent_analytics(self, days: int = 30) -> dict:
        """Get analytics from persisted analyses (complements Redis analytics)."""
        cutoff = datetime.now(UTC).timestamp() - days * 86400
        cutoff_dt = datetime.fromtimestamp(cutoff, tz=UTC)

        records = (
            self.session.query(AnalysisRecord)
            .filter(AnalysisRecord.created_at >= cutoff_dt)
            .all()
        )

        if not records:
            return {
                "total_analyses": 0,
                "period_days": days,
                "by_risk_level": {},
                "by_language": {},
                "avg_urgency": 0,
                "avg_manipulation": 0,
                "avg_confidence": 0,
                "fc_coverage": 0,
                "total_evidence_items": 0,
            }

        total = len(records)
        by_risk: dict[str, int] = {}
        by_lang: dict[str, int] = {}
        urgency_sum = 0.0
        manip_sum = 0.0
        conf_sum = 0.0
        fc_count = 0
        total_evidence = 0

        for r in records:
            if r.risk_level:
                by_risk[r.risk_level] = by_risk.get(r.risk_level, 0) + 1
            if r.language:
                by_lang[r.language] = by_lang.get(r.language, 0) + 1
            urgency_sum += r.urgency_score or 0
            manip_sum += r.manipulation_score or 0
            conf_sum += r.confidence or 0
            if r.fact_check_count > 0:
                fc_count += 1
            total_evidence += (
                r.fact_check_count + r.gdelt_article_count +
                r.wikipedia_count + r.brazilian_fc_count
            )

        return {
            "total_analyses": total,
            "period_days": days,
            "by_risk_level": by_risk,
            "by_language": by_lang,
            "avg_urgency": round(urgency_sum / total, 3),
            "avg_manipulation": round(manip_sum / total, 3),
            "avg_confidence": round(conf_sum / total, 3),
            "fc_coverage": round(fc_count / total, 3),
            "total_evidence_items": total_evidence,
        }

    # ── Learning Modules ───────────────────────────────────────────────────────

    def get_all_modules(self, active_only: bool = True) -> list[dict]:
        """Get all learning modules."""
        query = self.session.query(LearningModule).order_by(LearningModule.order_index)
        if active_only:
            query = query.filter_by(is_active=True)
        modules = query.all()
        return [
            {
                "id": m.id,
                "slug": m.slug,
                "title": m.title_pt,
                "description": m.description_pt,
                "difficulty": m.difficulty,
                "estimated_minutes": m.estimated_minutes,
                "topic": m.topic,
                "order_index": m.order_index,
            }
            for m in modules
        ]

    def get_module_by_slug(self, slug: str) -> dict | None:
        """Get a specific module with full content."""
        m = self.session.query(LearningModule).filter_by(slug=slug, is_active=True).first()
        if not m:
            return None
        return {
            "id": m.id,
            "slug": m.slug,
            "title": m.title_pt,
            "description": m.description_pt,
            "content": json.loads(m.content_json),
            "difficulty": m.difficulty,
            "estimated_minutes": m.estimated_minutes,
            "topic": m.topic,
        }

    def seed_learning_modules(self, modules: list[dict]) -> int:
        """Seed learning modules from JSON data. Upserts by slug."""
        count = 0
        for mod in modules:
            existing = self.session.query(LearningModule).filter_by(slug=mod["slug"]).first()
            if existing:
                existing.title_pt = mod["title"]
                existing.description_pt = mod.get("description", "")
                existing.content_json = json.dumps(mod.get("sections", []), ensure_ascii=False)
                existing.difficulty = mod.get("difficulty", "beginner")
                existing.estimated_minutes = mod.get("estimated_minutes", 5)
                existing.topic = mod.get("topic", "general")
                existing.order_index = mod.get("order_index", count)
            else:
                self.session.add(LearningModule(
                    slug=mod["slug"],
                    title_pt=mod["title"],
                    description_pt=mod.get("description", ""),
                    content_json=json.dumps(mod.get("sections", []), ensure_ascii=False),
                    difficulty=mod.get("difficulty", "beginner"),
                    estimated_minutes=mod.get("estimated_minutes", 5),
                    topic=mod.get("topic", "general"),
                    order_index=mod.get("order_index", count),
                ))
            count += 1
        self.session.commit()
        return count

    def get_user_progress(self, pseudonymous_user_id: str) -> list[dict]:
        """Get all learning progress for a user."""
        progress = (
            self.session.query(UserLearningProgress)
            .filter_by(pseudonymous_user_id=pseudonymous_user_id)
            .all()
        )
        return [
            {
                "module_id": p.module_id,
                "status": p.status,
                "score": p.score,
                "started_at": p.started_at.isoformat() if p.started_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in progress
        ]

    def update_user_progress(
        self,
        pseudonymous_user_id: str,
        module_slug: str,
        status: str,
        score: float | None = None,
        quiz_answers: dict | None = None,
    ) -> dict:
        """Update user progress on a module."""
        module = self.session.query(LearningModule).filter_by(slug=module_slug).first()
        if not module:
            raise ValueError(f"Module not found: {module_slug}")

        progress = (
            self.session.query(UserLearningProgress)
            .filter_by(pseudonymous_user_id=pseudonymous_user_id, module_id=module.id)
            .first()
        )

        now = datetime.now(UTC)

        if not progress:
            progress = UserLearningProgress(
                pseudonymous_user_id=pseudonymous_user_id,
                module_id=module.id,
                status=status,
                started_at=now if status == "in_progress" else None,
            )
            self.session.add(progress)
        else:
            progress.status = status

        if status == "in_progress" and not progress.started_at:
            progress.started_at = now
        if status == "completed":
            progress.completed_at = now
        if score is not None:
            progress.score = score
        if quiz_answers is not None:
            progress.quiz_answers_json = json.dumps(quiz_answers, ensure_ascii=False)

        self.session.commit()
        return {
            "module_slug": module_slug,
            "status": progress.status,
            "score": progress.score,
        }
