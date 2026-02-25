"""
domain_checker.py — Análise de domínio/URL (Micro-Batch 3.2)

Verificações disponíveis:
  - RDAP          registro do domínio (gratuito, sem chave)
  - urlscan.io    histórico de scans públicos (gratuito, sem chave — pesquisa)
  - VirusTotal    reputação de malware (VIRUSTOTAL_API_KEY — tier gratuito: 4 req/min)
  - Open PageRank autoridade do domínio (OPENPAGERANK_API_KEY — tier gratuito: 100 req/dia)

Ativado apenas quando content_type == "link".
Todas as verificações rodam em paralelo. Falha individual não afeta as outras.
Chaves ausentes → verificação ignorada sem erro.

Configuração opcional (.env):
  VIRUSTOTAL_API_KEY=   → https://www.virustotal.com/gui/join-us (gratuito)
  OPENPAGERANK_API_KEY= → https://www.domcop.com/openpagerank/signup (gratuito)
"""

import asyncio
import base64
import logging
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0

# ── URLs dos endpoints ────────────────────────────────────────────────────────

_RDAP_URL = "https://rdap.org/domain/{domain}"
_VIRUSTOTAL_URL = "https://www.virustotal.com/api/v3/urls/{url_id}"
_URLSCAN_SEARCH_URL = "https://urlscan.io/api/v1/search/"
_OPENPAGERANK_URL = "https://openpagerank.com/api/v1.0/getPageRank"


# ── Dataclasses de resultado ──────────────────────────────────────────────────

@dataclass
class RDAPResult:
    """Dados de registro do domínio via protocolo RDAP."""
    domain: str = ""
    registrar: str = ""
    registrar_url: str = ""
    creation_date: str = ""       # ISO 8601
    expiration_date: str = ""     # ISO 8601
    last_changed_date: str = ""   # ISO 8601
    status: list = field(default_factory=list)      # ex: ["active", "clientTransferProhibited"]
    name_servers: list = field(default_factory=list) # ex: ["ns1.example.com"]
    error: str = ""


@dataclass
class VirusTotalResult:
    """Reputação de URL/domínio via VirusTotal."""
    url: str = ""
    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0
    reputation: int = 0       # Score VirusTotal (negativo = ruim)
    last_analysis_date: str = ""
    error: str = ""


@dataclass
class URLScanResult:
    """Histórico de scans públicos via urlscan.io (pesquisa — sem nova submissão)."""
    url: str = ""
    scan_result_url: str = ""     # Página de resultado no urlscan.io
    screenshot_url: str = ""      # Screenshot PNG da página
    ip: str = ""
    country: str = ""
    server: str = ""
    malicious: bool = False
    scan_date: str = ""           # Data do scan mais recente encontrado
    total_scans_found: int = 0
    error: str = ""


@dataclass
class PageRankResult:
    """Autoridade do domínio via Open PageRank."""
    domain: str = ""
    page_rank_decimal: float = 0.0   # 0–10 (0=baixo, 10=máximo)
    rank: int = 0                    # Posição global (0 = não disponível)
    error: str = ""


@dataclass
class DomainCheckResponse:
    """Resultado agregado de todas as verificações de domínio."""
    url: str = ""
    domain: str = ""
    rdap: "RDAPResult" = field(default_factory=RDAPResult)
    virustotal: "VirusTotalResult" = field(default_factory=VirusTotalResult)
    urlscan: "URLScanResult" = field(default_factory=URLScanResult)
    pagerank: "PageRankResult" = field(default_factory=PageRankResult)
    error: str = ""    # Preenchido se a extração do domínio falhar


# ── Extração de domínio ───────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extrai o domínio (hostname sem www.) de uma URL.

    Suporta URLs com e sem esquema (http://, https://).
    Retorna string vazia se a URL for inválida.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname.lstrip("www.")
    except Exception:
        return ""


def _normalize_url(url: str) -> str:
    """Adiciona esquema https:// se ausente."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _virustotal_url_id(url: str) -> str:
    """Gera o ID de URL para a API VirusTotal (base64url sem padding)."""
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


# ── RDAP ─────────────────────────────────────────────────────────────────────

def _parse_rdap_events(events: list) -> dict:
    result = {}
    for ev in events:
        action = ev.get("eventAction", "")
        date = ev.get("eventDate", "")
        if action == "registration":
            result["creation_date"] = date
        elif action in ("expiration", "reregistration expiration"):
            result["expiration_date"] = date
        elif action == "last changed":
            result["last_changed_date"] = date
    return result


def _parse_rdap_registrar(entities: list) -> tuple[str, str]:
    """Extrai nome e URL do registrar das entidades RDAP."""
    for entity in entities:
        if "registrar" in entity.get("roles", []):
            vcard = entity.get("vcardArray", [[], []])[1]
            name = ""
            for field_data in vcard:
                if field_data[0] == "fn":
                    name = field_data[3]
                    break
            url = entity.get("links", [{}])[0].get("href", "") if entity.get("links") else ""
            return name, url
    return "", ""


async def _check_rdap(domain: str) -> RDAPResult:
    """Consulta RDAP para obter dados de registro do domínio.

    Gratuito, sem chave de API. Pode não estar disponível para todos os TLDs.
    """
    url = _RDAP_URL.format(domain=domain)
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 404:
                return RDAPResult(domain=domain, error="domínio não encontrado no RDAP")
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        return RDAPResult(domain=domain, error=f"HTTP {exc.response.status_code}")
    except httpx.TimeoutException:
        return RDAPResult(domain=domain, error="timeout")
    except Exception as exc:
        return RDAPResult(domain=domain, error=str(exc))

    events = _parse_rdap_events(data.get("events", []))
    registrar_name, registrar_url = _parse_rdap_registrar(data.get("entities", []))
    name_servers = [ns.get("ldhName", "").lower() for ns in data.get("nameservers", [])]
    status = data.get("status", [])

    return RDAPResult(
        domain=domain,
        registrar=registrar_name,
        registrar_url=registrar_url,
        creation_date=events.get("creation_date", ""),
        expiration_date=events.get("expiration_date", ""),
        last_changed_date=events.get("last_changed_date", ""),
        status=status,
        name_servers=name_servers,
    )


# ── VirusTotal ───────────────────────────────────────────────────────────────

async def _check_virustotal(url: str) -> VirusTotalResult:
    """Verifica reputação de URL no VirusTotal (analisa cache existente).

    Requer VIRUSTOTAL_API_KEY. Retorna resultado vazio se chave ausente.
    Tier gratuito: 4 requests/min, 500/dia.
    """
    api_key = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
    if not api_key:
        logger.debug("VIRUSTOTAL_API_KEY não configurada — verificação ignorada.")
        return VirusTotalResult(url=url)

    url_id = _virustotal_url_id(url)
    endpoint = _VIRUSTOTAL_URL.format(url_id=url_id)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                endpoint,
                headers={"x-apikey": api_key},
            )
            if resp.status_code == 404:
                # URL nunca analisada — não é necessariamente ruim
                return VirusTotalResult(url=url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        return VirusTotalResult(url=url, error=f"HTTP {exc.response.status_code}")
    except httpx.TimeoutException:
        return VirusTotalResult(url=url, error="timeout")
    except Exception as exc:
        return VirusTotalResult(url=url, error=str(exc))

    attrs = data.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})

    # Data do último scan (epoch → ISO)
    last_date = ""
    epoch = attrs.get("last_analysis_date")
    if epoch:
        from datetime import datetime, UTC
        last_date = datetime.fromtimestamp(epoch, tz=UTC).isoformat()

    return VirusTotalResult(
        url=url,
        malicious=stats.get("malicious", 0),
        suspicious=stats.get("suspicious", 0),
        harmless=stats.get("harmless", 0),
        undetected=stats.get("undetected", 0),
        reputation=attrs.get("reputation", 0),
        last_analysis_date=last_date,
    )


# ── urlscan.io ────────────────────────────────────────────────────────────────

async def _check_urlscan(url: str, domain: str) -> URLScanResult:
    """Pesquisa scans anteriores do domínio no urlscan.io.

    Usa a API de pesquisa pública (sem chave necessária).
    Retorna o scan mais recente encontrado, se houver.
    """
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                _URLSCAN_SEARCH_URL,
                params={"q": f"page.domain:{domain}", "size": 1, "sort": "date:desc"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        return URLScanResult(url=url, error=f"HTTP {exc.response.status_code}")
    except httpx.TimeoutException:
        return URLScanResult(url=url, error="timeout")
    except Exception as exc:
        return URLScanResult(url=url, error=str(exc))

    results = data.get("results", [])
    total = data.get("total", 0)

    if not results:
        return URLScanResult(url=url, total_scans_found=total)

    hit = results[0]
    page = hit.get("page", {})
    stats = hit.get("stats", {})
    scan_id = hit.get("_id", "")

    return URLScanResult(
        url=url,
        scan_result_url=f"https://urlscan.io/result/{scan_id}/" if scan_id else "",
        screenshot_url=hit.get("screenshot", ""),
        ip=page.get("ip", ""),
        country=page.get("country", ""),
        server=page.get("server", ""),
        malicious=bool(stats.get("malicious", 0) > 0),
        scan_date=hit.get("task", {}).get("time", ""),
        total_scans_found=total,
    )


# ── Open PageRank ─────────────────────────────────────────────────────────────

async def _check_pagerank(domain: str) -> PageRankResult:
    """Verifica autoridade do domínio via Open PageRank.

    Requer OPENPAGERANK_API_KEY. Retorna resultado vazio se chave ausente.
    Tier gratuito: 100 requests/dia.
    """
    api_key = os.getenv("OPENPAGERANK_API_KEY", "").strip()
    if not api_key:
        logger.debug("OPENPAGERANK_API_KEY não configurada — verificação ignorada.")
        return PageRankResult(domain=domain)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                _OPENPAGERANK_URL,
                params={"domains[]": domain},
                headers={"API-OPR": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        return PageRankResult(domain=domain, error=f"HTTP {exc.response.status_code}")
    except httpx.TimeoutException:
        return PageRankResult(domain=domain, error="timeout")
    except Exception as exc:
        return PageRankResult(domain=domain, error=str(exc))

    response_list = data.get("response", [])
    if not response_list:
        return PageRankResult(domain=domain, error="domínio não encontrado")

    entry = response_list[0]
    try:
        rank = int(entry.get("rank", 0) or 0)
    except (ValueError, TypeError):
        rank = 0

    return PageRankResult(
        domain=domain,
        page_rank_decimal=float(entry.get("page_rank_decimal", 0.0) or 0.0),
        rank=rank,
    )


# ── Orquestrador ──────────────────────────────────────────────────────────────

async def check_domain(url: str) -> DomainCheckResponse:
    """Executa todas as verificações de domínio em paralelo para a URL fornecida.

    Args:
        url: URL a analisar. Esquema http(s):// é adicionado se ausente.

    Returns:
        DomainCheckResponse com resultados de RDAP, VirusTotal, urlscan.io e PageRank.
        Verificações individuais que falharem retornam objetos com campo `error` preenchido.
    """
    normalized = _normalize_url(url)
    domain = _extract_domain(normalized)
    if not domain:
        return DomainCheckResponse(url=url, error="não foi possível extrair o domínio da URL")

    rdap_task = asyncio.create_task(_check_rdap(domain))
    vt_task = asyncio.create_task(_check_virustotal(normalized))
    urlscan_task = asyncio.create_task(_check_urlscan(normalized, domain))
    pr_task = asyncio.create_task(_check_pagerank(domain))

    rdap, vt, urlscan, pr = await asyncio.gather(
        rdap_task, vt_task, urlscan_task, pr_task,
        return_exceptions=True,
    )

    return DomainCheckResponse(
        url=normalized,
        domain=domain,
        rdap=rdap if not isinstance(rdap, Exception) else RDAPResult(domain=domain, error=str(rdap)),
        virustotal=vt if not isinstance(vt, Exception) else VirusTotalResult(url=normalized, error=str(vt)),
        urlscan=urlscan if not isinstance(urlscan, Exception) else URLScanResult(url=normalized, error=str(urlscan)),
        pagerank=pr if not isinstance(pr, Exception) else PageRankResult(domain=domain, error=str(pr)),
    )


# ── Serialização ──────────────────────────────────────────────────────────────

def serialize_domain_response(r: DomainCheckResponse) -> dict:
    """Converte DomainCheckResponse em dict JSON-serializável."""
    return {
        "url": r.url,
        "domain": r.domain,
        "error": r.error,
        "rdap": {
            "registrar": r.rdap.registrar,
            "registrar_url": r.rdap.registrar_url,
            "creation_date": r.rdap.creation_date,
            "expiration_date": r.rdap.expiration_date,
            "last_changed_date": r.rdap.last_changed_date,
            "status": r.rdap.status,
            "name_servers": r.rdap.name_servers,
            "error": r.rdap.error,
        },
        "virustotal": {
            "malicious": r.virustotal.malicious,
            "suspicious": r.virustotal.suspicious,
            "harmless": r.virustotal.harmless,
            "undetected": r.virustotal.undetected,
            "reputation": r.virustotal.reputation,
            "last_analysis_date": r.virustotal.last_analysis_date,
            "error": r.virustotal.error,
        },
        "urlscan": {
            "scan_result_url": r.urlscan.scan_result_url,
            "screenshot_url": r.urlscan.screenshot_url,
            "ip": r.urlscan.ip,
            "country": r.urlscan.country,
            "server": r.urlscan.server,
            "malicious": r.urlscan.malicious,
            "scan_date": r.urlscan.scan_date,
            "total_scans_found": r.urlscan.total_scans_found,
            "error": r.urlscan.error,
        },
        "pagerank": {
            "page_rank_decimal": r.pagerank.page_rank_decimal,
            "rank": r.pagerank.rank,
            "error": r.pagerank.error,
        },
    }
