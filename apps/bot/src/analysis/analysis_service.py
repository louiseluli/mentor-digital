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
from src.analysis.google_news import search_google_news
from src.analysis.newsapi import search_newsapi
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


def _extract_fc_query(full_query: str) -> str:
    """Extrai query curta focada no TÓPICO para a Google FC API.

    A API faz matching semântico de claims e retorna melhores resultados com
    3-5 palavras-chave de tópico (e.g. 'vacinas autismo crianças').
    Numbers/dates are removed — they make queries too specific and miss
    broader fact-checks about the same topic.
    """
    if not full_query:
        return full_query
    # FC API: content words first (vacinas, autismo), then proper nouns (Harvard).
    # Proper nouns are often attribution that dilute semantic claim matching.
    kw = _extract_keywords(full_query, max_words=10)
    words = [w for w in kw.split() if not w.replace("%", "").replace(",", "").replace(".", "").isdigit()]
    # Move lowercase words (content) before uppercase (proper nouns)
    content = [w for w in words if w[0].islower()]
    proper = [w for w in words if w[0].isupper()]
    reordered = content + proper
    return " ".join(reordered[:4]) if reordered else kw


# Stopwords PT + EN que não agregam à busca
_PT_STOPWORDS = {
    # ── Português ──
    "a", "à", "ao", "aos", "as", "às", "com", "como", "da", "das", "de",
    "do", "dos", "e", "é", "em", "entre", "esse", "essa", "este", "esta",
    "eu", "foi", "já", "mais", "mas", "na", "nas", "no", "nos", "não",
    "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por",
    "que", "quem", "se", "seu", "sua", "são", "também", "tem", "um",
    "uma", "vai", "ter", "todo", "toda", "todos", "todas", "muito",
    "ser", "sim", "sobre", "confirmou", "segundo", "devido", "prova",
    "ficar", "dias", "total", "sem", "precedentes", "partir", "estão",
    "após", "ainda", "apenas", "até", "cada", "pode", "qualquer",
    "tipo", "uso", "vez", "hora", "horas", "mês", "ano",
    "está", "estão", "estava", "foram", "seria", "sendo",
    "isso", "isto", "aquilo", "aqui", "ali", "lá",
    "dados", "forma", "parte", "grande", "novo", "nova",
    "real", "coisa", "nunca", "sempre", "outro", "outra",
    # Meses PT — nunca úteis como termos de busca
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    # Palavras genéricas que parecem nomes próprios mas não são entidades
    "terra", "mundo", "país", "brasil", "brasileiro", "brasileiros",
    "brasileira", "estudo", "pesquisa", "científico", "conforme", "afirma",
    # ── English ──
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "up",
    "about", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "each", "every", "no", "some", "such", "than", "too",
    "very", "just", "also", "now", "if", "as", "because", "until", "while",
    "only", "own", "same", "other", "more", "most", "few", "many", "much",
    "confirmed", "according", "says", "said", "reports", "announced",
    "revealed", "claimed", "stated", "told", "showed", "found",
    # Months EN
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}

# Palavras de manipulação/urgência — ruído para buscas, não são entidades
_NOISE_WORDS = {
    # PT
    "urgente", "atenção", "cuidado", "compartilhe", "compartilhar",
    "divulgue", "espalhe", "repasse", "apaguem", "censurem", "deletem",
    "proibir", "escondendo", "esconder", "revelou", "revelar", "preso",
    "antes", "amanhã", "agora", "todos", "ninguém",
    # Palavras dramáticas/sensacionalistas — ruído para buscas
    "escuridão", "caos", "destruição", "apocalipse", "colapso",
    "chocante", "inacreditável", "impressionante", "absurdo",
    # EN
    "urgent", "attention", "warning", "share", "spread", "repost",
    "hiding", "hidden", "hide", "cover-up", "coverup", "censored",
    "banned", "deleted", "removed", "shocking", "unbelievable",
    "incredible", "breaking", "massive", "huge", "devastating",
    "destruction", "chaos", "collapse", "apocalypse",
}

# Palavras genéricas que parecem nomes próprios por estarem capitalizadas
# mas não são entidades únicas — atrapalham buscas semânticas
# Parecem nomes próprios mas são genéricos — tratar como other_terms
_GENERIC_CAPITALIZED = {
    # PT
    "governo", "estado", "presidente", "lei", "reforma",
    "médicos", "cientistas", "pesquisadores",
    # EN
    "government", "governments", "president", "scientists", "doctors",
    "researchers", "officials", "experts", "public", "people",
}


def _extract_keywords(query: str, max_words: int = 6) -> str:
    """Extrai termos-chave do texto para buscas em APIs externas.

    Usado por FC API, Wikipedia, GDELT e Google News. Filtra stopwords,
    palavras de urgência/manipulação, e ALL-CAPS de ênfase (>5 chars).
    Prioriza: acrônimos reais (NASA, OMS), nomes próprios, números.
    """
    if not query or len(query) <= 30:
        return query

    words = query.replace(",", " ").replace(".", " ").split()
    key_terms: list[str] = []
    other_terms: list[str] = []

    for word in words:
        clean = word.strip(".,;:!?\"'()[]{}–—")
        if not clean:
            continue
        lower = clean.lower()
        if lower in _PT_STOPWORDS or lower in _NOISE_WORDS:
            continue
        # Generic capitalized words (Terra, Governo, Estudo) → treat as regular
        if lower in _GENERIC_CAPITALIZED:
            other_terms.append(lower)
            continue
        # ALL-CAPS ≤5 chars = likely acronym (NASA, OMS, PIB, COVID)
        # ALL-CAPS >5 chars = likely emphasis shouting → treat as regular word
        if clean.isupper() and len(clean) <= 5 and len(clean) >= 2:
            key_terms.append(clean)
        elif clean.isupper() and len(clean) > 5:
            other_terms.append(lower)
        elif clean[0].isupper() and len(clean) >= 3:
            key_terms.append(clean)
        elif any(c.isdigit() for c in clean):
            key_terms.append(clean)
        else:
            other_terms.append(clean)

    result = key_terms[:max_words]
    remaining = max_words - len(result)
    if remaining > 0:
        result.extend(other_terms[:remaining])

    return " ".join(result) if result else query[:60]


def _simplify_for_wikipedia(query: str, max_words: int = 4) -> str:
    """Extrai termos-chave do texto para busca Wikipedia.

    Content words first (tempestade solar), then proper nouns (NASA).
    Removes numbers — they cause Wikipedia to return unrelated articles.
    """
    keywords = _extract_keywords(query, max_words=max_words + 4)
    words = [w for w in keywords.split() if not w.replace("%", "").replace(",", "").replace(".", "").isdigit()]
    # Content words first — Wikipedia matches topics, not entities
    content = [w for w in words if w[0].islower()]
    proper = [w for w in words if w[0].isupper()]
    reordered = content + proper
    return " ".join(reordered[:max_words]) if reordered else keywords


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
    """GDELT DOC API + Google News RSS + NewsAPI — busca em PT e EN em paralelo.

    Três fontes de notícias rodam em paralelo:
    1. GDELT DOC API (gratuito, sem chave — pode estar fora do ar)
    2. Google News RSS (gratuito, sem chave — fallback confiável)
    3. NewsAPI.org (requer NEWSAPI_KEY — fontes internacionais de qualidade)

    Os resultados são mesclados e desduplicados para o frontend.
    Se uma fonte falhar, as outras garantem cobertura.

    Queries are simplified to keywords for much better results — full
    sentences return few/no matches from news search APIs.
    """
    from src.analysis.gdelt import GDELTResponse

    if not query:
        empty = serialize_gdelt_response(GDELTResponse())
        return {"por": empty, "en": empty}

    # Keyword queries return far more results than full sentences.
    # For news search, proper nouns (NASA, Musk) are more important than
    # content words, so we use _extract_keywords directly (not _simplify_for_wikipedia).
    news_query = _extract_keywords(query, max_words=6)
    # NewsAPI uses AND-matching — shorter queries return far more results
    newsapi_query = _extract_keywords(query, max_words=4)
    logger.debug("News query: %r | NewsAPI: %r (from %d chars)", news_query, newsapi_query, len(query))

    # ── Todas as fontes de notícias em paralelo ────────────────────────────
    por_task = asyncio.create_task(
        search_articles(news_query, source_language="por")
    )
    en_task = asyncio.create_task(
        search_articles(news_query, source_language="english")
    )
    gnews_pt_task = asyncio.create_task(
        search_google_news(news_query, max_results=10, lang="pt-BR")
    )
    gnews_en_task = asyncio.create_task(
        search_google_news(news_query, max_results=10, lang="en-US")
    )
    newsapi_pt_task = asyncio.create_task(
        search_newsapi(newsapi_query, language="pt", max_results=10)
    )
    newsapi_en_task = asyncio.create_task(
        search_newsapi(newsapi_query, language="en", max_results=10)
    )

    por_result, en_result, gnews_pt, gnews_en, newsapi_pt, newsapi_en = await asyncio.gather(
        por_task, en_task, gnews_pt_task, gnews_en_task, newsapi_pt_task, newsapi_en_task,
        return_exceptions=True,
    )

    por_resp = (
        serialize_gdelt_response(por_result) if not isinstance(por_result, Exception)
        else {"query": query, "error": str(por_result), "articles": []}
    )
    en_resp = (
        serialize_gdelt_response(en_result) if not isinstance(en_result, Exception)
        else {"query": query, "error": str(en_result), "articles": []}
    )

    # ── Helper: merge articles into a response with deduplication ──────────
    def _merge_articles(target: dict, source_response, label: str) -> None:
        if isinstance(source_response, Exception) or not source_response.articles:
            return
        serialized = serialize_gdelt_response(source_response)
        new_articles = serialized.get("articles", [])
        existing_keys = set()
        for a in target.get("articles", []):
            key = (a.get("domain", ""), a.get("title", "")[:40])
            existing_keys.add(key)
        added = 0
        for a in new_articles:
            key = (a.get("domain", ""), a.get("title", "")[:40])
            if key not in existing_keys:
                target["articles"].append(a)
                existing_keys.add(key)
                added += 1
        if added:
            logger.debug("%s: merged %d new articles", label, added)
        # Clear error if this source provided results but GDELT failed
        if target.get("error") and new_articles:
            target["error"] = ""

    # Merge Google News PT into PT response, EN into EN response
    _merge_articles(por_resp, gnews_pt, "Google News PT")
    _merge_articles(en_resp, gnews_en, "Google News EN")

    # Merge NewsAPI PT into PT response, EN into EN response
    _merge_articles(por_resp, newsapi_pt, "NewsAPI-PT")
    _merge_articles(en_resp, newsapi_en, "NewsAPI-EN")

    return {
        "por": por_resp,
        "en": en_resp,
    }


async def _run_wikipedia(query: str) -> dict:
    """Wikipedia API — busca em PT e EN em paralelo, sem chave necessária.

    Usa query simplificada (primeiras palavras-chave) para melhorar resultados
    da busca, já que Wikipedia search funciona melhor com termos curtos.
    """
    if not query:
        return {"pt": {"query": query, "results": [], "error": ""}, "en": {"query": query, "results": [], "error": ""}}

    # Wikipedia search works best with short keyword queries, not full sentences.
    # Extract key noun phrases: keep capitalized words, numbers, and quoted terms.
    wiki_query = _simplify_for_wikipedia(query)

    pt_task = asyncio.create_task(search_wikipedia(wiki_query, lang="pt"))
    en_task = asyncio.create_task(search_wikipedia(wiki_query, lang="en"))
    pt_result, en_result = await asyncio.gather(pt_task, en_task, return_exceptions=True)

    return {
        "pt": pt_result if not isinstance(pt_result, Exception)
              else {"query": wiki_query, "error": str(pt_result), "results": []},
        "en": en_result if not isinstance(en_result, Exception)
              else {"query": wiki_query, "error": str(en_result), "results": []},
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
