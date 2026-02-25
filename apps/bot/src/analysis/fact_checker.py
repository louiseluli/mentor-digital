"""
fact_checker.py — Cliente para a Google Fact Check Tools API (Micro-Batch 3.1)

Endpoint: GET https://factchecktools.googleapis.com/v1alpha1/claims:search
Documentação: https://developers.google.com/fact-check/tools/api/reference/rest

Comportamento seguro:
- Retorna FactCheckResponse vazio se GOOGLE_API_KEY não estiver configurada.
- Retorna FactCheckResponse com campo `error` em caso de falha de rede ou HTTP.
- Nunca propaga exceções — o caller decide como tratar ausência de resultados.

Configuração:
  1. Google Cloud Console → Biblioteca → "Fact Check Tools API" → Ativar
  2. Credenciais → Criar chave de API → copiar para .env como GOOGLE_API_KEY
  3. (Opcional) Restringir a chave ao IP do servidor em produção.
"""

import os
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
DEFAULT_PAGE_SIZE = 5
DEFAULT_TIMEOUT = 10.0  # segundos


# ── Dataclasses de resposta ──────────────────────────────────────────────────

@dataclass
class ClaimReview:
    """Revisão de uma afirmação por uma organização de fact-check."""
    publisher_name: str = ""
    publisher_site: str = ""
    url: str = ""
    title: str = ""
    review_date: str = ""
    text_rating: str = ""      # Ex.: "Falso", "Enganoso", "Verdadeiro"
    rating_value: int = 0      # 1–7 escala Google (1=falso, 7=verdadeiro), 0=não disponível
    language_code: str = ""


@dataclass
class FactCheckResult:
    """Uma afirmação verificada e suas revisões."""
    text: str = ""             # Texto da alegação
    claimant: str = ""         # Quem fez a alegação
    claim_date: str = ""       # Data da alegação (ISO 8601)
    reviews: list = field(default_factory=list)  # list[ClaimReview]


@dataclass
class FactCheckResponse:
    """Resposta completa da API — sempre retornada, mesmo em caso de erro."""
    query: str = ""
    results: list = field(default_factory=list)   # list[FactCheckResult]
    error: str = ""            # Preenchido em caso de falha; vazio = sucesso
    next_page_token: str = ""  # Para paginação futura


# ── Parsing ──────────────────────────────────────────────────────────────────

def _parse_review(raw: dict) -> ClaimReview:
    publisher = raw.get("publisher", {})
    rating = raw.get("reviewRating", {})
    return ClaimReview(
        publisher_name=publisher.get("name", ""),
        publisher_site=publisher.get("site", ""),
        url=raw.get("url", ""),
        title=raw.get("title", ""),
        review_date=raw.get("reviewDate", ""),
        text_rating=raw.get("textualRating", ""),
        rating_value=int(rating.get("ratingValue", 0)),
        language_code=raw.get("languageCode", ""),
    )


def _parse_claim(raw: dict) -> FactCheckResult:
    return FactCheckResult(
        text=raw.get("text", ""),
        claimant=raw.get("claimant", ""),
        claim_date=raw.get("claimDate", ""),
        reviews=[_parse_review(r) for r in raw.get("claimReview", [])],
    )


def _parse_response(query: str, data: dict) -> FactCheckResponse:
    return FactCheckResponse(
        query=query,
        results=[_parse_claim(c) for c in data.get("claims", [])],
        next_page_token=data.get("nextPageToken", ""),
    )


# ── API client ───────────────────────────────────────────────────────────────

async def search_claims(
    query: str,
    language_code: str = "pt",
    page_size: int = DEFAULT_PAGE_SIZE,
    page_token: str = "",
) -> FactCheckResponse:
    """Busca alegações verificadas relacionadas à query na Google Fact Check Tools API.

    Args:
        query:         Texto a buscar (URL, frase, nome de pessoa, etc.).
        language_code: Código BCP-47 do idioma preferido (ex: "pt", "en", "es", "fr").
                       A API retorna resultados em múltiplos idiomas se houver.
        page_size:     Número de resultados por página (máx. 10 pela API).
        page_token:    Token para buscar próxima página (paginação futura).

    Returns:
        FactCheckResponse com `results` preenchido, ou `error` em caso de falha.
        Retorna response vazio (sem erro) se GOOGLE_API_KEY não estiver configurada.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        logger.debug("GOOGLE_API_KEY não configurada — fact-check ignorado.")
        return FactCheckResponse(query=query)

    params: dict = {
        "query": query,
        "languageCode": language_code,
        "pageSize": min(page_size, 10),  # API limita a 10
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(FACT_CHECK_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("Fact Check API HTTP %s para query=%r", status, query)
        return FactCheckResponse(query=query, error=f"HTTP {status}")

    except httpx.TimeoutException:
        logger.warning("Fact Check API timeout para query=%r", query)
        return FactCheckResponse(query=query, error="timeout")

    except Exception as exc:
        logger.error("Fact Check API erro inesperado: %s", exc)
        return FactCheckResponse(query=query, error=str(exc))

    return _parse_response(query, data)


# ── Helpers de serialização ──────────────────────────────────────────────────

def serialize_response(response: FactCheckResponse) -> dict:
    """Converte FactCheckResponse em dict JSON-serializável para armazenamento."""
    return {
        "query": response.query,
        "error": response.error,
        "next_page_token": response.next_page_token,
        "results": [
            {
                "text": r.text,
                "claimant": r.claimant,
                "claim_date": r.claim_date,
                "reviews": [
                    {
                        "publisher_name": rv.publisher_name,
                        "publisher_site": rv.publisher_site,
                        "url": rv.url,
                        "title": rv.title,
                        "review_date": rv.review_date,
                        "text_rating": rv.text_rating,
                        "rating_value": rv.rating_value,
                        "language_code": rv.language_code,
                    }
                    for rv in r.reviews
                ],
            }
            for r in response.results
        ],
    }
