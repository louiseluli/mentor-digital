"""
test_newsapi.py — Testes do cliente NewsAPI.org

Todos os testes mocam httpx.AsyncClient e a env var NEWSAPI_KEY
para evitar chamadas reais à rede.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.newsapi import (
    search_newsapi,
    _clean_query,
    _parse_iso_date,
    _extract_domain,
    _parse_articles,
    _source_country_from_lang,
)
from src.analysis.gdelt import GDELTArticle, GDELTResponse


# ── Sample API Response ──────────────────────────────────────────────────────

SAMPLE_RESPONSE = {
    "status": "ok",
    "totalResults": 3,
    "articles": [
        {
            "source": {"id": None, "name": "Estadão"},
            "author": "Redação",
            "title": "Tempestade solar pode afetar comunicações no Brasil",
            "description": "Cientistas alertam para impacto nas telecomunicações.",
            "url": "https://www.estadao.com.br/ciencia/tempestade-solar-2026",
            "urlToImage": "https://www.estadao.com.br/img/solar.jpg",
            "publishedAt": "2026-02-28T14:22:00Z",
            "content": "Artigo completo sobre tempestade solar..."
        },
        {
            "source": {"id": "bbc-news", "name": "BBC News"},
            "author": "John Doe",
            "title": "Solar storm warning issued by NASA",
            "description": "NASA warns of potential solar storm impact.",
            "url": "https://www.bbc.com/news/science-solar-storm-2026",
            "urlToImage": "https://www.bbc.com/img/solar.jpg",
            "publishedAt": "2026-02-27T10:00:00Z",
            "content": "Full article about solar storm..."
        },
        {
            "source": {"id": None, "name": "Reuters"},
            "author": None,
            "title": "Global solar storm alert",
            "description": "Reuters reports on solar activity.",
            "url": "https://www.reuters.com/science/solar-storm",
            "urlToImage": None,
            "publishedAt": "2026-02-26T08:30:00Z",
            "content": "Reuters article..."
        }
    ]
}

EMPTY_RESPONSE = {
    "status": "ok",
    "totalResults": 0,
    "articles": []
}

ERROR_RESPONSE = {
    "status": "error",
    "code": "apiKeyInvalid",
    "message": "Your API key is invalid or incorrect."
}

REMOVED_ARTICLE_RESPONSE = {
    "status": "ok",
    "totalResults": 2,
    "articles": [
        {
            "source": {"id": None, "name": "[Removed]"},
            "title": "[Removed]",
            "url": "https://removed.com",
            "publishedAt": "2026-02-28T00:00:00Z"
        },
        {
            "source": {"id": None, "name": "Folha"},
            "title": "Artigo válido sobre tema",
            "url": "https://www.folha.uol.com.br/algo",
            "publishedAt": "2026-02-28T12:00:00Z"
        }
    ]
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_client(body: dict | str, status_code: int = 200):
    """Cria mock de httpx.AsyncClient com resposta JSON ou texto."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if isinstance(body, dict):
        mock_resp.json.return_value = body
        mock_resp.text = json.dumps(body)
    else:
        mock_resp.json.return_value = json.loads(body) if body else {}
        mock_resp.text = body

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


# ── Testes de helpers ─────────────────────────────────────────────────────────

class TestCleanQuery:
    def test_short_query_unchanged(self):
        assert _clean_query("tempestade solar") == "tempestade solar"

    def test_removes_brackets(self):
        assert _clean_query('[link] "quoted" (text)') == "link quoted text"

    def test_truncates_long_query(self):
        long_q = "a " * 100
        result = _clean_query(long_q)
        assert len(result) <= 120

    def test_empty_input(self):
        assert _clean_query("") == ""

    def test_collapses_whitespace(self):
        assert _clean_query("  multiple   spaces  ") == "multiple spaces"


class TestParseIsoDate:
    def test_standard_iso(self):
        assert _parse_iso_date("2026-02-28T14:22:00Z") == "2026-02-28T14:22:00Z"

    def test_empty_string(self):
        assert _parse_iso_date("") == ""

    def test_invalid_date(self):
        result = _parse_iso_date("not-a-date")
        assert result == "not-a-date"  # returns as-is on failure

    def test_none_input(self):
        assert _parse_iso_date(None) == ""


class TestExtractDomain:
    def test_full_url(self):
        assert _extract_domain("https://www.estadao.com.br/ciencia/algo") == "estadao.com.br"

    def test_strips_www(self):
        assert _extract_domain("https://www.bbc.com/news") == "bbc.com"

    def test_no_www(self):
        assert _extract_domain("https://reuters.com/article") == "reuters.com"

    def test_empty_url(self):
        assert _extract_domain("") == ""

    def test_http_url(self):
        assert _extract_domain("http://g1.globo.com/politica") == "g1.globo.com"


class TestSourceCountryFromLang:
    def test_pt_is_brazil(self):
        assert _source_country_from_lang("pt") == "Brazil"

    def test_en_is_empty(self):
        assert _source_country_from_lang("en") == ""

    def test_unknown_is_empty(self):
        assert _source_country_from_lang("ja") == ""


class TestParseArticles:
    def test_parses_all_articles(self):
        articles = _parse_articles(SAMPLE_RESPONSE, language="pt")
        assert len(articles) == 3

    def test_article_fields(self):
        articles = _parse_articles(SAMPLE_RESPONSE, language="pt")
        first = articles[0]
        assert first.url == "https://www.estadao.com.br/ciencia/tempestade-solar-2026"
        assert first.title == "Tempestade solar pode afetar comunicações no Brasil"
        assert first.domain == "estadao.com.br"
        assert first.language == "Portuguese"
        assert first.source_country == "Brazil"
        assert first.seen_date == "2026-02-28T14:22:00Z"
        assert first.social_image == "https://www.estadao.com.br/img/solar.jpg"

    def test_en_language_label(self):
        articles = _parse_articles(SAMPLE_RESPONSE, language="en")
        assert articles[0].language == "English"

    def test_respects_max_results(self):
        articles = _parse_articles(SAMPLE_RESPONSE, language="pt", max_results=2)
        assert len(articles) == 2

    def test_empty_response(self):
        articles = _parse_articles(EMPTY_RESPONSE, language="pt")
        assert len(articles) == 0

    def test_skips_removed_articles(self):
        articles = _parse_articles(REMOVED_ARTICLE_RESPONSE, language="pt")
        assert len(articles) == 1
        assert "válido" in articles[0].title

    def test_handles_missing_fields(self):
        data = {"articles": [{"url": "https://example.com", "source": {}}]}
        articles = _parse_articles(data, language="pt")
        assert len(articles) == 1
        assert articles[0].domain == "example.com"

    def test_skips_no_url(self):
        data = {"articles": [{"title": "No URL article", "source": {}}]}
        articles = _parse_articles(data, language="pt")
        assert len(articles) == 0


# ── Testes de search_newsapi ─────────────────────────────────────────────────

class TestSearchNewsapi:
    @pytest.mark.asyncio
    async def test_empty_query(self):
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key"}):
            result = await search_newsapi("")
        assert isinstance(result, GDELTResponse)
        assert result.articles == []
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NEWSAPI_KEY", None)
            result = await search_newsapi("tempestade solar")
        assert isinstance(result, GDELTResponse)
        assert result.articles == []
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_success(self):
        mock_client = _make_client(SAMPLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar", language="pt")

        assert isinstance(result, GDELTResponse)
        assert len(result.articles) == 3
        assert result.error == ""
        assert result.articles[0].domain == "estadao.com.br"
        assert result.articles[0].title == "Tempestade solar pode afetar comunicações no Brasil"

    @pytest.mark.asyncio
    async def test_success_en(self):
        mock_client = _make_client(SAMPLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("solar storm", language="en")

        assert isinstance(result, GDELTResponse)
        assert len(result.articles) == 3
        assert result.articles[0].language == "English"

    @pytest.mark.asyncio
    async def test_http_error(self):
        mock_client = _make_client({}, status_code=500)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert result.error == "HTTP 500"
        assert result.articles == []

    @pytest.mark.asyncio
    async def test_401_invalid_key(self):
        mock_client = _make_client(ERROR_RESPONSE, status_code=401)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "bad-key"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert "inválida" in result.error

    @pytest.mark.asyncio
    async def test_429_rate_limit(self):
        mock_client = _make_client({}, status_code=429)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert "rate limit" in result.error

    @pytest.mark.asyncio
    async def test_timeout(self):
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert result.error == "timeout"
        assert result.articles == []

    @pytest.mark.asyncio
    async def test_api_error_status(self):
        mock_client = _make_client(ERROR_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert "invalid" in result.error.lower() or "incorrect" in result.error.lower()

    @pytest.mark.asyncio
    async def test_empty_results(self):
        mock_client = _make_client(EMPTY_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("xyznonexistent123")

        assert result.articles == []
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_removed_articles_filtered(self):
        mock_client = _make_client(REMOVED_ARTICLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("algo")

        assert len(result.articles) == 1
        assert "válido" in result.articles[0].title

    @pytest.mark.asyncio
    async def test_gdelt_response_compatibility(self):
        """NewsAPI returns GDELTResponse objects for frontend compatibility."""
        mock_client = _make_client(SAMPLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert isinstance(result, GDELTResponse)
        assert all(isinstance(a, GDELTArticle) for a in result.articles)
        assert hasattr(result.articles[0], "url")
        assert hasattr(result.articles[0], "title")
        assert hasattr(result.articles[0], "domain")
        assert hasattr(result.articles[0], "seen_date")

    @pytest.mark.asyncio
    async def test_max_results_parameter(self):
        mock_client = _make_client(SAMPLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar", max_results=1)

        assert len(result.articles) <= 1

    @pytest.mark.asyncio
    async def test_passes_language_param(self):
        mock_client = _make_client(EMPTY_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                await search_newsapi("query", language="es")

        # Verify the API was called with correct language param
        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["language"] == "es"

    @pytest.mark.asyncio
    async def test_uses_api_key_in_params(self):
        mock_client = _make_client(EMPTY_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "my-secret-key"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                await search_newsapi("query")

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["apiKey"] == "my-secret-key"

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=RuntimeError("unexpected"))

        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert "unexpected" in result.error
        assert result.articles == []

    @pytest.mark.asyncio
    async def test_social_image_preserved(self):
        mock_client = _make_client(SAMPLE_RESPONSE)
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test-key-123"}):
            with patch("src.analysis.newsapi.httpx.AsyncClient", return_value=mock_client):
                result = await search_newsapi("tempestade solar")

        assert result.articles[0].social_image == "https://www.estadao.com.br/img/solar.jpg"
        # Reuters article has no image
        assert result.articles[2].social_image == ""
