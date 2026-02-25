"""
test_fact_checker.py — Testes do cliente Google Fact Check Tools API (Micro-Batch 3.1)

Todos os testes mocam httpx.AsyncClient para evitar chamadas reais à API.
A chave de API é controlada via os.environ para testar o comportamento sem chave.
"""

import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.fact_checker import (
    search_claims,
    serialize_response,
    FactCheckResponse,
    FactCheckResult,
    ClaimReview,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_API_RESPONSE = {
    "claims": [
        {
            "text": "Vacina causa autismo",
            "claimant": "Grupo WhatsApp",
            "claimDate": "2023-01-15T00:00:00Z",
            "claimReview": [
                {
                    "publisher": {"name": "Agência Lupa", "site": "lupa.news"},
                    "url": "https://lupa.news/verificacao/vacina-autismo",
                    "title": "Não, vacinas não causam autismo",
                    "reviewDate": "2023-01-20T00:00:00Z",
                    "textualRating": "Falso",
                    "reviewRating": {"ratingValue": 1},
                    "languageCode": "pt",
                }
            ],
        },
        {
            "text": "COVID-19 foi criado em laboratório",
            "claimant": "Postagem viral",
            "claimDate": "2021-05-01T00:00:00Z",
            "claimReview": [
                {
                    "publisher": {"name": "Aos Fatos", "site": "aosfatos.org"},
                    "url": "https://aosfatos.org/noticias/covid-laboratorio",
                    "title": "Não há evidências de que COVID foi criado em laboratório",
                    "reviewDate": "2021-05-10T00:00:00Z",
                    "textualRating": "Sem evidência",
                    "reviewRating": {"ratingValue": 2},
                    "languageCode": "pt",
                }
            ],
        },
    ],
    "nextPageToken": "abc123",
}


def _mock_http_response(body: dict, status_code: int = 200):
    """Cria um mock de resposta httpx."""
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
    return mock_resp


# ── Testes: sem chave de API ──────────────────────────────────────────────────

async def test_returns_empty_when_no_api_key():
    """Se GOOGLE_API_KEY não está configurada, retorna resposta vazia sem erro."""
    env = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        result = await search_claims("vacina autismo")

    assert isinstance(result, FactCheckResponse)
    assert result.results == []
    assert result.error == ""
    assert result.query == "vacina autismo"


async def test_returns_empty_when_api_key_is_blank():
    """Chave em branco equivale a não configurada."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "   "}):
        result = await search_claims("teste")

    assert result.results == []
    assert result.error == ""


# ── Testes: chamada HTTP bem-sucedida ─────────────────────────────────────────

async def test_parses_claims_correctly():
    """Resposta da API é parseada em FactCheckResult/ClaimReview corretamente."""
    mock_resp = _mock_http_response(SAMPLE_API_RESPONSE)

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-123"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await search_claims("vacina autismo")

    assert len(result.results) == 2
    assert result.error == ""
    assert result.next_page_token == "abc123"

    first = result.results[0]
    assert first.text == "Vacina causa autismo"
    assert first.claimant == "Grupo WhatsApp"
    assert first.claim_date == "2023-01-15T00:00:00Z"
    assert len(first.reviews) == 1

    review = first.reviews[0]
    assert review.publisher_name == "Agência Lupa"
    assert review.publisher_site == "lupa.news"
    assert review.text_rating == "Falso"
    assert review.rating_value == 1
    assert review.language_code == "pt"
    assert "lupa.news" in review.url


async def test_parses_second_claim():
    """Segundo claim também é parseado corretamente."""
    mock_resp = _mock_http_response(SAMPLE_API_RESPONSE)

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-123"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await search_claims("covid laboratorio")

    second = result.results[1]
    assert second.text == "COVID-19 foi criado em laboratório"
    assert second.reviews[0].publisher_name == "Aos Fatos"
    assert second.reviews[0].text_rating == "Sem evidência"


async def test_empty_claims_list():
    """Resposta sem claims retorna lista vazia sem erro."""
    mock_resp = _mock_http_response({"claims": []})

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-123"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await search_claims("notícia sem resultados")

    assert result.results == []
    assert result.error == ""


async def test_passes_correct_params():
    """Parâmetros corretos são enviados na requisição HTTP."""
    mock_resp = _mock_http_response({})

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "my-api-key"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            await search_claims("eleições fraude", language_code="pt", page_size=3)

    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["query"] == "eleições fraude"
    assert params["languageCode"] == "pt"
    assert params["pageSize"] == 3
    assert params["key"] == "my-api-key"


async def test_page_size_capped_at_10():
    """page_size > 10 é limitado a 10 (limite da API)."""
    mock_resp = _mock_http_response({})

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "my-api-key"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            await search_claims("teste", page_size=50)

    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
    assert params["pageSize"] == 10


# ── Testes: erros HTTP ────────────────────────────────────────────────────────

async def test_http_403_returns_error():
    """HTTP 403 (chave inválida) retorna FactCheckResponse com error preenchido."""
    from httpx import HTTPStatusError, Request, Response

    http_exc = HTTPStatusError(
        message="403 Forbidden",
        request=MagicMock(spec=Request),
        response=MagicMock(spec=Response, status_code=403),
    )

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "invalid-key"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=MagicMock(
                raise_for_status=MagicMock(side_effect=http_exc)
            ))
            mock_client_cls.return_value = mock_client

            result = await search_claims("teste")

    assert result.error == "HTTP 403"
    assert result.results == []


async def test_timeout_returns_error():
    """Timeout retorna FactCheckResponse com error='timeout'."""
    from httpx import TimeoutException

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client

            result = await search_claims("teste")

    assert result.error == "timeout"
    assert result.results == []


async def test_unexpected_exception_returns_error():
    """Exceção genérica (ex: ConnectionError) retorna error com a mensagem."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=ConnectionError("rede indisponível"))
            mock_client_cls.return_value = mock_client

            result = await search_claims("teste")

    assert "rede indisponível" in result.error
    assert result.results == []


# ── Testes: serialização ──────────────────────────────────────────────────────

def test_serialize_response_is_json_serializable():
    """serialize_response retorna dict válido para json.dumps."""
    response = FactCheckResponse(
        query="teste",
        results=[
            FactCheckResult(
                text="Afirmação falsa",
                claimant="Alguém",
                claim_date="2023-01-01T00:00:00Z",
                reviews=[
                    ClaimReview(
                        publisher_name="Lupa",
                        publisher_site="lupa.news",
                        url="https://lupa.news/1",
                        title="Falso",
                        review_date="2023-01-05T00:00:00Z",
                        text_rating="Falso",
                        rating_value=1,
                        language_code="pt",
                    )
                ],
            )
        ],
    )
    serialized = serialize_response(response)
    json_str = json.dumps(serialized)  # Deve funcionar sem TypeError
    parsed = json.loads(json_str)

    assert parsed["query"] == "teste"
    assert len(parsed["results"]) == 1
    assert parsed["results"][0]["text"] == "Afirmação falsa"
    assert parsed["results"][0]["reviews"][0]["publisher_name"] == "Lupa"
    assert parsed["results"][0]["reviews"][0]["rating_value"] == 1


def test_serialize_empty_response():
    """Resposta vazia serializa sem erros."""
    response = FactCheckResponse(query="vazio")
    serialized = serialize_response(response)
    assert serialized["results"] == []
    assert serialized["error"] == ""
    assert json.dumps(serialized)  # serializável


def test_serialize_response_with_error():
    """Resposta com erro é serializada corretamente."""
    response = FactCheckResponse(query="teste", error="HTTP 429")
    serialized = serialize_response(response)
    assert serialized["error"] == "HTTP 429"
    assert serialized["results"] == []
