"""
test_domain_checker.py — Testes do analisador de domínio/URL (Micro-Batch 3.2)

Todos os testes mocam httpx.AsyncClient para evitar chamadas reais à rede.
VIRUSTOTAL_API_KEY e OPENPAGERANK_API_KEY controladas via os.environ.
"""

import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.domain_checker import (
    _extract_domain,
    _virustotal_url_id,
    _check_rdap,
    _check_virustotal,
    _check_urlscan,
    _check_pagerank,
    check_domain,
    serialize_domain_response,
    RDAPResult,
    VirusTotalResult,
    URLScanResult,
    PageRankResult,
    DomainCheckResponse,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_http(body: dict, status_code: int = 200):
    """Cria mock de resposta httpx com raise_for_status adequado."""
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


def _make_async_client(mock_resp):
    """Retorna AsyncMock que simula httpx.AsyncClient como context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.post = AsyncMock(return_value=mock_resp)
    return mock_client


# ── Testes: _extract_domain ───────────────────────────────────────────────────

def test_extract_domain_https():
    assert _extract_domain("https://www.example.com/path?q=1") == "example.com"


def test_extract_domain_http():
    assert _extract_domain("http://blog.example.com.br/post") == "blog.example.com.br"


def test_extract_domain_no_scheme():
    assert _extract_domain("www.example.com") == "example.com"


def test_extract_domain_strips_www():
    assert _extract_domain("https://www.lupa.news/verificacao") == "lupa.news"


def test_extract_domain_empty():
    assert _extract_domain("") == ""


def test_extract_domain_plain_text():
    # Texto sem URL válida retorna string vazia ou o texto como domínio
    # O importante é não levantar exceção
    result = _extract_domain("isso não é uma url")
    assert isinstance(result, str)


# ── Testes: _virustotal_url_id ───────────────────────────────────────────────

def test_virustotal_url_id_is_base64url_no_padding():
    url = "https://example.com"
    url_id = _virustotal_url_id(url)
    assert "=" not in url_id
    assert "/" not in url_id or "_" in url_id or "-" in url_id  # base64url usa - e _


def test_virustotal_url_id_is_deterministic():
    url = "https://example.com/page"
    assert _virustotal_url_id(url) == _virustotal_url_id(url)


# ── Testes: _check_rdap ───────────────────────────────────────────────────────

RDAP_SAMPLE = {
    "events": [
        {"eventAction": "registration", "eventDate": "2010-05-01T00:00:00Z"},
        {"eventAction": "expiration",   "eventDate": "2026-05-01T00:00:00Z"},
        {"eventAction": "last changed", "eventDate": "2024-01-15T00:00:00Z"},
    ],
    "status": ["active", "clientTransferProhibited"],
    "nameservers": [
        {"ldhName": "NS1.EXAMPLE.COM"},
        {"ldhName": "NS2.EXAMPLE.COM"},
    ],
    "entities": [
        {
            "roles": ["registrar"],
            "vcardArray": [
                "vcard",
                [
                    ["version", {}, "text", "4.0"],
                    ["fn", {}, "text", "Registrar XYZ Ltda"],
                ],
            ],
            "links": [{"href": "https://registrar.xyz"}],
        }
    ],
}


async def test_rdap_parses_correctly():
    mock_resp = _mock_http(RDAP_SAMPLE)
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_rdap("example.com")

    assert result.error == ""
    assert result.domain == "example.com"
    assert result.creation_date == "2010-05-01T00:00:00Z"
    assert result.expiration_date == "2026-05-01T00:00:00Z"
    assert result.last_changed_date == "2024-01-15T00:00:00Z"
    assert "active" in result.status
    assert "ns1.example.com" in result.name_servers
    assert result.registrar == "Registrar XYZ Ltda"
    assert result.registrar_url == "https://registrar.xyz"


async def test_rdap_404_returns_error():
    from httpx import HTTPStatusError, Request, Response
    exc = HTTPStatusError(
        message="Not Found",
        request=MagicMock(spec=Request),
        response=MagicMock(spec=Response, status_code=404),
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status.side_effect = exc

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_rdap("unknown.xyz")

    assert result.error != ""
    assert result.creation_date == ""


async def test_rdap_timeout_returns_error():
    from httpx import TimeoutException

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=TimeoutException("timeout"))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = mock_client
        result = await _check_rdap("slow.com")

    assert result.error == "timeout"


async def test_rdap_empty_entities():
    """RDAP sem entidades registrar — não deve levantar exceção."""
    mock_resp = _mock_http({"events": [], "status": [], "nameservers": [], "entities": []})
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_rdap("example.com")

    assert result.error == ""
    assert result.registrar == ""


# ── Testes: _check_virustotal ─────────────────────────────────────────────────

VT_SAMPLE = {
    "data": {
        "attributes": {
            "last_analysis_stats": {
                "malicious": 3,
                "suspicious": 1,
                "harmless": 65,
                "undetected": 10,
            },
            "reputation": -5,
            "last_analysis_date": 1700000000,
        }
    }
}


async def test_virustotal_no_key_returns_empty():
    env = {k: v for k, v in os.environ.items() if k != "VIRUSTOTAL_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        result = await _check_virustotal("https://example.com")

    assert result.malicious == 0
    assert result.error == ""


async def test_virustotal_parses_correctly():
    mock_resp = _mock_http(VT_SAMPLE)
    with patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "vt-key-123"}):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value = _make_async_client(mock_resp)
            result = await _check_virustotal("https://example.com")

    assert result.malicious == 3
    assert result.suspicious == 1
    assert result.harmless == 65
    assert result.reputation == -5
    assert result.last_analysis_date != ""
    assert result.error == ""


async def test_virustotal_404_url_not_analyzed():
    """URL nunca analisada (404) retorna resultado vazio sem erro."""
    from httpx import HTTPStatusError, Request, Response
    exc = HTTPStatusError(
        message="Not Found",
        request=MagicMock(spec=Request),
        response=MagicMock(spec=Response, status_code=404),
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status.side_effect = exc

    with patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "vt-key-123"}):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value = _make_async_client(mock_resp)
            result = await _check_virustotal("https://newurl.com")

    assert result.malicious == 0
    assert result.error == ""


async def test_virustotal_403_returns_error():
    from httpx import HTTPStatusError, Request, Response
    exc = HTTPStatusError(
        message="Forbidden",
        request=MagicMock(spec=Request),
        response=MagicMock(spec=Response, status_code=403),
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.raise_for_status.side_effect = exc

    with patch.dict(os.environ, {"VIRUSTOTAL_API_KEY": "bad-key"}):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value = _make_async_client(mock_resp)
            result = await _check_virustotal("https://example.com")

    assert result.error == "HTTP 403"


# ── Testes: _check_urlscan ────────────────────────────────────────────────────

URLSCAN_SAMPLE = {
    "total": 42,
    "results": [
        {
            "_id": "abc-uuid-123",
            "page": {
                "url": "https://example.com",
                "ip": "93.184.216.34",
                "country": "US",
                "server": "ECS (nyb/1D07)",
            },
            "stats": {"malicious": 0},
            "screenshot": "https://urlscan.io/screenshots/abc-uuid-123.png",
            "task": {"time": "2024-06-01T12:00:00Z"},
        }
    ],
}


async def test_urlscan_parses_correctly():
    mock_resp = _mock_http(URLSCAN_SAMPLE)
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_urlscan("https://example.com", "example.com")

    assert result.error == ""
    assert result.ip == "93.184.216.34"
    assert result.country == "US"
    assert result.malicious is False
    assert result.total_scans_found == 42
    assert "abc-uuid-123" in result.scan_result_url
    assert "abc-uuid-123" in result.screenshot_url
    assert result.scan_date == "2024-06-01T12:00:00Z"


async def test_urlscan_no_results():
    mock_resp = _mock_http({"total": 0, "results": []})
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_urlscan("https://newsite.com", "newsite.com")

    assert result.total_scans_found == 0
    assert result.error == ""
    assert result.ip == ""


async def test_urlscan_malicious_flagged():
    sample = {
        "total": 1,
        "results": [
            {
                "_id": "xyz",
                "page": {"ip": "1.2.3.4", "country": "RU"},
                "stats": {"malicious": 5},
                "screenshot": "",
                "task": {"time": "2024-01-01T00:00:00Z"},
            }
        ],
    }
    mock_resp = _mock_http(sample)
    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = _make_async_client(mock_resp)
        result = await _check_urlscan("https://bad.site", "bad.site")

    assert result.malicious is True


async def test_urlscan_timeout():
    from httpx import TimeoutException

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=TimeoutException("timeout"))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value = mock_client
        result = await _check_urlscan("https://slow.com", "slow.com")

    assert result.error == "timeout"


# ── Testes: _check_pagerank ───────────────────────────────────────────────────

PR_SAMPLE = {
    "status_code": 200,
    "response": [
        {
            "domain": "example.com",
            "page_rank_decimal": 6.52,
            "rank": "12345",
        }
    ],
}


async def test_pagerank_no_key_returns_empty():
    env = {k: v for k, v in os.environ.items() if k != "OPENPAGERANK_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        result = await _check_pagerank("example.com")

    assert result.page_rank_decimal == 0.0
    assert result.error == ""


async def test_pagerank_parses_correctly():
    mock_resp = _mock_http(PR_SAMPLE)
    with patch.dict(os.environ, {"OPENPAGERANK_API_KEY": "pr-key-123"}):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value = _make_async_client(mock_resp)
            result = await _check_pagerank("example.com")

    assert result.page_rank_decimal == 6.52
    assert result.rank == 12345
    assert result.error == ""


async def test_pagerank_empty_response():
    mock_resp = _mock_http({"response": []})
    with patch.dict(os.environ, {"OPENPAGERANK_API_KEY": "pr-key-123"}):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value = _make_async_client(mock_resp)
            result = await _check_pagerank("unknown.com")

    assert result.error != ""


# ── Testes: check_domain (orquestrador) ──────────────────────────────────────

async def test_check_domain_invalid_url():
    """URL inválida da qual não é possível extrair domínio."""
    result = await check_domain("isso não é uma url válida com domínio")
    # Ou retorna erro ou extrai algo — não deve lançar exceção
    assert isinstance(result, DomainCheckResponse)


async def test_check_domain_aggregates_all_checks():
    """check_domain agrega RDAP, VT, urlscan e PageRank."""
    with patch(
        "src.analysis.domain_checker._check_rdap",
        new_callable=AsyncMock,
        return_value=RDAPResult(domain="example.com", registrar="Registrar X"),
    ), patch(
        "src.analysis.domain_checker._check_virustotal",
        new_callable=AsyncMock,
        return_value=VirusTotalResult(url="https://example.com", malicious=0),
    ), patch(
        "src.analysis.domain_checker._check_urlscan",
        new_callable=AsyncMock,
        return_value=URLScanResult(url="https://example.com", total_scans_found=10),
    ), patch(
        "src.analysis.domain_checker._check_pagerank",
        new_callable=AsyncMock,
        return_value=PageRankResult(domain="example.com", page_rank_decimal=5.0),
    ):
        result = await check_domain("https://example.com")

    assert result.domain == "example.com"
    assert result.rdap.registrar == "Registrar X"
    assert result.virustotal.malicious == 0
    assert result.urlscan.total_scans_found == 10
    assert result.pagerank.page_rank_decimal == 5.0


async def test_check_domain_handles_individual_failures():
    """Falha em um checker não afeta os outros."""
    with patch(
        "src.analysis.domain_checker._check_rdap",
        new_callable=AsyncMock,
        side_effect=Exception("RDAP offline"),
    ), patch(
        "src.analysis.domain_checker._check_virustotal",
        new_callable=AsyncMock,
        return_value=VirusTotalResult(url="https://example.com"),
    ), patch(
        "src.analysis.domain_checker._check_urlscan",
        new_callable=AsyncMock,
        return_value=URLScanResult(url="https://example.com"),
    ), patch(
        "src.analysis.domain_checker._check_pagerank",
        new_callable=AsyncMock,
        return_value=PageRankResult(domain="example.com"),
    ):
        result = await check_domain("https://example.com")

    assert "RDAP offline" in result.rdap.error
    assert result.virustotal.error == ""


# ── Testes: serialização ──────────────────────────────────────────────────────

def test_serialize_domain_response_is_json_serializable():
    """serialize_domain_response retorna dict JSON-serializável."""
    response = DomainCheckResponse(
        url="https://example.com",
        domain="example.com",
        rdap=RDAPResult(
            domain="example.com",
            registrar="XYZ",
            creation_date="2010-01-01T00:00:00Z",
            status=["active"],
            name_servers=["ns1.example.com"],
        ),
        virustotal=VirusTotalResult(url="https://example.com", malicious=2),
        urlscan=URLScanResult(url="https://example.com", country="BR", malicious=False),
        pagerank=PageRankResult(domain="example.com", page_rank_decimal=7.1, rank=500),
    )
    serialized = serialize_domain_response(response)
    json_str = json.dumps(serialized)
    parsed = json.loads(json_str)

    assert parsed["domain"] == "example.com"
    assert parsed["rdap"]["registrar"] == "XYZ"
    assert parsed["virustotal"]["malicious"] == 2
    assert parsed["urlscan"]["country"] == "BR"
    assert parsed["pagerank"]["page_rank_decimal"] == 7.1


def test_serialize_empty_response():
    """Resposta vazia serializa sem erros."""
    response = DomainCheckResponse(url="https://x.com", domain="x.com")
    serialized = serialize_domain_response(response)
    assert json.dumps(serialized)  # não lança TypeError
    assert serialized["rdap"]["registrar"] == ""
    assert serialized["virustotal"]["malicious"] == 0
