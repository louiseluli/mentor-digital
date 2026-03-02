"""
wikipedia_api.py — Busca de contexto na Wikipedia (Fase 11.x)

Sem API key. Timeout 8s. Falha sempre silenciosa.

Fluxo:
  1. Search API: /w/api.php?action=query&list=search&srsearch={query}
  2. Summary REST: /api/rest_v1/page/summary/{title}

Retorna até 2 artigos por idioma (PT e EN chamados em paralelo pelo caller).
"""

import logging

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 8.0
MAX_RESULTS = 2
EXTRACT_MAX_LEN = 300


async def search_wikipedia(query: str, lang: str = "pt") -> dict:
    """Busca artigos na Wikipedia para contextualizar afirmações verificáveis.

    Args:
        query: texto de busca extraído do conteúdo enviado pelo usuário.
        lang: código ISO do idioma ('pt' ou 'en').

    Returns:
        {
            "query": str,
            "results": [{"title", "extract", "url", "thumbnail"}],
            "error": str,  # vazio se sucesso
        }
    """
    if not query:
        return {"query": query, "results": [], "error": "empty query"}

    base = f"https://{lang}.wikipedia.org"

    headers = {
        "User-Agent": "MentorDigital/1.0 (https://github.com/louiseluli/mentor-digital; mentor-digital@example.com) httpx/0.27",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=headers) as client:
            # ── 1. Busca por título ──────────────────────────────────────────
            search_resp = await client.get(
                f"{base}/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": MAX_RESULTS + 1,  # pedir um a mais para filtrar ruins
                    "format": "json",
                    "utf8": 1,
                },
            )
            search_resp.raise_for_status()
            hits = search_resp.json().get("query", {}).get("search", [])

            if not hits:
                return {"query": query, "results": [], "error": ""}

            # ── 2. Resumo de cada artigo ──────────────────────────────────────
            results = []
            for hit in hits[:MAX_RESULTS]:
                title = hit["title"]
                try:
                    summary_resp = await client.get(
                        f"{base}/api/rest_v1/page/summary/{title.replace(' ', '_')}",
                        headers={"Accept": "application/json"},
                    )
                    if summary_resp.status_code != 200:
                        continue
                    s = summary_resp.json()
                    extract = s.get("extract", "")
                    if not extract or s.get("type") == "disambiguation":
                        continue
                    results.append(
                        {
                            "title": s.get("title", title),
                            "extract": extract[:EXTRACT_MAX_LEN],
                            "url": s.get("content_urls", {})
                                    .get("desktop", {})
                                    .get("page", f"{base}/wiki/{title.replace(' ', '_')}"),
                            "thumbnail": s.get("thumbnail", {}).get("source", ""),
                            "lang": lang,
                        }
                    )
                except Exception as exc:
                    logger.debug("Wikipedia summary failed for '%s': %s", title, exc)

            return {"query": query, "results": results, "error": ""}

    except httpx.TimeoutException:
        logger.warning("Wikipedia timeout | lang=%s | query=%r", lang, query[:60])
        return {"query": query, "results": [], "error": "timeout"}
    except Exception as exc:
        logger.warning("Wikipedia error | lang=%s | error=%s", lang, exc)
        return {"query": query, "results": [], "error": str(exc)}
