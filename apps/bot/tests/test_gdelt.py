"""
test_gdelt.py — Testes do cliente GDELT DOC API (Micro-Batch 3.3)

Todos os testes mocam httpx.AsyncClient para evitar chamadas reais à rede.
"""

import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.gdelt import (
    search_articles,
    serialize_gdelt_response,
    _clean_query,
    _parse_gdelt_date,
    GDELTResponse,
    GDELTArticle,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

GDELT_SAMPLE = {
    "articles": [
        {
            "url": "https://aosfatos.org/noticias/vacina-autismo",
            "title": "Vacinas não causam autismo, confirma OMS",
            "seendate": "20240115T120000Z",
            "socialimage": "https://aosfatos.org/image.jpg",
            "domain": "aosfatos.org",
            "language": "Portuguese",
            "sourcecountry": "Brazil",
        },
        {
            "url": "https://lupa.news/verificacao/vacina-2024",
            "title": "Lupa verifica: alegação sobre vacina é falsa",
            "seendate": "20240110T083000Z",
            "socialimage": "",
            "domain": "lupa.news",
            "language": "Portuguese",
            "sourcecountry": "Brazil",
        },
    ]
}


def _make_client(body: dict, status_code: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
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


# ── Testes: _clean_query ──────────────────────────────────────────────────────

def test_clean_query_short_text_unchanged():
    assert _clean_query("Vacina causa autismo") == "Vacina causa autismo"


def test_clean_query_removes_brackets():
    result = _clean_query("[imagem sem legenda]")
    assert "[" not in result
    assert "]" not in result


def test_clean_query_removes_quotes():
    result = _clean_query('"Isso é falso"')
    assert '"' not in result


def test_clean_query_truncates_long_text():
    long_text = "palavra " * 50  # 400 chars
    result = _clean_query(long_text)
    assert len(result) <= 150


def test_clean_query_no_mid_word_truncation():
    long_text = "abc " * 50
    result = _clean_query(long_text)
    # Não deve terminar no meio de uma palavra
    assert not result.endswith("ab") and not result.endswith("a")


def test_clean_query_empty_stays_empty():
    assert _clean_query("") == ""


# ── Testes: _parse_gdelt_date ─────────────────────────────────────────────────

def test_parse_gdelt_date_full_format():
    assert _parse_gdelt_date("20240115T120000Z") == "2024-01-15T12:00:00Z"


def test_parse_gdelt_date_empty():
    assert _parse_gdelt_date("") == ""


def test_parse_gdelt_date_date_only():
    result = _parse_gdelt_date("20240115")
    assert "2024-01-15" in result


def test_parse_gdelt_date_unknown_format_returns_original():
    weird = "not-a-date"
    assert _parse_gdelt_date(weird) == weird


# ── Testes: search_articles ───────────────────────────────────────────────────

async def test_search_articles_returns_empty_for_empty_query():
    """Query vazia retorna GDELTResponse vazio sem chamar a API."""
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client({})
        result = await search_articles("")

    assert result.articles == []
    assert result.error == ""
    MockClient.assert_not_called()


async def test_search_articles_parses_correctly():
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client(GDELT_SAMPLE)
        result = await search_articles("vacina autismo")

    assert len(result.articles) == 2
    assert result.error == ""

    a = result.articles[0]
    assert a.url == "https://aosfatos.org/noticias/vacina-autismo"
    assert a.title == "Vacinas não causam autismo, confirma OMS"
    assert a.domain == "aosfatos.org"
    assert a.language == "Portuguese"
    assert a.source_country == "Brazil"
    assert a.seen_date == "2024-01-15T12:00:00Z"
    assert a.social_image == "https://aosfatos.org/image.jpg"


async def test_search_articles_second_article():
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client(GDELT_SAMPLE)
        result = await search_articles("vacina")

    a = result.articles[1]
    assert a.domain == "lupa.news"
    assert a.seen_date == "2024-01-10T08:30:00Z"
    assert a.social_image == ""  # ausente no fixture


async def test_search_articles_empty_articles_list():
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client({"articles": []})
        result = await search_articles("algo sem cobertura")

    assert result.articles == []
    assert result.error == ""


async def test_search_articles_passes_correct_params():
    """Parâmetros corretos são enviados na requisição."""
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client({})
        await search_articles(
            "eleições fraude",
            max_records=5,
            timespan="WEEK",
            source_language="por",
        )

    call_kwargs = MockClient.return_value.get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["mode"] == "artlist"
    assert params["format"] == "json"
    assert params["maxrecords"] == 5
    assert params["timespan"] == "WEEK"
    assert params["sort"] == "DateDesc"
    assert "eleições fraude" in params["query"]
    assert "por" in params["query"]


async def test_search_articles_max_records_capped_at_250():
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client({})
        await search_articles("teste", max_records=999)

    call_kwargs = MockClient.return_value.get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["maxrecords"] == 250


async def test_search_articles_no_language_filter():
    """Sem source_language, o filtro não é adicionado à query."""
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_client({})
        await search_articles("vacina autismo")

    call_kwargs = MockClient.return_value.get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert "sourcelang" not in params["query"]


# ── Testes: tratamento de erros ───────────────────────────────────────────────

async def test_search_articles_http_error_returns_error():
    from httpx import HTTPStatusError, Request, Response

    exc = HTTPStatusError(
        message="Service Unavailable",
        request=MagicMock(spec=Request),
        response=MagicMock(spec=Response, status_code=503),
    )
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=MagicMock(
        raise_for_status=MagicMock(side_effect=exc)
    ))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = mock_client
        result = await search_articles("teste")

    assert result.error == "HTTP 503"
    assert result.articles == []


async def test_search_articles_timeout_returns_error():
    from httpx import TimeoutException

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=TimeoutException("timeout"))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = mock_client
        result = await search_articles("teste")

    assert result.error == "timeout"
    assert result.articles == []


async def test_search_articles_unexpected_exception():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=ConnectionError("rede indisponível"))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = mock_client
        result = await search_articles("teste")

    assert "rede indisponível" in result.error


# ── Testes: serialização ──────────────────────────────────────────────────────

def test_serialize_gdelt_response_is_json_serializable():
    response = GDELTResponse(
        query="vacina autismo",
        articles=[
            GDELTArticle(
                url="https://aosfatos.org/1",
                title="Vacina é segura",
                domain="aosfatos.org",
                language="Portuguese",
                source_country="Brazil",
                seen_date="2024-01-15T12:00:00Z",
                social_image="https://aosfatos.org/img.jpg",
            )
        ],
    )
    serialized = serialize_gdelt_response(response)
    json_str = json.dumps(serialized)  # não deve lançar TypeError
    parsed = json.loads(json_str)

    assert parsed["query"] == "vacina autismo"
    assert len(parsed["articles"]) == 1
    assert parsed["articles"][0]["domain"] == "aosfatos.org"
    assert parsed["articles"][0]["seen_date"] == "2024-01-15T12:00:00Z"


def test_serialize_empty_response():
    response = GDELTResponse(query="vazio")
    serialized = serialize_gdelt_response(response)
    assert serialized["articles"] == []
    assert serialized["error"] == ""
    assert json.dumps(serialized)


def test_serialize_response_with_error():
    response = GDELTResponse(query="teste", error="timeout")
    serialized = serialize_gdelt_response(response)
    assert serialized["error"] == "timeout"
    assert serialized["articles"] == []
