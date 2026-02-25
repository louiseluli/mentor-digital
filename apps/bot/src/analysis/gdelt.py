"""
gdelt.py — Cliente para a GDELT DOC API v2 (Micro-Batch 3.3)

Endpoint: GET https://api.gdeltproject.org/api/v2/doc/doc
Documentação: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

GDELT (Global Database of Events, Language, and Tone) monitora notícias de
todo o mundo em tempo real. Não requer chave de API — completamente gratuito.

Uso aqui:
- Busca artigos de mídia global relacionados ao conteúdo enviado pelo usuário.
- Fornece contexto de cobertura midiática: quem noticiou, quando, qual tom.
- Útil para identificar se uma alegação está circulando amplamente ou se é nova.
- Busca em PT e EN em paralelo para maximizar cobertura.

Comportamento seguro:
- Retorna GDELTResponse vazio se query for vazia ou se a API falhar.
- Nunca propaga exceções.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_MAX_RECORDS = 10     # máx. de artigos por busca (API suporta até 250)
DEFAULT_TIMESPAN = "MONTH"   # janela temporal padrão: últimos 30 dias
DEFAULT_TIMEOUT = 15.0       # GDELT pode ser lento
MAX_QUERY_LENGTH = 150       # caracteres — evitar queries muito longas


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class GDELTArticle:
    """Um artigo retornado pela GDELT DOC API."""
    url: str = ""
    title: str = ""
    domain: str = ""
    language: str = ""
    source_country: str = ""
    seen_date: str = ""        # ISO 8601 convertido de formato GDELT
    social_image: str = ""


@dataclass
class GDELTResponse:
    """Resposta da GDELT para uma query — sempre retornada, mesmo em erro."""
    query: str = ""
    articles: list = field(default_factory=list)  # list[GDELTArticle]
    error: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_query(query: str) -> str:
    """Limpa e trunca a query para uso seguro no GDELT.

    - Remove caracteres especiais da sintaxe GDELT que possam estar em texto livre.
    - Trunca em MAX_QUERY_LENGTH sem cortar palavras.
    """
    # Remove colchetes (usados por mídia sem legenda), aspas duplas, parênteses
    cleaned = re.sub(r'[\[\]"()]', " ", query)
    # Colapsa espaços múltiplos
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= MAX_QUERY_LENGTH:
        return cleaned
    truncated = cleaned[:MAX_QUERY_LENGTH]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 0 else truncated


def _parse_gdelt_date(date_str: str) -> str:
    """Converte data GDELT (ex: '20240115T120000Z') para ISO 8601."""
    if not date_str:
        return ""
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return date_str  # devolve original se não conseguir parsear


def _parse_articles(data: dict) -> list:
    """Converte lista de artigos brutos em GDELTArticle."""
    articles = []
    for raw in data.get("articles", []):
        articles.append(GDELTArticle(
            url=raw.get("url", ""),
            title=raw.get("title", ""),
            domain=raw.get("domain", ""),
            language=raw.get("language", ""),
            source_country=raw.get("sourcecountry", ""),
            seen_date=_parse_gdelt_date(raw.get("seendate", "")),
            social_image=raw.get("socialimage", ""),
        ))
    return articles


# ── Cliente ───────────────────────────────────────────────────────────────────

async def search_articles(
    query: str,
    max_records: int = DEFAULT_MAX_RECORDS,
    timespan: str = DEFAULT_TIMESPAN,
    source_language: str = "",
) -> GDELTResponse:
    """Busca artigos de mídia global relacionados à query na GDELT DOC API.

    Args:
        query:           Texto a buscar (URL, frase, nome, alegação).
        max_records:     Número de artigos a retornar (máx. 250).
        timespan:        Janela temporal: "DAY", "WEEK", "MONTH", "6M", "1Y".
        source_language: Filtro de idioma GDELT (ex: "por", "english").
                         String vazia = sem filtro (todos os idiomas).

    Returns:
        GDELTResponse com `articles`, ou `error` em caso de falha.
        Retorna GDELTResponse vazio (sem erro) se query for vazia.
    """
    clean = _clean_query(query)
    if not clean:
        return GDELTResponse(query=query)

    # Aplicar filtro de idioma na query GDELT se especificado
    gdelt_query = f"{clean} sourcelang:{source_language}" if source_language else clean

    params = {
        "query": gdelt_query,
        "mode": "artlist",
        "maxrecords": min(max_records, 250),
        "format": "json",
        "timespan": timespan,
        "sort": "DateDesc",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(GDELT_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("GDELT API HTTP %s para query=%r", status, clean)
        return GDELTResponse(query=query, error=f"HTTP {status}")
    except httpx.TimeoutException:
        logger.warning("GDELT API timeout para query=%r", clean)
        return GDELTResponse(query=query, error="timeout")
    except Exception as exc:
        logger.error("GDELT API erro inesperado: %s", exc)
        return GDELTResponse(query=query, error=str(exc))

    return GDELTResponse(
        query=query,
        articles=_parse_articles(data),
    )


# ── Serialização ──────────────────────────────────────────────────────────────

def serialize_gdelt_response(r: GDELTResponse) -> dict:
    """Converte GDELTResponse em dict JSON-serializável."""
    return {
        "query": r.query,
        "error": r.error,
        "articles": [
            {
                "url": a.url,
                "title": a.title,
                "domain": a.domain,
                "language": a.language,
                "source_country": a.source_country,
                "seen_date": a.seen_date,
                "social_image": a.social_image,
            }
            for a in r.articles
        ],
    }
