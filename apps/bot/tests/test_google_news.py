"""
test_google_news.py — Testes do cliente Google News RSS

Todos os testes mocam httpx.AsyncClient para evitar chamadas reais à rede.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.google_news import (
    search_google_news,
    _clean_query,
    _parse_rss_date,
    _extract_source_domain,
    _clean_title,
    _parse_rss_xml,
)
from src.analysis.gdelt import GDELTArticle, GDELTResponse


# ── Sample RSS XML ────────────────────────────────────────────────────────────

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>NASA tempestade solar - Google News</title>
<item>
<title>Tempestade solar atinge a Terra - Estadão</title>
<link>https://news.google.com/rss/articles/ABC123</link>
<pubDate>Wed, 04 Feb 2026 08:00:00 GMT</pubDate>
<source url="https://www.estadao.com.br">Estadão</source>
</item>
<item>
<title>NASA alerta para erupção solar - Folha de S.Paulo</title>
<link>https://news.google.com/rss/articles/DEF456</link>
<pubDate>Thu, 05 Feb 2026 10:30:00 GMT</pubDate>
<source url="https://www1.folha.uol.com.br">Folha de S.Paulo</source>
</item>
<item>
<title>Sol dispara explosões em direção à Terra - Olhar Digital</title>
<link>https://news.google.com/rss/articles/GHI789</link>
<pubDate>Fri, 06 Feb 2026 14:00:00 GMT</pubDate>
<source url="https://olhardigital.com.br">Olhar Digital</source>
</item>
</channel>
</rss>"""

EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Empty</title></channel></rss>"""


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_client(body_text: str, status_code: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = body_text
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response
        mock_resp.raise_for_status.side_effect = HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(spec=Request),
            response=MagicMock(spec=Response, status_code=status_code),
        )
    else:
        mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


# ── Tests: _clean_query ───────────────────────────────────────────────────────

def test_clean_query_short():
    assert _clean_query("NASA tempestade solar") == "NASA tempestade solar"


def test_clean_query_removes_brackets():
    assert _clean_query('[teste] "aspas" (paren)') == "teste aspas paren"


def test_clean_query_truncates():
    long = "a " * 200
    result = _clean_query(long)
    assert len(result) <= 120


# ── Tests: _parse_rss_date ────────────────────────────────────────────────────

def test_parse_rss_date_valid():
    result = _parse_rss_date("Wed, 04 Feb 2026 08:00:00 GMT")
    assert result == "2026-02-04T08:00:00Z"


def test_parse_rss_date_empty():
    assert _parse_rss_date("") == ""


def test_parse_rss_date_invalid():
    result = _parse_rss_date("not-a-date")
    assert result == "not-a-date"


# ── Tests: _extract_source_domain ─────────────────────────────────────────────

def test_extract_domain_with_www():
    assert _extract_source_domain("https://www.estadao.com.br") == "estadao.com.br"


def test_extract_domain_without_www():
    assert _extract_source_domain("https://olhardigital.com.br") == "olhardigital.com.br"


def test_extract_domain_empty():
    assert _extract_source_domain("") == ""


# ── Tests: _clean_title ──────────────────────────────────────────────────────

def test_clean_title_removes_source():
    result = _clean_title("Tempestade solar atinge a Terra - Estadão", "Estadão")
    assert result == "Tempestade solar atinge a Terra"


def test_clean_title_fallback_last_dash():
    result = _clean_title("Título muito longo sobre tempestade solar - Fonte Desconhecida", "Outra")
    assert result == "Título muito longo sobre tempestade solar"


def test_clean_title_no_dash():
    result = _clean_title("Título sem separador", "Fonte")
    assert result == "Título sem separador"


def test_clean_title_empty():
    assert _clean_title("", "Fonte") == ""


# ── Tests: _parse_rss_xml ────────────────────────────────────────────────────

def test_parse_rss_xml_extracts_articles():
    articles = _parse_rss_xml(SAMPLE_RSS)
    assert len(articles) == 3
    assert articles[0].title == "Tempestade solar atinge a Terra"
    assert articles[0].domain == "estadao.com.br"
    assert articles[0].url == "https://news.google.com/rss/articles/ABC123"
    assert articles[0].source_country == "Brazil"
    assert articles[0].language == "Portuguese"


def test_parse_rss_xml_respects_max():
    articles = _parse_rss_xml(SAMPLE_RSS, max_results=2)
    assert len(articles) == 2


def test_parse_rss_xml_empty():
    articles = _parse_rss_xml(EMPTY_RSS)
    assert articles == []


def test_parse_rss_xml_invalid():
    articles = _parse_rss_xml("not xml at all")
    assert articles == []


def test_parse_rss_xml_seen_date_format():
    articles = _parse_rss_xml(SAMPLE_RSS)
    assert articles[0].seen_date == "2026-02-04T08:00:00Z"


# ── Tests: search_google_news (async) ────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_empty_query():
    result = await search_google_news("")
    assert isinstance(result, GDELTResponse)
    assert result.articles == []
    assert result.error == ""


@pytest.mark.asyncio
async def test_search_success():
    mock_client = _make_client(SAMPLE_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("NASA tempestade solar")
    assert isinstance(result, GDELTResponse)
    assert len(result.articles) == 3
    assert result.articles[0].domain == "estadao.com.br"
    assert result.error == ""


@pytest.mark.asyncio
async def test_search_http_error():
    mock_client = _make_client("", status_code=429)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("teste")
    assert result.error == "HTTP 429"
    assert result.articles == []


@pytest.mark.asyncio
async def test_search_timeout():
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("teste")
    assert result.error == "timeout"
    assert result.articles == []


@pytest.mark.asyncio
async def test_search_empty_rss():
    mock_client = _make_client(EMPTY_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("query sem resultados")
    assert result.articles == []
    assert result.error == ""


@pytest.mark.asyncio
async def test_articles_are_gdelt_compatible():
    """Google News articles must be GDELTArticle instances for frontend compatibility."""
    mock_client = _make_client(SAMPLE_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("teste")
    for article in result.articles:
        assert isinstance(article, GDELTArticle)
        assert hasattr(article, "url")
        assert hasattr(article, "title")
        assert hasattr(article, "domain")
        assert hasattr(article, "seen_date")
        assert hasattr(article, "source_country")


# ── Tests: English locale support ─────────────────────────────────────────────

SAMPLE_EN_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>climate change hoax - Google News</title>
<item>
<title>Climate change is real, scientists confirm - Reuters</title>
<link>https://news.google.com/rss/articles/EN001</link>
<pubDate>Mon, 10 Mar 2026 12:00:00 GMT</pubDate>
<source url="https://www.reuters.com">Reuters</source>
</item>
<item>
<title>Fact-checking climate denial claims - AP News</title>
<link>https://news.google.com/rss/articles/EN002</link>
<pubDate>Tue, 11 Mar 2026 09:00:00 GMT</pubDate>
<source url="https://apnews.com">AP News</source>
</item>
</channel>
</rss>"""


@pytest.mark.asyncio
async def test_search_english_locale():
    """lang='en-US' should set English locale params and article fields."""
    mock_client = _make_client(SAMPLE_EN_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("climate change hoax", lang="en-US")
    assert len(result.articles) == 2
    for article in result.articles:
        assert article.language == "English"
        assert article.source_country == ""
    # Verify the GET call used correct locale params
    call_kwargs = mock_client.get.call_args
    params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
    assert params["hl"] == "en-US"
    assert params["gl"] == "US"
    assert params["ceid"] == "US:en"


@pytest.mark.asyncio
async def test_search_default_locale_is_pt_br():
    """Default lang should produce PT-BR articles."""
    mock_client = _make_client(SAMPLE_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("tempestade solar")
    for article in result.articles:
        assert article.language == "Portuguese"
        assert article.source_country == "Brazil"


@pytest.mark.asyncio
async def test_search_unknown_locale_falls_back_to_pt():
    """Unknown lang tag should fall back to PT-BR."""
    mock_client = _make_client(SAMPLE_RSS)
    with patch("src.analysis.google_news.httpx.AsyncClient", return_value=mock_client):
        result = await search_google_news("teste", lang="xx-XX")
    for article in result.articles:
        assert article.language == "Portuguese"
        assert article.source_country == "Brazil"
