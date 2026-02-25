"""
analytics.py — Registro anonimizado de eventos de análise (Micro-Batch 8.2)

Armazena eventos no Redis como sorted set ordenado por timestamp Unix.
Nenhum dado pessoal é salvo — apenas métricas de impacto agregadas.

Redis key: mentor:analytics:events  (sorted set, score = timestamp Unix)
Limite:    10 000 eventos mais recentes (ZREMRANGEBYRANK)

Uso:
    event = AnalyticsEvent.from_analysis("telegram", "text", results)
    record_event(event, redis_client)

    summary = get_summary(redis_client, days=30)
"""

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)

_ANALYTICS_KEY = "mentor:analytics:events"
_MAX_EVENTS = 10_000

# Fórmula de risco — mesma do componente evidence-scale.tsx no frontend
_URGENCY_WEIGHT = 0.4
_MANIPULATION_WEIGHT = 0.6

_RISK_THRESHOLDS = [
    (0.25, "low"),
    (0.50, "moderate"),
    (0.75, "high"),
]


def _composite_score(urgency: float, manipulation: float) -> float:
    return urgency * _URGENCY_WEIGHT + manipulation * _MANIPULATION_WEIGHT


def _risk_level(score: float) -> str:
    for threshold, label in _RISK_THRESHOLDS:
        if score < threshold:
            return label
    return "critical"


@dataclass
class AnalyticsEvent:
    event_id: str
    timestamp: float        # Unix timestamp (score no sorted set)
    platform: str           # 'telegram' | 'whatsapp'
    content_type: str       # 'text' | 'link' | 'image' | 'video' | 'audio'
    language: str           # detectado pelo NLP (ex: 'pt', 'en')
    risk_level: str         # 'low' | 'moderate' | 'high' | 'critical'
    urgency_score: float    # 0.0–1.0
    manipulation_score: float
    claim_score: float
    has_fact_check: bool    # True se FC retornou ≥1 resultado
    has_gdelt: bool         # True se GDELT retornou ≥1 artigo
    word_count: int

    @classmethod
    def from_analysis(
        cls,
        platform: str,
        content_type: str,
        results: dict,
    ) -> "AnalyticsEvent":
        """Constrói evento a partir do dict retornado por analyze_content()."""
        nlp = results.get("nlp", {})
        urgency = float(nlp.get("urgency", {}).get("score", 0.0))
        manipulation = float(nlp.get("manipulation", {}).get("score", 0.0))
        claim = float(nlp.get("claim", {}).get("score", 0.0))

        score = _composite_score(urgency, manipulation)

        fc = results.get("fact_check", {})
        has_fc = bool(
            fc.get("pt", {}).get("results") or fc.get("en", {}).get("results")
        )

        gdelt = results.get("gdelt", {})
        has_gdelt = bool(
            gdelt.get("por", {}).get("articles") or gdelt.get("en", {}).get("articles")
        )

        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            platform=platform,
            content_type=content_type,
            language=nlp.get("language", ""),
            risk_level=_risk_level(score),
            urgency_score=round(urgency, 3),
            manipulation_score=round(manipulation, 3),
            claim_score=round(claim, 3),
            has_fact_check=has_fc,
            has_gdelt=has_gdelt,
            word_count=int(nlp.get("word_count", 0)),
        )


def record_event(event: AnalyticsEvent, redis_client) -> None:
    """Persiste evento no sorted set do Redis. Silencia erros para não bloquear o fluxo."""
    try:
        data = json.dumps(asdict(event), ensure_ascii=False)
        redis_client.zadd(_ANALYTICS_KEY, {data: event.timestamp})
        # Mantém apenas os MAX_EVENTS mais recentes (remove os mais antigos)
        redis_client.zremrangebyrank(_ANALYTICS_KEY, 0, -(_MAX_EVENTS + 1))
    except Exception as exc:
        logger.error("Falha ao registrar evento analytics: %s", exc)


def _empty_summary(days: int) -> dict:
    """Retorna estrutura completa com zeros — garante contrato da API mesmo sem eventos."""
    return {
        "total": 0,
        "period_days": days,
        "by_platform": {},
        "by_content_type": {},
        "by_risk_level": {},
        "by_language": {},
        "fact_check_coverage": 0.0,
        "gdelt_coverage": 0.0,
        "avg_urgency": 0.0,
        "avg_manipulation": 0.0,
    }


def get_summary(redis_client, days: int = 30) -> dict:
    """
    Retorna sumário agregado dos últimos N dias.

    Campos retornados:
        total, period_days, by_platform, by_content_type, by_risk_level,
        by_language, fact_check_coverage, gdelt_coverage,
        avg_urgency, avg_manipulation
    """
    try:
        min_score = time.time() - days * 86_400
        raw_entries = redis_client.zrangebyscore(_ANALYTICS_KEY, min_score, "+inf")

        if not raw_entries:
            return _empty_summary(days)

        events: list[AnalyticsEvent] = []
        for raw in raw_entries:
            try:
                data = json.loads(raw)
                events.append(AnalyticsEvent(**data))
            except Exception:
                continue  # ignora entradas corrompidas

        total = len(events)
        if total == 0:
            return _empty_summary(days)

        by_platform: dict[str, int] = {}
        by_content_type: dict[str, int] = {}
        by_risk_level: dict[str, int] = {}
        by_language: dict[str, int] = {}
        fc_hits = 0
        gdelt_hits = 0

        for e in events:
            by_platform[e.platform] = by_platform.get(e.platform, 0) + 1
            by_content_type[e.content_type] = by_content_type.get(e.content_type, 0) + 1
            by_risk_level[e.risk_level] = by_risk_level.get(e.risk_level, 0) + 1
            by_language[e.language] = by_language.get(e.language, 0) + 1
            if e.has_fact_check:
                fc_hits += 1
            if e.has_gdelt:
                gdelt_hits += 1

        return {
            "total": total,
            "period_days": days,
            "by_platform": by_platform,
            "by_content_type": by_content_type,
            "by_risk_level": by_risk_level,
            "by_language": by_language,
            "fact_check_coverage": round(fc_hits / total, 3),
            "gdelt_coverage": round(gdelt_hits / total, 3),
            "avg_urgency": round(sum(e.urgency_score for e in events) / total, 3),
            "avg_manipulation": round(sum(e.manipulation_score for e in events) / total, 3),
        }
    except Exception as exc:
        logger.error("Falha ao calcular sumário analytics: %s", exc)
        return {**_empty_summary(days), "error": str(exc)}
