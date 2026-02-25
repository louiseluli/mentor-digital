"""
test_nlp.py — Testes do analisador NLP local baseado em regras (Micro-Batch 3.4)

Todos os testes são síncronos (analyze_text é síncrono, sem IO).
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

from src.analysis.nlp import (
    analyze_text,
    serialize_nlp_result,
    NLPResult,
    NLPSignal,
)


# ── Testes: entradas inválidas ────────────────────────────────────────────────

def test_analyze_text_empty_returns_error():
    result = analyze_text("")
    assert result.error != ""


def test_analyze_text_placeholder_audio_returns_error():
    result = analyze_text("[áudio]")
    assert result.error != ""


def test_analyze_text_placeholder_image_returns_error():
    result = analyze_text("[imagem sem legenda]")
    assert result.error != ""


def test_analyze_text_empty_scores_are_zero():
    result = analyze_text("")
    assert result.urgency.score == 0.0
    assert result.claim.score == 0.0
    assert result.manipulation.score == 0.0


# ── Testes: word_count ────────────────────────────────────────────────────────

def test_analyze_text_word_count():
    result = analyze_text("Vacina causa autismo segundo estudo")
    assert result.word_count == 5


def test_analyze_text_word_count_empty():
    result = analyze_text("")
    assert result.word_count == 0


# ── Testes: detecção de idioma ────────────────────────────────────────────────

def test_analyze_text_detects_portuguese():
    text = "A vacina não causa autismo, isso é uma mentira que não tem base científica"
    result = analyze_text(text)
    assert result.language == "pt"


def test_analyze_text_detects_english():
    text = "The vaccine does not cause autism, this is a lie that has no scientific basis"
    result = analyze_text(text)
    assert result.language == "en"


def test_analyze_text_language_is_string():
    result = analyze_text("xyz 123 abc")
    assert isinstance(result.language, str)


# ── Testes: urgência ──────────────────────────────────────────────────────────

def test_analyze_text_urgency_low_for_neutral():
    result = analyze_text("Hoje está um bom dia para sair e passear no parque.")
    assert result.urgency.score < 0.30


def test_analyze_text_urgency_high_for_urgent_pt():
    result = analyze_text("URGENTE! Compartilhe antes que deletem! Vai sair do ar!")
    assert result.urgency.score >= 0.50


def test_analyze_text_urgency_has_evidence():
    result = analyze_text("Urgente compartilhe antes que apaguem essa informação!")
    assert len(result.urgency.evidence) > 0


def test_analyze_text_urgency_before_delete_pattern():
    result = analyze_text("Veja antes que deletem este vídeo importante")
    assert result.urgency.score > 0.0


def test_analyze_text_urgency_share_now_en():
    result = analyze_text("Share now before they delete this!")
    assert result.urgency.score > 0.0


def test_analyze_text_urgency_caps_boost():
    """CAPS > 20% deve aumentar urgência e registrar evidência."""
    result = analyze_text("VACINA MATA PESSOAS inocentes agora urgente")
    assert result.caps_ratio > 0.20
    assert any("CAPS" in e for e in result.urgency.evidence)


def test_analyze_text_urgency_caps_manipulation_boost():
    """CAPS > 40% deve também aumentar manipulação."""
    result = analyze_text("URGENTE VACINA MATA CHIP GOVERNO ESCONDE TUDO VERDADE REAL")
    assert result.caps_ratio > 0.40
    assert any("CAPS" in e for e in result.manipulation.evidence)


# ── Testes: afirmações verificáveis ──────────────────────────────────────────

def test_analyze_text_claim_low_for_neutral():
    result = analyze_text("Hoje está um bom dia para sair e passear no parque.")
    assert result.claim.score < 0.30


def test_analyze_text_claim_high_for_statistics():
    text = (
        "Segundo estudo da OMS, 90% das crianças vacinadas desenvolvem complicações. "
        "Pesquisa da Fiocruz confirma que sempre há risco."
    )
    result = analyze_text(text)
    assert result.claim.score >= 0.40


def test_analyze_text_claim_percentage_evidence():
    result = analyze_text("90% dos brasileiros apoiam essa medida")
    assert result.claim.score > 0.0
    assert any("percentagem" in e for e in result.claim.evidence)


def test_analyze_text_claim_authority_organism():
    result = analyze_text("Segundo especialistas da OMS, isso está comprovado")
    assert result.claim.score > 0.0
    assert len(result.claim.evidence) > 0


def test_analyze_text_claim_absolute_statement():
    result = analyze_text("Todos os médicos concordam que isso nunca acontece")
    assert result.claim.score > 0.0


def test_analyze_text_claim_confirmed_truth():
    result = analyze_text("Está comprovado e confirmado por pesquisa universitária")
    assert result.claim.score > 0.0


# ── Testes: manipulação emocional ────────────────────────────────────────────

def test_analyze_text_manipulation_low_for_neutral():
    result = analyze_text("O parque municipal abriu suas portas para visitação.")
    assert result.manipulation.score < 0.30


def test_analyze_text_manipulation_high_for_conspiracy():
    text = (
        "O governo esconde a verdade sobre o chip que colocam nas vacinas. "
        "Eles não querem que você saiba da nova ordem mundial!"
    )
    result = analyze_text(text)
    assert result.manipulation.score >= 0.50


def test_analyze_text_manipulation_fear_death():
    result = analyze_text("Risco de vida para seus filhos! Epidemia se espalhando!")
    assert result.manipulation.score > 0.0
    assert len(result.manipulation.evidence) > 0


def test_analyze_text_manipulation_flat_earth():
    result = analyze_text("A terra plana é a verdade que o governo esconde")
    assert result.manipulation.score > 0.0


def test_analyze_text_manipulation_clickbait_secret():
    result = analyze_text("Segredo revelado: você não vai acreditar no que descobriram!")
    assert result.manipulation.score > 0.0


def test_analyze_text_manipulation_conspiracy_chip():
    result = analyze_text("O microchip está sendo instalado via 5G nas vacinas")
    assert result.manipulation.score > 0.0


def test_analyze_text_manipulation_nom():
    result = analyze_text("A nova ordem mundial está por trás disso tudo")
    assert result.manipulation.score >= 0.50


# ── Testes: estrutura dos sinais ─────────────────────────────────────────────

def test_analyze_text_signal_labels():
    result = analyze_text("Texto simples de teste")
    assert result.urgency.label == "urgência"
    assert result.claim.label == "afirmações verificáveis"
    assert result.manipulation.label == "manipulação emocional"


def test_analyze_text_scores_bounded_0_to_1():
    text = (
        "URGENTE! Compartilhe antes que deletem! Governo esconde chip nas vacinas! "
        "90% das pessoas morrem! OMS confirma! Nova Ordem Mundial!"
    )
    result = analyze_text(text)
    assert 0.0 <= result.urgency.score <= 1.0
    assert 0.0 <= result.claim.score <= 1.0
    assert 0.0 <= result.manipulation.score <= 1.0


def test_analyze_text_caps_ratio_bounded():
    result = analyze_text("URGENTE compartilhe")
    assert 0.0 <= result.caps_ratio <= 1.0


def test_analyze_text_text_stored_truncated():
    long_text = "abc " * 200  # 800 chars
    result = analyze_text(long_text)
    assert len(result.text) <= 500


def test_analyze_text_evidence_are_strings():
    result = analyze_text("Urgente! Compartilhe antes que deletem!")
    assert all(isinstance(e, str) for e in result.urgency.evidence)


# ── Testes: serialize_nlp_result ─────────────────────────────────────────────

def test_serialize_nlp_result_json_serializable():
    result = analyze_text("Vacina causa autismo segundo pesquisa")
    serialized = serialize_nlp_result(result)
    json_str = json.dumps(serialized)
    parsed = json.loads(json_str)
    assert "urgency" in parsed
    assert "claim" in parsed
    assert "manipulation" in parsed


def test_serialize_nlp_result_top_level_keys():
    result = analyze_text("Texto de teste")
    s = serialize_nlp_result(result)
    assert "language" in s
    assert "word_count" in s
    assert "caps_ratio" in s
    assert "error" in s
    assert "urgency" in s
    assert "claim" in s
    assert "manipulation" in s


def test_serialize_nlp_result_signal_keys():
    result = analyze_text("Texto de teste")
    s = serialize_nlp_result(result)
    for signal in ("urgency", "claim", "manipulation"):
        assert "score" in s[signal]
        assert "evidence" in s[signal]


def test_serialize_nlp_result_error_case():
    result = analyze_text("")
    s = serialize_nlp_result(result)
    assert s["error"] != ""


def test_serialize_nlp_result_scores_are_floats():
    result = analyze_text("Texto de teste")
    s = serialize_nlp_result(result)
    assert isinstance(s["urgency"]["score"], float)
    assert isinstance(s["claim"]["score"], float)
    assert isinstance(s["manipulation"]["score"], float)


def test_serialize_nlp_result_evidence_is_list():
    result = analyze_text("URGENTE compartilhe antes que deletem")
    s = serialize_nlp_result(result)
    assert isinstance(s["urgency"]["evidence"], list)


def test_serialize_nlp_result_word_count_is_int():
    result = analyze_text("Texto de teste com cinco palavras aqui")
    s = serialize_nlp_result(result)
    assert isinstance(s["word_count"], int)
