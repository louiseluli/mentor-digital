"""
nlp.py — Analisador NLP local baseado em regras ponderadas (Micro-Batch 3.4)

Sem modelo externo, sem download, sem chave de API.
Todas as regras, pesos e thresholds são configurados aqui.

Produz três sinais linguísticos com score 0.0–1.0 e evidências explicáveis:

  urgency_score        Linguagem que cria pressa/pânico para compartilhar imediatamente.
                       Alta pontuação → perguntar: "por que o texto quer que eu aja agora?"

  claim_score          Densidade de afirmações verificáveis (estatísticas, autoridade,
                       datas, fatos absolutos).
                       Alta pontuação → perguntar: "quais dessas afirmações podem ser checadas?"

  manipulation_score   Apelos emocionais para contornar o pensamento crítico
                       (medo, raiva, indignação, orgulho manipulador).
                       Alta pontuação → perguntar: "quais emoções esse conteúdo está tentando ativar?"

Os sinais alimentam a plataforma web (Fase 5).
O bot NÃO exibe os scores — eles são usados internamente para enriquecer o contexto.

Multilíngue: PT, EN, ES, FR (regras curadas para cada idioma).
"""

import re
from dataclasses import dataclass, field
from typing import NamedTuple


# ── Tipos internos ────────────────────────────────────────────────────────────

class _Rule(NamedTuple):
    """Uma regra de pontuação: padrão regex (case-insensitive) + peso + rótulo."""
    pattern: str    # regex compilado com re.IGNORECASE
    weight: float   # contribuição ao score (antes de capping)
    label: str      # evidência legível para o usuário


@dataclass
class NLPSignal:
    """Sinal linguístico com score e evidências que o justificam."""
    score: float = 0.0            # 0.0 (ausente) → 1.0 (forte)
    evidence: list = field(default_factory=list)  # list[str] — regras ativadas
    label: str = ""               # nome do sinal (ex: "urgência")


@dataclass
class NLPResult:
    """Resultado completo da análise NLP para um texto."""
    text: str = ""
    language: str = "unknown"     # "pt" | "en" | "es" | "fr" | "unknown"
    urgency: NLPSignal = field(default_factory=lambda: NLPSignal(label="urgência"))
    claim: NLPSignal = field(default_factory=lambda: NLPSignal(label="afirmações verificáveis"))
    manipulation: NLPSignal = field(default_factory=lambda: NLPSignal(label="manipulação emocional"))
    word_count: int = 0
    caps_ratio: float = 0.0       # proporção de palavras em MAIÚSCULAS (0.0–1.0)
    error: str = ""


# ── Base de regras — configuradas aqui ───────────────────────────────────────
#
# Estrutura: _Rule(r"padrão_regex", peso, "rótulo_legível")
# Pesos somam-se; o score final é min(soma, 1.0).
# Regras com peso maior capturam sinais mais fortes.
# Regras sobrepostas são esperadas — reforçam o sinal.

# ─────────────────────────────────────────────────────────────────────────────
# URGENCY: linguagem que cria senso de pressa / pânico para compartilhar
# ─────────────────────────────────────────────────────────────────────────────
_URGENCY_RULES: list[_Rule] = [
    # ── Chamadas à ação urgente (PT) ──────────────────────────────────────────
    _Rule(r'\burgente\b',                              0.35, "urgente (PT)"),
    _Rule(r'\bcompartilhe\b',                          0.20, "compartilhe (PT)"),
    _Rule(r'\brepasse\b',                              0.18, "repasse (PT)"),
    _Rule(r'\bpasse\s+(?:para|adiante)\b',             0.15, "passe adiante (PT)"),
    _Rule(r'\bavise\s+(?:todos|seus|sua)\b',            0.20, "avise todos (PT)"),
    _Rule(r'\balerte\b',                               0.15, "alerte (PT)"),
    _Rule(r'\bveja\s+antes\s+que\b',                   0.30, "veja antes que (PT)"),
    _Rule(r'\bantes\s+que\s+(?:deletem|apaguem|sumam|removam|tirem)\b', 0.50, "antes que deletem (PT)"),
    _Rule(r'\bvai\s+sair\s+do\s+ar\b',                0.40, "vai sair do ar (PT)"),
    _Rule(r'\bsendo\s+(?:censurado|bloqueado|apagado)\b', 0.45, "sendo censurado (PT)"),
    _Rule(r'\bproibido\s+de\s+circular\b',             0.50, "proibido circular (PT)"),

    # ── Chamadas à ação urgente (EN) ──────────────────────────────────────────
    _Rule(r'\burgent(?:ly)?\b',                        0.35, "urgent (EN)"),
    _Rule(r'\bshare\s+(?:now|immediately|asap|this)\b', 0.25, "share now (EN)"),
    _Rule(r'\bbefore\s+(?:they|it\s+gets?)\s+(?:deleted?|removed?|censored|banned?)\b', 0.50, "before they delete (EN)"),
    _Rule(r'\bbreaking\s*(?:news)?\b',                 0.20, "breaking news (EN)"),
    _Rule(r'\bspread\s+the\s+(?:word|news|truth)\b',   0.25, "spread the word (EN)"),
    _Rule(r'\bgoing\s+viral\b',                        0.15, "going viral (EN)"),
    _Rule(r'\bdo\s+not\s+ignore\b',                    0.30, "do not ignore (EN)"),

    # ── Chamadas à ação urgente (ES) ──────────────────────────────────────────
    _Rule(r'\burgente\b',                              0.35, "urgente (ES)"),
    _Rule(r'\bcomparte(?:n)?\b',                       0.20, "comparte (ES)"),
    _Rule(r'\antes\s+que\s+(?:lo\s+)?borren\b',        0.50, "antes que borren (ES)"),
    _Rule(r'\breenví[ae]\b',                           0.18, "reenvía (ES)"),

    # ── Chamadas à ação urgente (FR) ──────────────────────────────────────────
    _Rule(r'\bpartagez\b',                             0.20, "partagez (FR)"),
    _Rule(r'\bavant\s+(?:qu[\'e]ils?\s+)?(?:supprime|efface|censure)\b', 0.50, "avant qu'ils suppriment (FR)"),
    _Rule(r'\bfaites\s+passer\b',                      0.25, "faites passer (FR)"),

    # ── Padrões tipográficos (language-agnostic) ─────────────────────────────
    _Rule(r'!!+',                                      0.12, "exclamações múltiplas"),
    _Rule(r'\?{2,}',                                   0.08, "interrogações múltiplas"),
    _Rule(r'(?:!!+\??|\?+!+){1,}',                     0.10, "mistura !?"),
    _Rule(r'[A-ZÁÉÍÓÚÀÂÊÔÃÕÜÇ]{4,}',                  0.08, "palavras em CAIXA ALTA"),  # capturado per-match
]


# ─────────────────────────────────────────────────────────────────────────────
# CLAIM: densidade de afirmações verificáveis
# ─────────────────────────────────────────────────────────────────────────────
_CLAIM_RULES: list[_Rule] = [
    # ── Estatísticas e números ────────────────────────────────────────────────
    _Rule(r'\d+\s*(?:%(?=\W|$)|(?:por\s*cento|percent(?:age)?|pourcent)\b)', 0.20, "percentagem"),
    _Rule(r'\d+\s*(?:mil(?:hões?|hares?)?|bilhões?|millions?|billions?|thousands?|milliers?)\b', 0.18, "grande número"),
    _Rule(r'\d+\s*(?:mortes?|deaths?|casos?|cases?|infectad[oa]s?|infected)\b', 0.25, "estatística de saúde"),
    _Rule(r'\bem\s+\d+\s+(?:de\s+cada|out\s+of|sur)\s+\d+\b',   0.25, "razão X em Y"),
    _Rule(r'\b(?:um|uma|dois|duas|três|um\s+terço|metade|a\s+half|one\s+third)\s+d[aoe]s?\b', 0.12, "fração"),

    # ── Afirmações de autoridade ──────────────────────────────────────────────
    _Rule(r'\b(?:estudo|pesquisa|relatório|levantamento|survey|study|report|étude|rapport)\b', 0.20, "autoridade: estudo"),
    _Rule(r'\b(?:universidade|hospital|instituto|faculdade|university|hospital|institute)\b', 0.18, "autoridade: instituição"),
    _Rule(r'\b(?:oms|who|cdc|anvisa|fiocruz|ibge|inpe|ipcc|onu|un|fbi|cia|nasa)\b', 0.25, "autoridade: organismo"),
    _Rule(r'\b(?:segundo|conforme|de\s+acordo\s+com|according\s+to|selon|según)\b',  0.12, "citação de fonte"),
    _Rule(r'\b(?:especialistas?|cientistas?|médicos?|experts?|scientists?|doctors?|experts?|scientifiques?)\b', 0.15, "autoridade: especialistas"),

    # ── Afirmações absolutas ──────────────────────────────────────────────────
    _Rule(r'\b(?:sempre|nunca|jamais|todos|ninguém|nenhum|todos\s+os|always|never|everyone|nobody|toujours|jamais|tout\s+le\s+monde)\b', 0.18, "afirmação absoluta"),
    _Rule(r'\b(?:comprovado|confirmado|provado|proven|confirmed|prouvé|confirmado|demostrado)\b', 0.22, "verdade afirmada"),
    _Rule(r'\b(?:causa|provoca|leva\s+a|resulta\s+em|causes?|leads?\s+to|provoque|ocasiona)\b', 0.15, "relação causal"),

    # ── Datas e eventos específicos ───────────────────────────────────────────
    _Rule(r'\b(?:em\s+)?\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b', 0.15, "data específica (PT)"),
    _Rule(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b', 0.15, "data específica (EN)"),
    _Rule(r'\b\d{4}\b',                                0.08, "ano mencionado"),

    # ── Nomes próprios (proxy via maiúscula inicial após espaço) ──────────────
    _Rule(r'(?<=\s)[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)+', 0.10, "possível nome próprio"),
]


# ─────────────────────────────────────────────────────────────────────────────
# MANIPULATION: apelos emocionais para contornar pensamento crítico
# ─────────────────────────────────────────────────────────────────────────────
_MANIPULATION_RULES: list[_Rule] = [
    # ── Medo ─────────────────────────────────────────────────────────────────
    _Rule(r'\b(?:risco\s+de\s+vida|risco\s+de\s+morte|vai\s+(?:te\s+)?matar|perigo\s+(?:de\s+)?morte)\b', 0.45, "medo: risco de morte (PT)"),
    _Rule(r'\b(?:epidemia|pandemia|contágio|contaminação|vírus\s+(?:mortal|perigoso)|epidemic|pandemic|contagion)\b', 0.25, "medo: epidemia"),
    _Rule(r'\b(?:acabe\s+com|destruirão|aniquilação|colapso|fim\s+do|end\s+of|collapse\s+of)\b', 0.30, "medo: colapso"),
    _Rule(r'\b(?:seus\s+filhos?|suas\s+crianças?|your\s+children?|vos\s+enfants?)\b',            0.25, "medo: ameaça às crianças"),
    _Rule(r'\b(?:cuidado|beware|attention|méfiez-vous)\b',                                        0.15, "aviso de perigo"),

    # ── Raiva e indignação ────────────────────────────────────────────────────
    _Rule(r'\b(?:revoltante|indignante|absurdo|vergonhoso|criminoso|inadmissível|outraging?|shocking|scandaleux)\b', 0.30, "raiva: indignação"),
    _Rule(r'\b(?:eles\s+(?:estão|vão|querem)|they\s+(?:are|want|will)|ils\s+(?:veulent|vont))\b', 0.20, "raiva: 'eles' ameaçadores"),
    _Rule(r'\b(?:governo\s+(?:esconde|censura|proíbe|mente)|media\s+(?:hides?|lies?|censors?)|mídia\s+não\s+mostra)\b', 0.40, "raiva: conspiração governo/mídia"),
    _Rule(r'\b(?:não\s+(?:podem|devem)\s+(?:saber|ver)|they\s+don\'?t\s+want\s+you\s+to\s+know|ils\s+ne\s+veulent\s+pas\s+que)\b', 0.45, "raiva: informação suprimida"),

    # ── Conspiração ───────────────────────────────────────────────────────────
    _Rule(r'\b(?:nova\s+ordem\s+mundial|new\s+world\s+order|nouvel\s+ordre\s+mondial|nuevo\s+orden\s+mundial)\b', 0.50, "conspiração: NOM"),
    _Rule(r'\b(?:illuminati|deep\s+state|estado\s+profundo|globalistas?|globalists?|élites?)\b',  0.45, "conspiração: elite global"),
    _Rule(r'\b(?:chip|microchip|implante|nanobots?|5g\s+(?:causa|mata|controla))\b',              0.50, "conspiração: tecnologia oculta"),
    _Rule(r'\b(?:terraplan(?:ismo|ista)|terra\s+plana|flat\s+earth|terre\s+plate)\b',             0.40, "conspiração: terra plana"),
    _Rule(r'\b(?:eles?\s+(?:nos?)\s+(?:controlam|vigiam|espionam)|they\s+(?:control|watch|spy)\s+(?:us|you))\b', 0.40, "conspiração: controle"),

    # ── Orgulho manipulador / apelo à identidade ──────────────────────────────
    _Rule(r'\b(?:defenda\s+(?:o\s+brasil|sua\s+família|nosso\s+país)|defend\s+(?:our\s+country|america|the\s+truth))\b', 0.25, "orgulho: chamada patriótica"),
    _Rule(r'\b(?:verdadeiros?\s+brasileiros?|true\s+patriots?|vrais?\s+français?)\b',             0.30, "orgulho: identidade exclusiva"),
    _Rule(r'\b(?:traidores?|traitors?|traîtres?)\b',                                              0.25, "desumanização: traidor"),

    # ── Clickbait emocional ───────────────────────────────────────────────────
    _Rule(r'\b(?:você\s+não\s+(?:vai|irá)\s+acreditar|you\s+won\'?t\s+believe|vous\s+n\'allez\s+pas\s+croire)\b', 0.30, "clickbait: surpresa"),
    _Rule(r'\b(?:chocante|inacreditável|jaw-?dropping|unbelievable|incroyable|increíble)\b',      0.25, "clickbait: sensação"),
    _Rule(r'\b(?:nunca\s+antes\s+(?:visto|revelado|mostrado)|never\s+before\s+(?:seen|revealed))\b', 0.30, "clickbait: exclusividade"),
    _Rule(r'\b(?:segredo\s+(?:revelado|exposto|oculto)|secret\s+(?:revealed?|exposed?|hidden)|secret\s+révélé)\b', 0.35, "clickbait: segredo revelado"),
]


# ── Detecção de idioma ─────────────────────────────────────────────────────────

_LANG_MARKERS: dict[str, set] = {
    "pt": {"de", "do", "da", "que", "não", "com", "para", "uma", "por", "são", "mais",
           "mas", "foi", "tem", "seu", "sua", "isso", "esse", "este", "como", "muito",
           "também", "quando", "onde", "quem", "pelo", "pela", "nos", "nas"},
    "en": {"the", "and", "for", "that", "this", "with", "are", "from", "have", "not",
           "but", "was", "you", "they", "will", "been", "would", "could", "their",
           "has", "had", "what", "when", "where", "which", "who"},
    "es": {"que", "con", "para", "una", "los", "del", "por", "como", "más", "pero",
           "las", "sus", "son", "una", "está", "tiene", "todo", "también", "cuando",
           "muy", "puede", "hacer", "nos", "este", "hay"},
    "fr": {"les", "des", "une", "dans", "est", "pas", "sur", "qui", "par", "aussi",
           "plus", "mais", "tout", "comme", "ont", "leur", "cette", "vous", "nous",
           "avec", "fait", "être", "sont", "bien"},
}


def _detect_language(text: str) -> str:
    """Detecção de idioma por frequência de marcadores léxicos."""
    words = set(re.findall(r'\b[a-záéíóúàâêôãõüçñ]+\b', text.lower()))
    scores = {
        lang: len(words & markers)
        for lang, markers in _LANG_MARKERS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


# ── Motor de pontuação ────────────────────────────────────────────────────────

def _apply_rules(text: str, rules: list[_Rule]) -> tuple[float, list[str]]:
    """Aplica lista de regras ao texto e retorna (score capped, evidências)."""
    text_lower = text.lower()
    total = 0.0
    evidence: list[str] = []

    for rule in rules:
        try:
            matches = re.findall(rule.pattern, text_lower, re.IGNORECASE | re.UNICODE)
        except re.error:
            continue
        if matches:
            # Cada ocorrência contribui; limitamos a 3 para evitar dominância
            count = min(len(matches), 3)
            total += rule.weight * count
            evidence.append(f"{rule.label}" + (f" ×{len(matches)}" if len(matches) > 1 else ""))

    return min(round(total, 3), 1.0), evidence


def _caps_ratio(text: str) -> float:
    """Proporção de palavras totalmente em maiúsculas (≥4 chars) sobre total de palavras."""
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return 0.0
    caps_words = [w for w in words if len(w) >= 4 and w.isupper()]
    return round(len(caps_words) / len(words), 3)


# ── Função principal ──────────────────────────────────────────────────────────

def analyze_text(text: str) -> NLPResult:
    """Analisa o texto e retorna três sinais linguísticos com evidências.

    Função síncrona — sem IO, sem side effects. Completa em < 2ms para textos
    de até 1000 caracteres.

    Args:
        text: Texto a analisar (conteúdo enviado pelo usuário).

    Returns:
        NLPResult com scores 0.0–1.0 para urgência, afirmações e manipulação.
    """
    if not text or text.strip().startswith("["):
        return NLPResult(text=text, error="texto vazio ou mídia sem legenda")

    word_count = len(re.findall(r'\b\w+\b', text))
    caps = _caps_ratio(text)
    lang = _detect_language(text)

    u_score, u_evidence = _apply_rules(text, _URGENCY_RULES)
    c_score, c_evidence = _apply_rules(text, _CLAIM_RULES)
    m_score, m_evidence = _apply_rules(text, _MANIPULATION_RULES)

    # CAPS ratio reforça urgência: > 20% de palavras em maiúsculas → +0.15
    if caps > 0.20:
        u_score = min(u_score + 0.15, 1.0)
        u_evidence.append(f"CAPS excessivo ({caps:.0%} das palavras)")
    if caps > 0.40:
        m_score = min(m_score + 0.10, 1.0)
        m_evidence.append(f"CAPS muito alto ({caps:.0%})")

    return NLPResult(
        text=text[:500],  # armazenar somente o início para evitar Redis bloat
        language=lang,
        urgency=NLPSignal(score=u_score, evidence=u_evidence, label="urgência"),
        claim=NLPSignal(score=c_score, evidence=c_evidence, label="afirmações verificáveis"),
        manipulation=NLPSignal(score=m_score, evidence=m_evidence, label="manipulação emocional"),
        word_count=word_count,
        caps_ratio=caps,
    )


# ── Serialização ──────────────────────────────────────────────────────────────

def serialize_nlp_result(r: NLPResult) -> dict:
    """Converte NLPResult em dict JSON-serializável."""
    return {
        "language": r.language,
        "word_count": r.word_count,
        "caps_ratio": r.caps_ratio,
        "error": r.error,
        "urgency": {
            "score": r.urgency.score,
            "evidence": r.urgency.evidence,
        },
        "claim": {
            "score": r.claim.score,
            "evidence": r.claim.evidence,
        },
        "manipulation": {
            "score": r.manipulation.score,
            "evidence": r.manipulation.evidence,
        },
    }
