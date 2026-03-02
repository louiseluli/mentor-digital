"""
scoring.py — Pontuação de risco multi-dimensional (Fase 12.x)

Combina quatro dimensões para um score geral de risco:
  1. Linguística  — urgência, manipulação, proporção de maiúsculas (NLP local)
  2. Fact-checks  — vereditos encontrados pelas agências (Google FC + IFCN)
  3. Cobertura    — presença em GDELT, Wikipedia e verificadores brasileiros
  4. Claim × No-FC — boost when many claims but no fact-checks back them

Algoritmo:
  if fc_data:  overall = linguistic×0.25 + factcheck×0.65 + (1−coverage)×0.10
  else:        overall = linguistic×0.55 + claim_penalty×0.15 + (1−coverage×0.30)×0.30
               Floors: manipulation≥0.30 → min 0.40; manipulation≥0.50 → min 0.55

Confiança: 0.30 (base) + 0.40 (se FC disponível) + coverage×0.30

Tabela de vereditos FC (Google rating_value 1-7):
  1–2 → Falso      (score 1.0)
  3–4 → Misto      (score 0.5)
  5–7 → Verdadeiro (score 0.1)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ── Helpers internos ──────────────────────────────────────────────────────────

def _linguistic_risk(nlp: dict) -> float:
    """Risco linguístico baseado em urgência, manipulação e maiúsculas."""
    urgency = nlp.get("urgency", {}).get("score", 0.0)
    manip = nlp.get("manipulation", {}).get("score", 0.0)
    caps = nlp.get("caps_ratio", 0.0)
    caps_boost = 0.15 if caps > 0.20 else 0.0
    return min(1.0, urgency * 0.35 + manip * 0.50 + caps_boost)


def _rating_to_risk(rating_value: int) -> float:
    """Converte rating_value Google FC (1–7) em sinal de risco (0–1)."""
    if rating_value <= 0:
        return 0.5   # desconhecido
    if rating_value <= 2:
        return 1.0   # Falso
    if rating_value <= 4:
        return 0.65  # Misto / Enganoso
    return 0.1       # Verdadeiro


# Termos verificados via text_rating (quando rating_value=0)
_MIXED_TERMS = {
    "enganoso", "misleading", "missing context", "sem contexto",
    "distorcido", "exagerado", "parcialmente", "misto", "mixed",
    "out of context", "fora de contexto", "descontextualizado", "parcial",
}
_FALSE_TERMS = {
    "falso", "false", "incorrect", "incorreto", "errado", "wrong",
    "mentira", "fake", "inverídico", "infundado",
}
_TRUE_TERMS = {
    "verdadeiro", "true", "correto", "correct", "verdade",
    "procedente", "confirmado", "verified", "verídico",
}


def _text_to_category(text_rating: str) -> str | None:
    """Mapeia text_rating → 'false'|'mixed'|'true'|None quando rating_value=0.

    Verifica misto ANTES de falso porque 'enganoso' não é 'falso'.
    """
    t = text_rating.lower().strip()
    if not t:
        return None
    for term in _MIXED_TERMS:
        if term in t:
            return "mixed"
    for term in _FALSE_TERMS:
        if term in t:
            return "false"
    for term in _TRUE_TERMS:
        if term in t:
            return "true"
    return None


def _factcheck_signal(fc_results: list) -> tuple[float, str, dict]:
    """
    Calcula sinal de risco a partir dos vereditos encontrados.

    Aplica floors progressivos quando vereditos falsos dominam:
      ≥1 Falso             → signal ≥ 0.75
      ≥2 Falsos            → signal ≥ 0.85
      Falsos ≥ Mistos      → signal ≥ 0.90
      ≥3 Falsos            → signal ≥ 0.92

    Returns:
        (signal: float, verdict_key: str, breakdown: dict)
    """
    if not fc_results:
        return 0.5, "no_data", {"total": 0, "false": 0, "mixed": 0, "true": 0}

    false_count = 0
    mixed_count = 0
    true_count = 0
    risk_sum = 0.0

    for claim in fc_results:
        for review in claim.get("reviews", []):
            rv = review.get("rating_value", 0)
            if rv > 0:
                # Caminho normal: rating numérico disponível
                risk_sum += _rating_to_risk(rv)
                if rv <= 2:
                    false_count += 1
                elif rv <= 4:
                    mixed_count += 1
                else:
                    true_count += 1
            else:
                # Fallback: interpretar text_rating quando rating_value=0
                category = _text_to_category(review.get("text_rating", ""))
                if category == "false":
                    risk_sum += 1.0
                    false_count += 1
                elif category == "mixed":
                    risk_sum += 0.65
                    mixed_count += 1
                elif category == "true":
                    risk_sum += 0.1
                    true_count += 1
                # Sem categoria reconhecível → não conta no sinal

    review_count = false_count + mixed_count + true_count
    if review_count == 0:
        # FC encontrados mas nenhum com veredito legível → inconclusivo
        return 0.5, "no_clear_verdict", {"total": len(fc_results), "false": 0, "mixed": 0, "true": 0}

    signal = risk_sum / review_count

    # Floors progressivos quando "Falso" aparece — agências dizem que é mentira
    if false_count >= 1:
        signal = max(signal, 0.75)
    if false_count >= 2:
        signal = max(signal, 0.85)
    if false_count >= 1 and false_count >= mixed_count:
        signal = max(signal, 0.90)
    if false_count >= 3:
        signal = max(signal, 0.92)

    # Veredito dominante
    if false_count > 0:
        verdict = "verified_false"
    elif mixed_count > 0 and true_count == 0:
        verdict = "mixed"
    elif true_count > 0 and false_count == 0 and mixed_count == 0:
        verdict = "verified_true"
    else:
        verdict = "no_clear_verdict"

    breakdown = {
        "total": len(fc_results),
        "false": false_count,
        "mixed": mixed_count,
        "true": true_count,
    }
    return min(1.0, signal), verdict, breakdown


def _coverage_score(gdelt: dict, wiki: dict, br_fc: list) -> float:
    """
    Mede o quanto o conteúdo está coberto por fontes confiáveis.
    Alta cobertura = mais contexto disponível (sinal ambíguo sozinho).
    """
    gdelt_count = (
        len(gdelt.get("por", {}).get("articles", []))
        + len(gdelt.get("en", {}).get("articles", []))
    )
    wiki_count = (
        len(wiki.get("pt", {}).get("results", []))
        + len(wiki.get("en", {}).get("results", []))
    )
    br_count = len(br_fc)

    # GDELT: até 20 artigos → contribui até 0.50
    # Wikipedia: até 4 artigos → contribui até 0.25
    # Brazilian FC: até 5 artigos → contribui até 0.25
    score = (
        min(gdelt_count, 20) / 20 * 0.50
        + min(wiki_count, 4) / 4 * 0.25
        + min(br_count, 5) / 5 * 0.25
    )
    return min(1.0, score)


# ── Função pública ────────────────────────────────────────────────────────────

LEVEL_LABELS = {
    "low": "Baixo risco",
    "moderate": "Risco moderado",
    "high": "Alto risco",
    "critical": "Risco crítico",
}

VERDICT_PT = {
    "verified_false": "Verificado como falso por agências de fact-check",
    "mixed": "Avaliações mistas — alguns itens contestados",
    "verified_true": "Verificado como verdadeiro",
    "no_clear_verdict": "Verificado, mas sem classificação clara",
    "no_data": "Sem verificações específicas encontradas",
}


def compute_risk_score(analysis: dict) -> dict:
    """Calcula pontuação de risco multi-dimensional a partir dos resultados de análise.

    Args:
        analysis: dict completo retornado por analyze_content() — inclui
                  'nlp', 'fact_check', 'gdelt', 'wikipedia', 'brazilian_fc'.

    Returns:
        Dict com:
          overall (0–1), level, verdict, dimensions, confidence,
          fc_verdict_breakdown, verdict_pt (string em português).
    """
    nlp = analysis.get("nlp", {})
    fact_check = analysis.get("fact_check", {})
    gdelt = analysis.get("gdelt", {})
    wiki = analysis.get("wikipedia", {})
    br_fc_results = analysis.get("brazilian_fc", {}).get("results", [])

    all_fc_results = (
        fact_check.get("pt", {}).get("results", [])
        + fact_check.get("en", {}).get("results", [])
    )

    linguistic = _linguistic_risk(nlp)
    fc_signal, verdict, breakdown = _factcheck_signal(all_fc_results)
    coverage = _coverage_score(gdelt, wiki, br_fc_results)

    has_fc = bool(all_fc_results)

    # ── Claim penalty: high claims + no FC = unverified scary claims ──────
    claim_score = nlp.get("claim", {}).get("score", 0.0)
    manip_score = nlp.get("manipulation", {}).get("score", 0.0)
    urgency_score = nlp.get("urgency", {}).get("score", 0.0)
    # claim_penalty ranges 0-1: higher when many claims remain unchecked
    claim_penalty = claim_score * 0.70 + manip_score * 0.30

    if has_fc:
        overall = linguistic * 0.25 + fc_signal * 0.65 + (1 - coverage) * 0.10
        # Floor: se agências confirmaram como falso, nunca classificar abaixo de "high"
        if verdict == "verified_false":
            overall = max(overall, 0.65)
        elif verdict == "mixed":
            overall = max(overall, 0.40)
    else:
        # Sem FC: sinal linguístico mais pesado + claim penalty + cobertura
        overall = linguistic * 0.60 + claim_penalty * 0.15 + (1 - coverage) * 0.25

        # Floors: when manipulation is detected, don't let score drop too low
        # These catch the case where a text uses conspiracy language but has
        # low urgency (no "URGENTE", no "compartilhe") — still suspicious
        if manip_score >= 0.50:
            overall = max(overall, 0.55)
        elif manip_score >= 0.30:
            overall = max(overall, 0.40)

        # Combined signal boost: urgency + manipulation together = stronger signal
        if urgency_score >= 0.20 and manip_score >= 0.20:
            overall = max(overall, 0.45)

        # Triple signal boost: urgency + manipulation + claims all present
        if urgency_score >= 0.15 and manip_score >= 0.20 and claim_score >= 0.20:
            overall = max(overall, 0.50)

    overall = max(0.0, min(1.0, overall))
    confidence = min(1.0, 0.30 + (0.40 if has_fc else 0.0) + coverage * 0.30)

    if overall < 0.25:
        level = "low"
    elif overall < 0.50:
        level = "moderate"
    elif overall < 0.75:
        level = "high"
    else:
        level = "critical"

    # Override: verified_false com múltiplos vereditos → no mínimo "high"
    if verdict == "verified_false" and breakdown.get("false", 0) >= 2:
        if level in ("low", "moderate"):
            level = "high"

    result = {
        "overall": round(overall, 3),
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "verdict": verdict,
        "verdict_pt": VERDICT_PT[verdict],
        "dimensions": {
            "linguistic": round(linguistic, 3),
            "factcheck": round(fc_signal, 3) if has_fc else None,
            "coverage": round(coverage, 3),
            "claim_penalty": round(claim_penalty, 3) if not has_fc else None,
        },
        "confidence": round(confidence, 3),
        "fc_verdict_breakdown": breakdown,
    }

    logger.debug(
        "Risk score | overall=%.2f | level=%s | verdict=%s | confidence=%.2f",
        overall, level, verdict, confidence,
    )
    return result
