"""
brazilian_fc.py — Busca nos feeds RSS de verificadores brasileiros (Fase 12.x)

Fontes verificadas e ativas (fev/2026):
  - Aos Fatos       https://www.aosfatos.org/noticias/feed/   (~20 artigos recentes)
  - Agência Lupa    https://www.agencialupa.org/feed/          (~10 artigos recentes)

Estratégia: keyword-match entre termos extraídos da query e título/descrição de cada item.
Complementa o Google Fact Check API (que cobre as mesmas fontes via IFCN) com artigos
recentes ainda não indexados.

Cache: Redis 'mentor:br_fc:{hash}' TTL 1h para evitar bater nos feeds a cada análise.
Sem dependências externas além de httpx (já no requirements).
"""

import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, UTC

import httpx

logger = logging.getLogger(__name__)

FEEDS: dict[str, str] = {
    "Aos Fatos": "https://www.aosfatos.org/noticias/feed/",
    "Agência Lupa": "https://www.agencialupa.org/feed/",
}

TIMEOUT = 8.0
MAX_RESULTS = 5
MIN_KEYWORD_MATCH = 2   # mínimo de termos que devem aparecer no artigo

# Stopwords PT simples — sem NLTK
_STOPWORDS_PT = frozenset({
    "que", "com", "uma", "para", "por", "mas", "como", "não", "mais",
    "pelo", "pela", "dos", "das", "nos", "nas", "seu", "sua", "são",
    "está", "esse", "essa", "isto", "isso", "ele", "ela", "eles",
    "elas", "ser", "ter", "tem", "foi", "vai", "pode", "sobre",
    "entre", "desde", "quando", "porque", "também", "ainda", "muito",
    "nada", "tudo", "cada", "outro", "outra", "todos", "todas",
    "mesmo", "após", "antes", "depois", "além", "segundo",
})


# ── Extração de palavras-chave ────────────────────────────────────────────────

def _extract_keywords(query: str, max_terms: int = 8) -> list[str]:
    """Extrai termos significativos da query (>3 chars, sem stopwords PT)."""
    words = query.lower().split()
    keywords = [
        w.strip(".,!?;:\"'()[]{}") for w in words
        if len(w) > 3 and w not in _STOPWORDS_PT
    ]
    return list(dict.fromkeys(keywords))[:max_terms]  # preserva ordem, sem duplicatas


def _match_score(text: str, keywords: list[str]) -> int:
    """Conta quantos keywords aparecem no texto (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


# ── Parsing de RSS ────────────────────────────────────────────────────────────

_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def _parse_rss_items(xml_text: str, source_name: str) -> list[dict]:
    """Parse básico de RSS 2.0 — retorna lista de dicts com campos padronizados."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("RSS parse error (%s): %s", source_name, exc)
        return []

    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc_raw = (item.findtext("description") or "").strip()
        # Remove tags HTML simples da descrição
        import re
        desc = re.sub(r"<[^>]+>", " ", desc_raw).strip()[:300]
        pub_date = (item.findtext("pubDate") or "").strip()

        # Tenta converter data
        date_str = ""
        if pub_date:
            try:
                dt = parsedate_to_datetime(pub_date)
                date_str = dt.strftime("%d/%m/%Y")
            except Exception:
                date_str = pub_date[:10]

        if title and link:
            items.append({
                "title": title,
                "url": link,
                "date": date_str,
                "source": source_name,
                "snippet": desc,
            })

    return items


# ── Fetch + match por fonte ───────────────────────────────────────────────────

async def _fetch_and_match(
    source_name: str, feed_url: str, keywords: list[str]
) -> list[dict]:
    """Baixa feed RSS e retorna itens que contêm ≥ MIN_KEYWORD_MATCH termos."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "MentorDigital/1.0"})
            resp.raise_for_status()
        items = _parse_rss_items(resp.text, source_name)
    except httpx.TimeoutException:
        logger.warning("Brazilian FC timeout | source=%s", source_name)
        return []
    except Exception as exc:
        logger.warning("Brazilian FC fetch error | source=%s | error=%s", source_name, exc)
        return []

    matched = []
    for item in items:
        search_text = item["title"] + " " + item["snippet"]
        score = _match_score(search_text, keywords)
        if score >= MIN_KEYWORD_MATCH:
            item["_score"] = score
            matched.append(item)

    return matched


# ── Função pública ────────────────────────────────────────────────────────────

async def search_brazilian_fc(query: str, redis_client=None) -> dict:
    """Busca nos feeds RSS dos verificadores brasileiros por keyword-match.

    Args:
        query: texto da análise (até 200 chars extraídos pelo analysis_service).
        redis_client: cliente Redis opcional para cache de 1h.

    Returns:
        {
            "query": str,
            "results": [{"title","url","date","source","snippet"}],
            "error": str,
        }
    """
    if not query:
        return {"query": query, "results": [], "error": ""}

    # Cache Redis
    cache_key = f"mentor:br_fc:{hashlib.md5(query.encode()).hexdigest()}"
    if redis_client:
        try:
            import json
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    keywords = _extract_keywords(query)
    if len(keywords) < MIN_KEYWORD_MATCH:
        logger.debug("Brazilian FC: query muito curta/genérica — skip")
        return {"query": query, "results": [], "error": ""}

    tasks = [
        asyncio.create_task(_fetch_and_match(name, url, keywords))
        for name, url in FEEDS.items()
    ]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    combined: list[dict] = []
    for res in results_nested:
        if not isinstance(res, Exception):
            combined.extend(res)

    # Ordenar por score desc, manter no máximo MAX_RESULTS
    combined.sort(key=lambda x: (-x.get("_score", 0), x.get("date", "")))
    for item in combined:
        item.pop("_score", None)

    result = {"query": query, "results": combined[:MAX_RESULTS], "error": ""}

    # Persistir no cache (1h)
    if redis_client:
        try:
            import json
            redis_client.set(cache_key, json.dumps(result), ex=3600)
        except Exception:
            pass

    logger.info("Brazilian FC | keywords=%s | hits=%d", keywords[:4], len(combined))
    return result
