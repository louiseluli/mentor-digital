"""
test_analytics.py — Testes do módulo de analytics anonimizado (Micro-Batch 8.2)

Seções:
  1. AnalyticsEvent.from_analysis() — score composto, risk_level, flags FC/GDELT
  2. record_event()                 — persistência no Redis (fakeredis)
  3. get_summary()                  — agregação, filtro de período, cobertura
"""

import json
import os
import sys
import time

import fakeredis
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper")
os.environ.setdefault("ANALYTICS_PEPPER", "test_analytics_pepper")

from src.analytics import (
    AnalyticsEvent,
    _ANALYTICS_KEY,
    _composite_score,
    _risk_level,
    get_summary,
    record_event,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_results(
    urgency: float = 0.1,
    manipulation: float = 0.1,
    claim: float = 0.1,
    language: str = "pt",
    word_count: int = 10,
    fc_results: list | None = None,
    gdelt_articles: list | None = None,
) -> dict:
    """Constrói dict de resultados de análise compatível com analyze_content()."""
    return {
        "nlp": {
            "language": language,
            "word_count": word_count,
            "caps_ratio": 0.0,
            "error": "",
            "urgency": {"score": urgency, "evidence": []},
            "claim": {"score": claim, "evidence": []},
            "manipulation": {"score": manipulation, "evidence": []},
        },
        "fact_check": {
            "pt": {"results": fc_results or [], "error": ""},
            "en": {"results": [], "error": ""},
        },
        "gdelt": {
            "por": {"articles": gdelt_articles or [], "error": ""},
            "en": {"articles": [], "error": ""},
        },
    }


@pytest.fixture
def redis():
    return fakeredis.FakeRedis()


# ── 1. AnalyticsEvent.from_analysis() ─────────────────────────────────────────


def test_composite_formula():
    """urgency×0.4 + manipulation×0.6 está correto."""
    assert _composite_score(1.0, 0.0) == pytest.approx(0.4)
    assert _composite_score(0.0, 1.0) == pytest.approx(0.6)
    assert _composite_score(0.5, 0.5) == pytest.approx(0.5)


def test_risk_level_low():
    assert _risk_level(0.0) == "low"
    assert _risk_level(0.24) == "low"


def test_risk_level_moderate():
    assert _risk_level(0.25) == "moderate"
    assert _risk_level(0.49) == "moderate"


def test_risk_level_high():
    assert _risk_level(0.50) == "high"
    assert _risk_level(0.74) == "high"


def test_risk_level_critical():
    assert _risk_level(0.75) == "critical"
    assert _risk_level(1.0) == "critical"


def test_from_analysis_risk_level_low():
    results = _make_results(urgency=0.1, manipulation=0.1)
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    assert event.risk_level == "low"


def test_from_analysis_risk_level_critical():
    results = _make_results(urgency=1.0, manipulation=1.0)
    event = AnalyticsEvent.from_analysis("whatsapp", "link", results)
    assert event.risk_level == "critical"


def test_from_analysis_has_fact_check_true():
    fc = [{"text": "Afirmação falsa", "claimant": "Portal X", "claim_date": "", "reviews": []}]
    results = _make_results(fc_results=fc)
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    assert event.has_fact_check is True


def test_from_analysis_has_fact_check_false():
    results = _make_results(fc_results=[])
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    assert event.has_fact_check is False


def test_from_analysis_has_gdelt_true():
    articles = [{"url": "http://g.com", "title": "Artigo", "domain": "g.com",
                 "language": "por", "source_country": "BR", "seen_date": "", "social_image": ""}]
    results = _make_results(gdelt_articles=articles)
    event = AnalyticsEvent.from_analysis("whatsapp", "text", results)
    assert event.has_gdelt is True


def test_from_analysis_has_gdelt_false():
    results = _make_results(gdelt_articles=[])
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    assert event.has_gdelt is False


def test_from_analysis_fields():
    """Campos básicos são preenchidos corretamente."""
    results = _make_results(urgency=0.3, manipulation=0.5, language="en", word_count=25)
    event = AnalyticsEvent.from_analysis("whatsapp", "link", results)
    assert event.platform == "whatsapp"
    assert event.content_type == "link"
    assert event.language == "en"
    assert event.word_count == 25
    assert event.urgency_score == pytest.approx(0.3, abs=0.001)
    assert event.manipulation_score == pytest.approx(0.5, abs=0.001)
    assert event.event_id != ""


# ── 2. record_event() ──────────────────────────────────────────────────────────


def test_record_event_stores_in_redis(redis):
    results = _make_results()
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    record_event(event, redis)
    count = redis.zcard(_ANALYTICS_KEY)
    assert count == 1


def test_record_event_stores_correct_data(redis):
    results = _make_results(urgency=0.8, manipulation=0.9)
    event = AnalyticsEvent.from_analysis("whatsapp", "link", results)
    record_event(event, redis)
    entries = redis.zrangebyscore(_ANALYTICS_KEY, "-inf", "+inf")
    assert len(entries) == 1
    stored = json.loads(entries[0])
    assert stored["platform"] == "whatsapp"
    assert stored["content_type"] == "link"
    assert stored["risk_level"] == "critical"


def test_record_event_silences_exception():
    """Erros do Redis não propagam — record_event retorna None silenciosamente."""

    class BrokenRedis:
        def zadd(self, *a, **kw):
            raise ConnectionError("Redis off")

        def zremrangebyrank(self, *a, **kw):
            pass

    event = AnalyticsEvent.from_analysis("telegram", "text", _make_results())
    # Não deve lançar exceção
    record_event(event, BrokenRedis())


# ── 3. get_summary() ───────────────────────────────────────────────────────────


def test_get_summary_empty(redis):
    result = get_summary(redis, days=30)
    assert result["total"] == 0
    assert result["period_days"] == 30


def test_get_summary_total_count(redis):
    for _ in range(5):
        event = AnalyticsEvent.from_analysis("telegram", "text", _make_results())
        record_event(event, redis)
    summary = get_summary(redis, days=30)
    assert summary["total"] == 5


def test_get_summary_distributions(redis):
    for _ in range(3):
        record_event(
            AnalyticsEvent.from_analysis("telegram", "text", _make_results(urgency=0.1, manipulation=0.1)),
            redis,
        )
    for _ in range(2):
        record_event(
            AnalyticsEvent.from_analysis("whatsapp", "link", _make_results(urgency=0.1, manipulation=0.1)),
            redis,
        )
    summary = get_summary(redis, days=30)
    assert summary["by_platform"]["telegram"] == 3
    assert summary["by_platform"]["whatsapp"] == 2
    assert summary["by_content_type"]["text"] == 3
    assert summary["by_content_type"]["link"] == 2


def test_get_summary_period_filter(redis):
    """Evento com timestamp antigo não aparece em days=1."""
    old_event = AnalyticsEvent.from_analysis("telegram", "text", _make_results())
    old_event = AnalyticsEvent(
        **{**old_event.__dict__, "timestamp": time.time() - 3 * 86_400}
    )
    record_event(old_event, redis)

    recent_event = AnalyticsEvent.from_analysis("telegram", "text", _make_results())
    record_event(recent_event, redis)

    summary = get_summary(redis, days=1)
    assert summary["total"] == 1


def test_get_summary_fact_check_coverage(redis):
    fc = [{"text": "claim", "claimant": "X", "claim_date": "", "reviews": []}]
    for _ in range(3):
        record_event(
            AnalyticsEvent.from_analysis("telegram", "text", _make_results(fc_results=fc)),
            redis,
        )
    for _ in range(2):
        record_event(
            AnalyticsEvent.from_analysis("telegram", "text", _make_results(fc_results=[])),
            redis,
        )
    summary = get_summary(redis, days=30)
    assert summary["fact_check_coverage"] == pytest.approx(0.6)
