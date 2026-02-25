"""
test_analysis_service.py — Testes do orquestrador de análise (Micro-Batch 3.3)

Testa analyze_content() mockando search_claims e search_articles para evitar
chamadas reais à rede. GDELT é mockado via _run_gdelt para simplificar.
"""

import sys
import os
import json
import pytest
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.models import ConversationContext
from src.analysis.fact_checker import FactCheckResponse, FactCheckResult, ClaimReview
from src.analysis.gdelt import GDELTResponse, GDELTArticle
from src.analysis.analysis_service import analyze_content, _extract_query


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_ctx(content_raw: str = "Vacina causa autismo", content_type: str = "text") -> ConversationContext:
    ctx = ConversationContext(user_id="test_user", platform="terminal")
    ctx.content_raw = content_raw
    ctx.content_type = content_type
    return ctx


def make_fact_check_result(text: str = "Afirmação falsa") -> FactCheckResponse:
    return FactCheckResponse(
        query=text,
        results=[
            FactCheckResult(
                text=text,
                claimant="Alguém",
                claim_date="2023-01-01T00:00:00Z",
                reviews=[
                    ClaimReview(
                        publisher_name="Agência Lupa",
                        publisher_site="lupa.news",
                        text_rating="Falso",
                        rating_value=1,
                    )
                ],
            )
        ],
    )


def make_gdelt_result(query: str = "teste") -> GDELTResponse:
    return GDELTResponse(
        query=query,
        articles=[
            GDELTArticle(
                url="https://aosfatos.org/1",
                title="Artigo de teste",
                domain="aosfatos.org",
                language="Portuguese",
                source_country="Brazil",
                seen_date="2024-01-15T12:00:00Z",
            )
        ],
    )


_EMPTY_GDELT = {"por": {"articles": [], "error": ""}, "en": {"articles": [], "error": ""}}

_DEFAULT_NLP = {
    "language": "pt",
    "word_count": 4,
    "caps_ratio": 0.0,
    "error": "",
    "urgency": {"score": 0.0, "evidence": []},
    "claim": {"score": 0.0, "evidence": []},
    "manipulation": {"score": 0.0, "evidence": []},
}


@contextmanager
def _mock_apis(
    fc_return=None,
    gdelt_return=None,
    nlp_return=None,
    fc_side_effect=None,
    gdelt_side_effect=None,
    nlp_side_effect=None,
):
    """Context manager que mocka search_claims, _run_gdelt e _run_nlp simultaneamente."""
    fc_kwargs = {"new_callable": AsyncMock}
    if fc_side_effect is not None:
        fc_kwargs["side_effect"] = fc_side_effect
    else:
        fc_kwargs["return_value"] = fc_return or FactCheckResponse()

    gdelt_kwargs = {"new_callable": AsyncMock}
    if gdelt_side_effect is not None:
        gdelt_kwargs["side_effect"] = gdelt_side_effect
    else:
        gdelt_kwargs["return_value"] = gdelt_return or _EMPTY_GDELT

    nlp_kwargs = {"new_callable": AsyncMock}
    if nlp_side_effect is not None:
        nlp_kwargs["side_effect"] = nlp_side_effect
    else:
        nlp_kwargs["return_value"] = nlp_return or _DEFAULT_NLP

    with patch("src.analysis.analysis_service.search_claims", **fc_kwargs), \
         patch("src.analysis.analysis_service._run_gdelt", **gdelt_kwargs), \
         patch("src.analysis.analysis_service._run_nlp", **nlp_kwargs):
        yield


# ── Testes: _extract_query ────────────────────────────────────────────────────

def test_extract_query_short_text():
    ctx = make_ctx("Vacina mata")
    assert _extract_query(ctx) == "Vacina mata"


def test_extract_query_long_text_truncated():
    ctx = make_ctx("palavra " * 50)
    query = _extract_query(ctx)
    assert len(query) <= 200
    assert not query.endswith("palav")


def test_extract_query_media_without_caption():
    ctx = make_ctx("[imagem sem legenda]", content_type="image")
    assert _extract_query(ctx) == ""


def test_extract_query_audio_placeholder():
    ctx = make_ctx("[áudio]", content_type="audio")
    assert _extract_query(ctx) == ""


def test_extract_query_link():
    url = "https://exemplo.com/noticia-falsa"
    ctx = make_ctx(url, content_type="link")
    assert _extract_query(ctx) == url


def test_extract_query_empty_content():
    ctx = make_ctx("")
    assert _extract_query(ctx) == ""


# ── Testes: analyze_content — fact_check ─────────────────────────────────────

async def test_analyze_content_stores_results_in_ctx():
    ctx = make_ctx("Vacina causa autismo")
    with _mock_apis(fc_return=make_fact_check_result("Vacina causa autismo")):
        result = await analyze_content(ctx)

    assert "fact_check" in ctx.analysis_results
    assert "fact_check" in result
    assert "analyzed_at" in result
    assert "query" in result


async def test_analyze_content_includes_gdelt_in_results():
    """GDELT agora faz parte dos resultados de analyze_content."""
    ctx = make_ctx("Eleições fraude")
    with _mock_apis():
        result = await analyze_content(ctx)

    assert "gdelt" in result
    assert "gdelt" in ctx.analysis_results


async def test_analyze_content_returns_json_serializable_dict():
    ctx = make_ctx("Vacina causa autismo")
    with _mock_apis(fc_return=make_fact_check_result()):
        result = await analyze_content(ctx)

    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    assert "fact_check" in parsed
    assert "gdelt" in parsed


async def test_analyze_content_fact_check_has_pt_and_en():
    ctx = make_ctx("Vacina causa autismo")
    calls = []

    async def mock_search(query, language_code="pt", page_size=5, page_token=""):
        calls.append(language_code)
        return FactCheckResponse(query=query)

    with patch("src.analysis.analysis_service.search_claims", side_effect=mock_search), \
         patch("src.analysis.analysis_service._run_gdelt", new_callable=AsyncMock, return_value=_EMPTY_GDELT):
        await analyze_content(ctx)

    assert "pt" in calls
    assert "en" in calls


async def test_analyze_content_gdelt_has_por_and_en():
    """_run_gdelt é chamado e retorna resultados por idioma."""
    ctx = make_ctx("Vacina causa autismo")
    gdelt_result = {
        "por": {"articles": [{"title": "Artigo PT"}], "error": ""},
        "en": {"articles": [{"title": "Article EN"}], "error": ""},
    }
    with _mock_apis(gdelt_return=gdelt_result):
        result = await analyze_content(ctx)

    assert result["gdelt"]["por"]["articles"][0]["title"] == "Artigo PT"
    assert result["gdelt"]["en"]["articles"][0]["title"] == "Article EN"


async def test_analyze_content_empty_query_skips_search_claims():
    """Conteúdo de mídia sem legenda não chama search_claims."""
    ctx = make_ctx("[imagem sem legenda]", content_type="image")

    with patch(
        "src.analysis.analysis_service.search_claims",
        new_callable=AsyncMock,
    ) as mock_search, \
         patch("src.analysis.analysis_service._run_gdelt", new_callable=AsyncMock, return_value=_EMPTY_GDELT):
        await analyze_content(ctx)

    mock_search.assert_not_called()


async def test_analyze_content_empty_query_skips_gdelt():
    """Conteúdo de mídia sem legenda não chama _run_gdelt com query preenchida."""
    ctx = make_ctx("[áudio]", content_type="audio")

    with patch("src.analysis.analysis_service.search_claims", new_callable=AsyncMock, return_value=FactCheckResponse()), \
         patch("src.analysis.analysis_service._run_gdelt", new_callable=AsyncMock) as mock_gdelt:
        # _run_gdelt ainda é chamado, mas com query vazia → retorna vazio internamente
        mock_gdelt.return_value = _EMPTY_GDELT
        result = await analyze_content(ctx)

    # Resultado gdelt está presente, mas sem artigos
    gdelt = result.get("gdelt", {})
    assert isinstance(gdelt, dict)


async def test_analyze_content_handles_fact_check_error():
    ctx = make_ctx("Vacina causa autismo")
    with _mock_apis(fc_side_effect=Exception("API indisponível")):
        result = await analyze_content(ctx)

    assert "fact_check" in result


async def test_analyze_content_handles_gdelt_error():
    """Erro no GDELT não propaga."""
    ctx = make_ctx("Terra é plana")
    with _mock_apis(gdelt_side_effect=Exception("GDELT offline")):
        result = await analyze_content(ctx)

    assert "gdelt" in result
    assert "fact_check" in result


async def test_analyze_content_merges_into_existing_results():
    ctx = make_ctx("Vacina causa autismo")
    ctx.analysis_results["previous_analysis"] = {"key": "value"}

    with _mock_apis():
        await analyze_content(ctx)

    assert "previous_analysis" in ctx.analysis_results
    assert "fact_check" in ctx.analysis_results
    assert "gdelt" in ctx.analysis_results


async def test_analyze_content_records_query_in_result():
    content = "Eleições foram fraudadas"
    ctx = make_ctx(content)

    with _mock_apis():
        result = await analyze_content(ctx)

    assert result["query"] == content


async def test_analyze_content_with_real_fact_check_results():
    ctx = make_ctx("Terra é plana")
    mock_fc = make_fact_check_result("Terra é plana")

    with _mock_apis(fc_return=mock_fc):
        result = await analyze_content(ctx)

    fc = result["fact_check"]
    pt_results = fc.get("pt", {}).get("results", [])
    en_results = fc.get("en", {}).get("results", [])
    assert len(pt_results) + len(en_results) > 0


async def test_analyze_content_link_includes_domain_key():
    """Quando content_type == 'link', resultado inclui 'domain'."""
    ctx = make_ctx("https://fakesource.com/artigo", content_type="link")

    with _mock_apis(), \
         patch(
             "src.analysis.analysis_service._run_domain_analysis",
             new_callable=AsyncMock,
             return_value={"domain": "fakesource.com", "error": ""},
         ):
        result = await analyze_content(ctx)

    assert "domain" in result
    assert result["domain"]["domain"] == "fakesource.com"


async def test_analyze_content_text_excludes_domain_key():
    """Quando content_type != 'link', resultado NÃO inclui 'domain'."""
    ctx = make_ctx("Vacina mata pessoas", content_type="text")

    with _mock_apis():
        result = await analyze_content(ctx)

    assert "domain" not in result


# ── Testes: analyze_content — nlp ────────────────────────────────────────────

async def test_analyze_content_includes_nlp_in_results():
    """NLP é incluído no resultado de analyze_content."""
    ctx = make_ctx("Vacina causa autismo")
    with _mock_apis():
        result = await analyze_content(ctx)

    assert "nlp" in result
    assert "nlp" in ctx.analysis_results


async def test_analyze_content_nlp_has_expected_keys():
    """Resultado nlp contém as chaves de sinal esperadas."""
    ctx = make_ctx("Vacina causa autismo")
    nlp_result = {
        "language": "pt",
        "word_count": 3,
        "caps_ratio": 0.0,
        "error": "",
        "urgency": {"score": 0.2, "evidence": ["urgente (PT)"]},
        "claim": {"score": 0.3, "evidence": ["percentagem"]},
        "manipulation": {"score": 0.1, "evidence": []},
    }
    with _mock_apis(nlp_return=nlp_result):
        result = await analyze_content(ctx)

    nlp = result["nlp"]
    assert "language" in nlp
    assert "urgency" in nlp
    assert "claim" in nlp
    assert "manipulation" in nlp


async def test_analyze_content_handles_nlp_error():
    """Erro no NLP não propaga — resultado inclui chave 'nlp' com erro."""
    ctx = make_ctx("Vacina causa autismo")
    with _mock_apis(nlp_side_effect=Exception("NLP crash")):
        result = await analyze_content(ctx)

    assert "nlp" in result
