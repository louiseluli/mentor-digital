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


# ══════════════════════════════════════════════════════════════════════════════
# NOVOS TESTES — Padrões baseados em datasets acadêmicos
# (LIAR, FakeNewsNet, CHECKED, NELA-GT, PHEME, FakevsSatire,
#  Garg & Sharma 2022, Choudhary & Arora 2021, Horne & Adali 2017)
# ══════════════════════════════════════════════════════════════════════════════

# ── Anti-vacina (PT) ────────────────────────────────────────────────────────

class TestAntiVaxPT:
    def test_nao_vacine_filhos(self):
        result = analyze_text("NÃO VACINE seu filho! A vacina mata crianças e causa autismo")
        assert result.manipulation.score >= 0.40, f"manipulation={result.manipulation.score}"
        assert any("anti-vax" in e for e in result.manipulation.evidence)

    def test_vacina_mata(self):
        result = analyze_text("A vacina mata milhares de pessoas todos os anos")
        assert result.manipulation.score >= 0.30

    def test_vacina_veneno(self):
        result = analyze_text("A vacina é veneno puro que estão injetando nas crianças")
        assert result.manipulation.score >= 0.40

    def test_efeitos_colaterais_escondidos(self):
        result = analyze_text("Os efeitos colaterais escondidos da vacina são terríveis")
        assert result.manipulation.score >= 0.30
        assert any("efeitos colaterais" in e for e in result.manipulation.evidence)

    def test_ingredientes_toxicos(self):
        result = analyze_text("Esta vacina contém ingredientes tóxicos como mercúrio e alumínio")
        assert result.manipulation.score >= 0.40

    def test_mortes_pos_vacina(self):
        result = analyze_text("Já registraram 500 mortes após vacinação no Brasil")
        assert result.manipulation.score >= 0.30


# ── Anti-vacina (EN) ────────────────────────────────────────────────────────

class TestAntiVaxEN:
    def test_dont_vaccinate(self):
        result = analyze_text("Don't vaccinate your children! The vaccine is deadly poison")
        assert result.manipulation.score >= 0.40

    def test_vaccine_kills(self):
        result = analyze_text("The vaccine kills thousands of people every year")
        assert result.manipulation.score >= 0.30

    def test_vaccine_autism(self):
        result = analyze_text("The vaccine causes autism in children, studies confirm it")
        assert result.manipulation.score >= 0.30
        assert any("autism" in e for e in result.manipulation.evidence)

    def test_hidden_side_effects(self):
        result = analyze_text("They don't want you to know about the hidden side effects")
        assert result.manipulation.score >= 0.40

    def test_rushed_vaccine(self):
        result = analyze_text("This rushed vaccine was never properly tested on humans")
        assert result.manipulation.score >= 0.30


# ── Negação Científica (PT) ─────────────────────────────────────────────────

class TestScienceDenialPT:
    def test_nasa_admitiu(self):
        result = analyze_text("NASA admitiu que a Terra é plana e que nunca pisamos na Lua")
        assert result.manipulation.score >= 0.40
        assert any("NASA" in e or "admitiu" in e for e in result.manipulation.evidence)

    def test_aquecimento_global_farsa(self):
        result = analyze_text("O aquecimento global é uma farsa criada para controlar a população")
        assert result.manipulation.score >= 0.40

    def test_cientistas_mentem(self):
        result = analyze_text("Os cientistas mentem para ganhar financiamento do governo")
        assert result.manipulation.score >= 0.30

    def test_dados_manipulados(self):
        result = analyze_text("Os dados foram manipulados para justificar o lockdown")
        assert result.manipulation.score >= 0.30

    def test_consenso_falso(self):
        result = analyze_text("O consenso científico é falso e comprado pela indústria")
        assert result.manipulation.score >= 0.40


# ── Negação Científica (EN) ─────────────────────────────────────────────────

class TestScienceDenialEN:
    def test_global_warming_hoax(self):
        result = analyze_text("Global warming is a hoax created by the elite to control us")
        assert result.manipulation.score >= 0.40

    def test_scientists_lie(self):
        result = analyze_text("Scientists lie about climate change for grant money")
        assert result.manipulation.score >= 0.30

    def test_data_fabricated(self):
        result = analyze_text("The data was fabricated to justify the government response")
        assert result.manipulation.score >= 0.30

    def test_evolution_just_theory(self):
        result = analyze_text("Evolution is just a theory that has never been proven")
        assert result.manipulation.score >= 0.30


# ── Desinformação de Saúde (PT) ─────────────────────────────────────────────

class TestHealthDisinfoPT:
    def test_ivermectina_cura(self):
        result = analyze_text("Ivermectina cura COVID-19 em 48 horas, médicos proibidos de falar")
        assert result.manipulation.score >= 0.50

    def test_cha_cura(self):
        result = analyze_text("Chá de boldo cura o câncer em 30 dias, pesquisem vocês mesmos")
        assert result.manipulation.score >= 0.40

    def test_quimioterapia_veneno(self):
        result = analyze_text("Quimioterapia é veneno puro. A cura do câncer escondida pela indústria")
        assert result.manipulation.score >= 0.50

    def test_nao_existe_virus(self):
        result = analyze_text("Não existe vírus, isso é tudo uma farsa para vender vacina")
        assert result.manipulation.score >= 0.40

    def test_protocolo_proibido(self):
        result = analyze_text("Existe um protocolo proibido que os médicos não podem revelar")
        assert result.manipulation.score >= 0.40


# ── Desinformação de Saúde (EN) ─────────────────────────────────────────────

class TestHealthDisinfoEN:
    def test_ivermectin_cures(self):
        result = analyze_text("Ivermectin cures COVID in 48 hours, doctors banned from speaking")
        assert result.manipulation.score >= 0.50

    def test_lemon_water_cures(self):
        result = analyze_text("Lemon water cures cancer naturally, do your own research")
        assert result.manipulation.score >= 0.40

    def test_chemo_is_poison(self):
        result = analyze_text("Chemotherapy is poison, cancer cure hidden by big pharma")
        assert result.manipulation.score >= 0.50

    def test_covid_is_flu(self):
        result = analyze_text("COVID is just a flu, the pandemic doesn't exist")
        assert result.manipulation.score >= 0.40


# ── Atribuição Vaga de Fontes ────────────────────────────────────────────────

class TestVagueAttrPT:
    def test_dizem_que(self):
        result = analyze_text("Dizem que o governo está escondendo a verdade sobre a vacina")
        assert result.manipulation.score >= 0.20

    def test_pesquisem_voces_mesmos(self):
        result = analyze_text("Pesquisem vocês mesmos, a mídia não vai mostrar isso")
        assert result.manipulation.score >= 0.30

    def test_vi_no_whatsapp(self):
        result = analyze_text("Vi no WhatsApp que a vacina causa problemas graves")
        assert result.manipulation.score >= 0.20


class TestVagueAttrEN:
    def test_they_say(self):
        result = analyze_text("They say the government is hiding the truth about the vaccine")
        assert result.manipulation.score >= 0.20

    def test_do_your_own_research(self):
        result = analyze_text("Do your own research, the media won't show you this")
        assert result.manipulation.score >= 0.30


# ── Apelo Emocional Infantil ─────────────────────────────────────────────────

class TestChildAppeal:
    def test_proteja_filhos_pt(self):
        result = analyze_text("Proteja seus filhos! Estão envenenando as crianças na escola")
        assert result.manipulation.score >= 0.40

    def test_children_dying_en(self):
        result = analyze_text("Children are dying from the vaccine, protect your kids now!")
        assert result.manipulation.score >= 0.40


# ── Golpe / Manipulação Financeira ───────────────────────────────────────────

class TestFinancialScam:
    def test_dinheiro_facil_pt(self):
        result = analyze_text("Ganhe dinheiro fácil trabalhando de casa, clique no link")
        assert result.manipulation.score >= 0.30

    def test_pyramid_scheme_en(self):
        result = analyze_text("This is not a pyramid scheme, invest now before it's too late")
        assert result.manipulation.score >= 0.40


# ── Hedging (Garg & Sharma 2022, Choudhary & Arora 2021) ────────────────────

class TestHedging:
    def test_no_hedging_boosts_manipulation(self):
        """Texto com afirmações e manipulação mas sem hedging → boost."""
        text = "A vacina mata crianças, cientistas mentem sobre os dados"
        result = analyze_text(text)
        assert any("sem hedging" in e for e in result.manipulation.evidence)

    def test_hedging_reduces_manipulation(self):
        """Texto com hedging presente → manipulação reduzida."""
        text = "Possivelmente pode haver efeitos colaterais, segundo alguns estudos"
        result = analyze_text(text)
        # Should not have high manipulation
        assert result.manipulation.score < 0.30

    def test_legitimate_news_low_score(self):
        """Notícia legítima com hedging e fontes deve ter score baixo."""
        text = ("Segundo pesquisadores da Universidade de São Paulo, "
                "o medicamento pode ter potencial terapêutico, "
                "embora mais estudos sejam necessários para confirmar os resultados.")
        result = analyze_text(text)
        assert result.manipulation.score < 0.15, f"manipulation={result.manipulation.score}"


# ── Textos completos: integração PT + EN ────────────────────────────────

class TestFullTextIntegration:
    def test_antivax_complete_pt(self):
        """Texto anti-vax completo em PT deve receber score alto."""
        text = (
            "URGENTE! NÃO VACINE SEU FILHO! A vacina da dengue mata crianças. "
            "Os efeitos colaterais escondidos são terríveis. O governo esconde "
            "a verdade porque a indústria farmacêutica paga bilhões. "
            "Pesquisem vocês mesmos antes que censurem! Compartilhem!!!"
        )
        result = analyze_text(text)
        assert result.manipulation.score >= 0.60, f"manipulation={result.manipulation.score}"
        assert result.urgency.score >= 0.30, f"urgency={result.urgency.score}"

    def test_antivax_complete_en(self):
        """Texto anti-vax completo em EN deve receber score alto."""
        text = (
            "BREAKING! Don't vaccinate your children! The vaccine kills "
            "thousands and they're hiding the side effects. Big pharma "
            "doesn't want you to know the truth. Do your own research!"
        )
        result = analyze_text(text)
        assert result.manipulation.score >= 0.60, f"manipulation={result.manipulation.score}"

    def test_science_denial_complete_pt(self):
        """Texto de negação científica completo em PT."""
        text = (
            "NASA admitiu que a Terra é plana! Os cientistas mentem e "
            "os dados foram manipulados. O consenso científico é falso, "
            "é tudo farsa para controlar a população."
        )
        result = analyze_text(text)
        assert result.manipulation.score >= 0.60, f"manipulation={result.manipulation.score}"

    def test_health_misinfo_complete_pt(self):
        """Texto de desinformação de saúde completo em PT."""
        text = (
            "Ivermectina cura COVID em 48 horas mas os médicos proibidos "
            "de falar a verdade. A quimioterapia é veneno, a cura do câncer "
            "é escondida pela indústria farmacêutica para lucrar."
        )
        result = analyze_text(text)
        assert result.manipulation.score >= 0.60, f"manipulation={result.manipulation.score}"

    def test_legitimate_news_stays_low(self):
        """Uma notícia legítima não deve receber score alto."""
        text = (
            "Segundo dados do IBGE divulgados nesta terça-feira, a taxa de "
            "desemprego no Brasil ficou em 7,4% no trimestre encerrado em "
            "outubro, uma queda de 0,3 ponto percentual em relação ao "
            "trimestre anterior. Os números indicam uma recuperação "
            "gradual do mercado de trabalho brasileiro."
        )
        result = analyze_text(text)
        assert result.manipulation.score < 0.20, f"manipulation={result.manipulation.score}"
        assert result.urgency.score < 0.20, f"urgency={result.urgency.score}"

    def test_legitimate_science_stays_low(self):
        """Texto científico legítimo não deve disparar negação científica."""
        text = (
            "Researchers at the University of Cambridge published a study "
            "suggesting that the new treatment may reduce symptoms by 30%. "
            "However, more clinical trials are needed. The results, while "
            "promising, should be interpreted with caution."
        )
        result = analyze_text(text)
        assert result.manipulation.score < 0.15, f"manipulation={result.manipulation.score}"
