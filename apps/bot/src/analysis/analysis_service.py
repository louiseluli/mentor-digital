"""
analysis_service.py — Orquestrador de análise de conteúdo (Micro-Batch 3.3)

Responsabilidade única: receber um ConversationContext após o primeiro conteúdo
enviado pelo usuário, disparar TODOS os analisadores em paralelo, e persistir
os resultados em ctx.analysis_results (salvo no Redis pelo session_manager).

Fase 3.1  → Google Fact Check Tools API                    (implementado)
Fase 3.2  → RDAP + VirusTotal + urlscan.io + Open PageRank (implementado)
Fase 3.3  → GDELT DOC API                                  (implementado)
Fase 3.4  → Hugging Face Inference API (NLP)               (stub pronto)

Os resultados NÃO são exibidos no bot — são consumidos pela plataforma web (Fase 5).
"""

import asyncio
import logging
from datetime import datetime, UTC

from src.models import ConversationContext
from src.analysis.fact_checker import search_claims, serialize_response
from src.analysis.domain_checker import check_domain, serialize_domain_response
from src.analysis.gdelt import search_articles, serialize_gdelt_response
from src.analysis.nlp import analyze_text, serialize_nlp_result

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


# ── Analisadores ──────────────────────────────────────────────────────────────

async def _run_fact_check(query: str) -> dict:
    """Google Fact Check Tools API — busca em PT e EN para maior cobertura."""
    from src.analysis.fact_checker import FactCheckResponse

    if not query:
        empty = serialize_response(FactCheckResponse())
        return {"pt": empty, "en": empty}

    pt_task = asyncio.create_task(search_claims(query, language_code="pt"))
    en_task = asyncio.create_task(search_claims(query, language_code="en"))
    pt_result, en_result = await asyncio.gather(pt_task, en_task, return_exceptions=True)

    return {
        "pt": serialize_response(pt_result) if not isinstance(pt_result, Exception)
              else {"query": query, "error": str(pt_result), "results": []},
        "en": serialize_response(en_result) if not isinstance(en_result, Exception)
              else {"query": query, "error": str(en_result), "results": []},
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

    # ── Fase 3.1 + 3.3 + 3.4 em paralelo: Fact Check, GDELT e NLP ───────────
    fc_task = asyncio.create_task(_run_fact_check(query))
    gdelt_task = asyncio.create_task(_run_gdelt(query))
    nlp_task = asyncio.create_task(_run_nlp(ctx))
    fc_outcome, gdelt_outcome, nlp_outcome = await asyncio.gather(
        fc_task, gdelt_task, nlp_task, return_exceptions=True
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
    }
    if domain is not None:
        results["domain"] = domain

    ctx.analysis_results.update(results)

    total_fc = (
        len(fact_check.get("pt", {}).get("results", []))
        + len(fact_check.get("en", {}).get("results", []))
    )
    total_gdelt = (
        len(gdelt.get("por", {}).get("articles", []))
        + len(gdelt.get("en", {}).get("articles", []))
    )
    logger.info(
        "Análise concluída | content_id=%s | fc_hits=%d | gdelt_articles=%d | domain=%s | nlp_lang=%s",
        ctx.content_id, total_fc, total_gdelt,
        domain.get("domain", "") if domain else "—",
        nlp.get("language", "?"),
    )

    return results
