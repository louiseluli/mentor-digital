"""
newsapi.py — Cliente para NewsAPI.org (fontes de notícias confiáveis, multilíngue)

Endpoint: GET https://newsapi.org/v2/everything
Documentação: https://newsapi.org/docs/endpoints/everything

NewsAPI indexa artigos de 80.000+ fontes globais incluindo Reuters, BBC,
Associated Press, Estadão, Folha, G1, El País, Le Monde, etc.
Requer chave de API (tier dev = 100 req/dia, suficiente para testes).

Uso aqui:
- Busca artigos de notícias confiáveis em PT e EN sobre o conteúdo enviado.
- Complementa GDELT e Google News com fontes internacionais de qualidade.
- Retorna artigos no mesmo formato do GDELT (GDELTArticle) para reuso no frontend.
- Busca em múltiplos idiomas para cobrir fontes que confirmam ou contradizem.

Comportamento seguro:
- Retorna lista vazia se query for vazia, API key for ausente ou API falhar.
- Nunca propaga exceções.
"""

import logging
import os
import re
from datetime import datetime, timedelta, UTC

import httpx

from src.analysis.gdelt import GDELTArticle, GDELTResponse

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
DEFAULT_TIMEOUT = 15.0
MAX_RESULTS = 10
MAX_QUERY_LENGTH = 120

# Map NewsAPI language codes → human-readable labels (same as GDELT/GNews)
_LANG_LABELS = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
}

# Preferred sources for Brazilian context (NewsAPI source IDs)
# These are optional — the free-text search already covers global sources.
PREFERRED_SOURCES_PT = ""
PREFERRED_SOURCES_EN = ""


def _get_api_key() -> str:
    """Retorna a chave da NewsAPI.org a partir de variável de ambiente."""
    return os.getenv("NEWSAPI_KEY", "")


def _clean_query(query: str) -> str:
    """Limpa e trunca a query para uso na NewsAPI."""
    cleaned = re.sub(r'[\[\]"()]', " ", query)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= MAX_QUERY_LENGTH:
        return cleaned
    truncated = cleaned[:MAX_QUERY_LENGTH]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 0 else truncated


def _parse_iso_date(date_str: str) -> str:
    """Normaliza data ISO 8601 retornada pela NewsAPI."""
    if not date_str:
        return ""
    try:
        # NewsAPI returns dates like "2026-02-28T14:22:00Z"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return date_str


def _extract_domain(url: str) -> str:
    """Extrai domínio limpo da URL (ex: 'https://www.estadao.com.br/...' → 'estadao.com.br')."""
    if not url:
        return ""
    try:
        # Remove protocol
        domain = url.split("//", 1)[-1].split("/", 1)[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _source_country_from_lang(language: str) -> str:
    """Infere país de origem a partir do idioma da busca."""
    return {
        "pt": "Brazil",
        "en": "",
        "es": "",
        "fr": "",
        "de": "",
    }.get(language, "")


def _parse_articles(
    data: dict,
    language: str = "pt",
    max_results: int = MAX_RESULTS,
) -> list[GDELTArticle]:
    """Converte resposta da NewsAPI para lista de GDELTArticle."""
    articles: list[GDELTArticle] = []
    raw_articles = data.get("articles", [])

    for item in raw_articles[:max_results]:
        url = item.get("url", "")
        if not url:
            continue

        title = item.get("title", "") or ""
        # NewsAPI sometimes returns "[Removed]" for restricted articles
        if title == "[Removed]" or url == "https://removed.com":
            continue

        source_name = item.get("source", {}).get("name", "")
        domain = _extract_domain(url)
        published_at = _parse_iso_date(item.get("publishedAt", ""))
        image = item.get("urlToImage", "") or ""

        articles.append(GDELTArticle(
            url=url,
            title=title,
            domain=domain or source_name,
            language=_LANG_LABELS.get(language, language),
            source_country=_source_country_from_lang(language),
            seen_date=published_at,
            social_image=image,
        ))

    return articles


async def search_newsapi(
    query: str,
    language: str = "pt",
    max_results: int = MAX_RESULTS,
    sort_by: str = "relevancy",
) -> GDELTResponse:
    """Busca artigos na NewsAPI.org.

    Args:
        query:       Texto de busca (frase, nome, alegação).
        language:    Código de idioma ('pt', 'en', 'es', etc.).
        max_results: Número máximo de artigos a retornar.
        sort_by:     Ordenação: 'relevancy', 'popularity', ou 'publishedAt'.

    Returns:
        GDELTResponse (mesmo formato do GDELT) com artigos ou erro.
    """
    api_key = _get_api_key()
    if not api_key:
        logger.debug("NEWSAPI_KEY não configurada — pulando NewsAPI")
        return GDELTResponse(query=query)

    clean = _clean_query(query)
    if not clean:
        return GDELTResponse(query=query)

    # Search last 30 days (NewsAPI free tier limit)
    from_date = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "q": clean,
        "language": language,
        "sortBy": sort_by,
        "pageSize": min(max_results, 100),  # API max is 100
        "from": from_date,
        "apiKey": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(NEWSAPI_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        # NewsAPI returns 401 for invalid key, 429 for rate limit
        if status == 401:
            logger.error("NewsAPI: chave inválida (HTTP 401)")
            return GDELTResponse(query=query, error="API key inválida")
        if status == 429:
            logger.warning("NewsAPI: rate limit atingido (HTTP 429)")
            return GDELTResponse(query=query, error="rate limit")
        logger.warning("NewsAPI HTTP %s para query=%r lang=%s", status, clean, language)
        return GDELTResponse(query=query, error=f"HTTP {status}")
    except httpx.TimeoutException:
        logger.warning("NewsAPI timeout para query=%r lang=%s", clean, language)
        return GDELTResponse(query=query, error="timeout")
    except Exception as exc:
        logger.error("NewsAPI erro inesperado: %s", exc)
        return GDELTResponse(query=query, error=str(exc))

    if data.get("status") != "ok":
        error_msg = data.get("message", "unknown error")
        logger.warning("NewsAPI status=%s: %s", data.get("status"), error_msg)
        return GDELTResponse(query=query, error=error_msg)

    articles = _parse_articles(data, language=language, max_results=max_results)
    total = data.get("totalResults", len(articles))

    logger.info(
        "NewsAPI: %d artigos (total=%d) para query=%r lang=%s",
        len(articles), total, clean[:60], language,
    )

    return GDELTResponse(query=query, articles=articles)
