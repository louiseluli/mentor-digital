"""
google_news.py — Cliente para Google News RSS (fallback/complemento ao GDELT)

Endpoint: GET https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419
Não requer chave de API — completamente gratuito.

Uso aqui:
- Busca artigos de notícias brasileiras relacionados ao conteúdo enviado pelo usuário.
- Retorna resultados de fontes confiáveis como Estadão, Folha, G1, CNN Brasil, etc.
- Serve como fallback quando o GDELT está fora do ar e também como complemento.
- Retorna artigos no mesmo formato do GDELT (GDELTArticle) para reuso no frontend.

Comportamento seguro:
- Retorna lista vazia se query for vazia ou se a API falhar.
- Nunca propaga exceções.
"""

import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from src.analysis.gdelt import GDELTArticle, GDELTResponse

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
DEFAULT_TIMEOUT = 15.0
MAX_RESULTS = 10
MAX_QUERY_LENGTH = 120


def _clean_query(query: str) -> str:
    """Limpa e trunca a query para uso no Google News RSS."""
    cleaned = re.sub(r'[\[\]"()]', " ", query)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= MAX_QUERY_LENGTH:
        return cleaned
    truncated = cleaned[:MAX_QUERY_LENGTH]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 0 else truncated


def _parse_rss_date(date_str: str) -> str:
    """Converte data RFC 822 (e.g. 'Wed, 04 Feb 2026 08:00:00 GMT') p/ ISO 8601."""
    if not date_str:
        return ""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return date_str


def _extract_source_domain(source_url: str) -> str:
    """Extrai domínio limpo da URL da fonte (ex: 'https://www.estadao.com.br' → 'estadao.com.br')."""
    if not source_url:
        return ""
    domain = source_url.replace("https://", "").replace("http://", "").rstrip("/")
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _clean_title(title: str, source_name: str) -> str:
    """Remove o nome da fonte do final do título (Google News adiciona ' - Fonte')."""
    if not title:
        return ""
    if source_name and title.endswith(f" - {source_name}"):
        return title[: -(len(source_name) + 3)].strip()
    # Fallback: remove tudo após o último ' - '
    last_dash = title.rfind(" - ")
    if last_dash > 20:  # mínimo de 20 chars no título
        return title[:last_dash].strip()
    return title


def _parse_rss_xml(xml_text: str, max_results: int = MAX_RESULTS) -> list[GDELTArticle]:
    """Parseia XML do Google News RSS e retorna lista de GDELTArticle."""
    articles: list[GDELTArticle] = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        logger.warning("Falha ao parsear XML do Google News RSS: %s", exc)
        return articles

    channel = root.find("channel")
    if channel is None:
        return articles

    for item in channel.findall("item"):
        if len(articles) >= max_results:
            break

        title_el = item.find("title")
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")
        source_el = item.find("source")

        raw_title = title_el.text if title_el is not None and title_el.text else ""
        url = link_el.text if link_el is not None and link_el.text else ""
        pub_date = pub_date_el.text if pub_date_el is not None and pub_date_el.text else ""
        source_name = source_el.text if source_el is not None and source_el.text else ""
        source_url = source_el.get("url", "") if source_el is not None else ""

        if not url:
            continue

        domain = _extract_source_domain(source_url)
        title = _clean_title(raw_title, source_name)

        articles.append(GDELTArticle(
            url=url,
            title=title or raw_title,
            domain=domain,
            language="Portuguese",
            source_country="Brazil",
            seen_date=_parse_rss_date(pub_date),
            social_image="",
        ))

    return articles


async def search_google_news(
    query: str,
    max_results: int = MAX_RESULTS,
    lang: str = "pt-BR",
) -> GDELTResponse:
    """Busca artigos no Google News RSS.

    Args:
        query:       Texto de busca (frase, nome, alegação).
        max_results: Número máximo de artigos a retornar.
        lang:        Locale tag: "pt-BR" (default) ou "en-US" para inglês.

    Returns:
        GDELTResponse (mesmo formato do GDELT) com artigos ou erro.
    """
    clean = _clean_query(query)
    if not clean:
        return GDELTResponse(query=query)

    # Configure locale-specific parameters
    _LOCALE_MAP: dict[str, dict[str, str]] = {
        "pt-BR": {"hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419",
                  "language": "Portuguese", "source_country": "Brazil"},
        "en-US": {"hl": "en-US", "gl": "US", "ceid": "US:en",
                  "language": "English", "source_country": ""},
        "en-GB": {"hl": "en-GB", "gl": "GB", "ceid": "GB:en",
                  "language": "English", "source_country": "United Kingdom"},
    }
    locale = _LOCALE_MAP.get(lang, _LOCALE_MAP["pt-BR"])

    params = {
        "q": clean,
        "hl": locale["hl"],
        "gl": locale["gl"],
        "ceid": locale["ceid"],
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(GOOGLE_NEWS_RSS_URL, params=params)
            resp.raise_for_status()
            xml_text = resp.text
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("Google News RSS HTTP %s para query=%r", status, clean)
        return GDELTResponse(query=query, error=f"HTTP {status}")
    except httpx.TimeoutException:
        logger.warning("Google News RSS timeout para query=%r", clean)
        return GDELTResponse(query=query, error="timeout")
    except Exception as exc:
        logger.error("Google News RSS erro inesperado: %s", exc)
        return GDELTResponse(query=query, error=str(exc))

    articles = _parse_rss_xml(xml_text, max_results=max_results)

    # Set locale-specific fields on articles
    for article in articles:
        article.language = locale["language"]
        article.source_country = locale["source_country"]

    logger.info("Google News RSS (%s): %d artigos para query=%r", lang, len(articles), clean[:60])

    return GDELTResponse(query=query, articles=articles)
