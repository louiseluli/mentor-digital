"""
analysis_service.py — Orquestrador de análise de conteúdo (Micro-Batch 3.3 / 12.x)

Responsabilidade única: receber um ConversationContext após o primeiro conteúdo
enviado pelo usuário, disparar TODOS os analisadores em paralelo, e persistir
os resultados em ctx.analysis_results (salvo no Redis pelo session_manager).

Fase 3.1  → Google Fact Check Tools API                    (implementado)
Fase 3.2  → RDAP + VirusTotal + urlscan.io + Open PageRank (implementado)
Fase 3.3  → GDELT DOC API                                  (implementado)
Fase 3.4  → Hugging Face Inference API (NLP)               (stub pronto)
Fase 11.x → Wikipedia API (PT + EN, sem API key)           (implementado)
Fase 12.x → Brazilian FC RSS (Aos Fatos + Agência Lupa)    (implementado)
Fase 12.x → Pontuação multi-dimensional (scoring.py)       (implementado)

Os resultados NÃO são exibidos no bot — são consumidos pela plataforma web (Fase 5).
"""

import asyncio
import logging
import re
from datetime import datetime, UTC

from src.models import ConversationContext
from src.analysis.fact_checker import search_claims, serialize_response
from src.analysis.domain_checker import check_domain, serialize_domain_response
from src.analysis.gdelt import search_articles, serialize_gdelt_response
from src.analysis.nlp import analyze_text, serialize_nlp_result
from src.analysis.wikipedia_api import search_wikipedia
from src.analysis.brazilian_fc import search_brazilian_fc
from src.analysis.scoring import compute_risk_score

logger = logging.getLogger(__name__)


# ── Helpers internos ─────────────────────────────────────────────────────────

def _extract_query(ctx: ConversationContext, max_length: int = 200) -> str:
    """Extrai o melhor texto de busca do conteúdo enviado.

    - Para links, usa a URL completa (analisadores de domínio usarão o URL diretamente).
    - Para texto longo, trunca em max_length caracteres sem cortar palavras.
    - Para imagens/áudio sem legenda, retorna string vazia (sem busca possível).
    """
    content = ctx.content_raw.strip()
    if not content or content.startswith("["):
        return ""
    if len(content) <= max_length:
        return content
    truncated = content[:max_length]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 0 else truncated


def _extract_fc_query(full_query: str, max_length: int = 90) -> str:
    """Extrai query curta focada na afirmação principal para a Google FC API.

    A API retorna melhores resultados com queries curtas (idealmente ≤90 chars)
    porque faz matching semântico de claims — não busca full-text.

    Estratégia: usa a primeira frase do texto, onde geralmente está a afirmação
    central. Se não encontrar pontuação de fim de frase nos primeiros 120 chars,
    trunca em max_length sem cortar palavras.
    """
    if not full_query or len(full_query) <= max_length:
        return full_query
    # Primeira frase: primeiro . ! ? dentro dos primeiros 120 chars
    m = re.search(r"[.!?]", full_query[:120])
    if m and m.start() >= 15:          # frase mínima de 15 chars para ter sentido
        return full_query[:m.start()].strip()
    # Fallback: trunca em max_length sem cortar palavra no meio
    truncated = full_query[:max_length]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 20 else truncated


# ── Analisadores ──────────────────────────────────────────────────────────────

async def _run_fact_check(query: str) -> dict:
    """Google Fact Check Tools API — busca em PT e EN para maior cobertura.

    Usa _extract_fc_query() para obter a primeira frase do texto — a Google FC
    API faz matching semântico de claims e retorna muito mais resultados com
    queries curtas (≤90 chars) do que com parágrafos completos.
    page_size=10 para obter o máximo de resultados permitido pela API.
    """
    from src.analysis.fact_checker import FactCheckResponse

    if not query:
        empty = serialize_response(FactCheckResponse())
        return {"pt": empty, "en": empty}

    fc_query = _extract_fc_query(query)
    logger.debug("FC query: %r (original: %d chars)", fc_query, len(query))

    pt_task = asyncio.create_task(search_claims(fc_query, language_code="pt", page_size=10))
    en_task = asyncio.create_task(search_claims(fc_query, language_code="en", page_size=10))
    pt_result, en_result = await asyncio.gather(pt_task, en_task, return_exceptions=True)

    return {
        "pt": serialize_response(pt_result) if not isinstance(pt_result, Exception)
              else {"query": fc_query, "error": str(pt_result), "results": []},
        "en": serialize_response(en_result) if not isinstance(en_result, Exception)
              else {"query": fc_query, "error": str(en_result), "results": []},
    }


async def _run_domain_analysis(url: str) -> dict:
    """RDAP + VirusTotal + urlscan.io + Open PageRank em paralelo."""
    result = await check_domain(url)
    return serialize_domain_response(result)


async def _run_nlp(ctx: ConversationContext) -> dict:
    """Analisador NLP local — regras ponderadas, multilíngue, sem IO, sem chave de API."""
    result = analyze_text(ctx.content_raw)
    return serialize_nlp_result(result)


async def _run_gdelt(query: str) -> dict:
    """GDELT DOC API — busca em PT e EN em paralelo, sem chave necessária."""
    from src.analysis.gdelt import GDELTResponse

    if not query:
        empty = serialize_gdelt_response(GDELTResponse())
        return {"por": empty, "en": empty}

    por_task = asyncio.create_task(
        search_articles(query, source_language="por")
    )
    en_task = asyncio.create_task(
        search_articles(query, source_language="english")
    )
    por_result, en_result = await asyncio.gather(por_task, en_task, return_exceptions=True)

    return {
        "por": serialize_gdelt_response(por_result) if not isinstance(por_result, Exception)
               else {"query": query, "error": str(por_result), "articles": []},
        "en": serialize_gdelt_response(en_result) if not isinstance(en_result, Exception)
              else {"query": query, "error": str(en_result), "articles": []},
    }


async def _run_wikipedia(query: str) -> dict:
    """Wikipedia API — busca em PT e EN em paralelo, sem chave necessária."""
    if not query:
        return {"pt": {"query": query, "results": [], "error": ""}, "en": {"query": query, "results": [], "error": ""}}

    pt_task = asyncio.create_task(search_wikipedia(query, lang="pt"))
    en_task = asyncio.create_task(search_wikipedia(query, lang="en"))
    pt_result, en_result = await asyncio.gather(pt_task, en_task, return_exceptions=True)

    return {
        "pt": pt_result if not isinstance(pt_result, Exception)
              else {"query": query, "error": str(pt_result), "results": []},
        "en": en_result if not isinstance(en_result, Exception)
              else {"query": query, "error": str(en_result), "results": []},
    }


async def _run_brazilian_fc(query: str, redis_client=None) -> dict:
    """Verificadores brasileiros via RSS (Aos Fatos + Agência Lupa) — keyword-match."""
    if not query:
        return {"query": query, "results": [], "error": ""}
    return await search_brazilian_fc(query, redis_client=redis_client)


# ── Orquestrador principal ───────────────────────────────────────────────────

async def analyze_content(ctx: ConversationContext) -> dict:
    """Executa toda a análise disponível para o conteúdo do contexto.

    Fact-check e GDELT rodam em paralelo entre si (e internamente também em paralelo).
    Domain analysis roda adicionalmente se content_type == "link".

    Args:
        ctx: ConversationContext já populado com content_raw e content_type.

    Returns:
        Dict com todos os resultados de análise (JSON-serializável).
        O mesmo dict é mesclado em ctx.analysis_results para persistência.
    """
    query = _extract_query(ctx)
    is_link = ctx.content_type == "link"
    started_at = datetime.now(UTC).isoformat()

    logger.info(
        "Análise iniciada | content_id=%s | type=%s | query=%r",
        ctx.content_id, ctx.content_type, query[:80] if query else "",
    )

    # ── Todas as fontes em paralelo: FC, GDELT, NLP, Wikipedia, Brazilian FC ──
    redis_client = None
    try:
        from src.session_manager import SessionManager
        import os
        redis_client = SessionManager.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0")
        ).redis
    except Exception:
        pass  # sem cache — continua sem Redis

    fc_task = asyncio.create_task(_run_fact_check(query))
    gdelt_task = asyncio.create_task(_run_gdelt(query))
    nlp_task = asyncio.create_task(_run_nlp(ctx))
    wiki_task = asyncio.create_task(_run_wikipedia(query))
    br_fc_task = asyncio.create_task(_run_brazilian_fc(query, redis_client))
    fc_outcome, gdelt_outcome, nlp_outcome, wiki_outcome, br_fc_outcome = await asyncio.gather(
        fc_task, gdelt_task, nlp_task, wiki_task, br_fc_task, return_exceptions=True
    )

    fact_check = (
        fc_outcome if not isinstance(fc_outcome, Exception)
        else {"error": str(fc_outcome), "results": []}
    )
    gdelt = (
        gdelt_outcome if not isinstance(gdelt_outcome, Exception)
        else {"error": str(gdelt_outcome), "articles": []}
    )
    nlp = (
        nlp_outcome if not isinstance(nlp_outcome, Exception)
        else {"error": str(nlp_outcome)}
    )
    wikipedia = (
        wiki_outcome if not isinstance(wiki_outcome, Exception)
        else {"error": str(wiki_outcome), "pt": {"results": []}, "en": {"results": []}}
    )
    brazilian_fc = (
        br_fc_outcome if not isinstance(br_fc_outcome, Exception)
        else {"error": str(br_fc_outcome), "results": []}
    )

    # ── Fase 3.2: Domain Analysis (apenas para links) ─────────────────────────
    domain = None
    if is_link and query:
        try:
            domain = await _run_domain_analysis(query)
        except Exception as exc:
            logger.error("Domain analysis falhou: %s", exc)
            domain = {"error": str(exc)}

    results: dict = {
        "analyzed_at": started_at,
        "query": query,
        "fact_check": fact_check,
        "gdelt": gdelt,
        "nlp": nlp,
        "wikipedia": wikipedia,
        "brazilian_fc": brazilian_fc,
    }
    if domain is not None:
        results["domain"] = domain

    # ── Pontuação multi-dimensional (síncrono, rápido) ─────────────────────────
    try:
        results["risk_score"] = compute_risk_score(results)
    except Exception as exc:
        logger.error("Risk scoring falhou: %s", exc)
        results["risk_score"] = None

    ctx.analysis_results.update(results)

    total_fc = (
        len(fact_check.get("pt", {}).get("results", []))
        + len(fact_check.get("en", {}).get("results", []))
    )
    total_gdelt = (
        len(gdelt.get("por", {}).get("articles", []))
        + len(gdelt.get("en", {}).get("articles", []))
    )
    total_wiki = (
        len(wikipedia.get("pt", {}).get("results", []))
        + len(wikipedia.get("en", {}).get("results", []))
    )
    total_br_fc = len(brazilian_fc.get("results", []))
    risk = results.get("risk_score") or {}
    logger.info(
        "Análise concluída | content_id=%s | fc=%d | gdelt=%d | wiki=%d | br_fc=%d | "
        "risk=%.2f(%s) | domain=%s | lang=%s",
        ctx.content_id, total_fc, total_gdelt, total_wiki, total_br_fc,
        risk.get("overall", 0), risk.get("level", "?"),
        domain.get("domain", "") if domain else "—",
        nlp.get("language", "?"),
    )

    return results
