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

    # ── Urgência política (PT/EN) ─────────────────────────────────────────────
    _Rule(r'\b(?:vai\s+(?:acabar|fechar|destruir)\s+(?:o|a|os|as))\b',  0.20, "urgência: vai destruir (PT)"),
    _Rule(r'\b(?:aprovaram?\s+(?:de\s+madrugada|escondido|às\s+escuras))\b', 0.40, "urgência: aprovado escondido (PT)"),
    _Rule(r'\b(?:passed\s+(?:secretly|quietly|in\s+secret|overnight))\b', 0.40, "urgência: passed secretly (EN)"),

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
    _Rule(r'\b[A-ZÁÉÍÓÚÀÂÊÔÃÕÜÇ]{4,}\b',              0.10, "palavras em CAIXA ALTA"),  # capturado per-match; weight↑ 0.08→0.10
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

    # ── Escondendo / ocultando — verbo progressivo (PT/EN) ───────────────
    _Rule(r'\b(?:está|estão|estava|estavam)\s+(?:escondendo|ocultando|censurando|encobrindo|mentindo)\b', 0.40, "conspiração: escondendo (PT)"),
    _Rule(r'\b(?:is|are|was|were)\s+(?:hiding|concealing|covering\s+up|censoring|suppressing|lying\s+about)\b', 0.40, "conspiração: hiding (EN)"),
    _Rule(r'\bescondendo\s+(?:isso|isto|da\s+população|do\s+povo|de\s+(?:você|nós|todos))\b', 0.45, "conspiração: escondendo da população (PT)"),
    _Rule(r'\b(?:hiding|concealing)\s+(?:this|it|the\s+truth)\s+from\b', 0.45, "conspiração: hiding from public (EN)"),

    # ── Ninguém fala / informação suprimida ──────────────────────────────
    _Rule(r'\bninguém\s+(?:fala|mostra|comenta|sabe)\b', 0.35, "conspiração: ninguém fala (PT)"),
    _Rule(r'\b(?:população|povo)\s+não\s+(?:sabe|pode\s+saber|fica\s+sabendo)\b', 0.35, "conspiração: população não sabe (PT)"),
    _Rule(r'\b(?:no\s+one\s+(?:talks?|knows?|speaks?)\s+about|mainstream\s+media\s+(?:won\'?t|doesn\'?t|refuses?\s+to))\b', 0.35, "conspiração: suppressed info (EN)"),

    # ── Fraude e conspirações políticas ───────────────────────────────────
    _Rule(r'\b(?:fraude\s+(?:nas?\s+)?(?:urnas?|eleição|eleições|eleitoral)|election\s+fraud|rigged\s+(?:election|vote|system))\b', 0.50, "conspiração: fraude eleitoral"),
    _Rule(r'\b(?:decreto\s+secreto|lei\s+secreta|reunião\s+secreta|plano\s+secreto|secret\s+(?:decree|order|plan|law))\b', 0.45, "conspiração: plano secreto"),
    _Rule(r'\b(?:golpe\s+(?:de\s+estado|militar|comunista|(?:da|do)\s+(?:esquerda|direita))|coup\s+d\'?état|military\s+coup)\b', 0.45, "conspiração: golpe"),
    _Rule(r'\b(?:ditadura|dictatorship|tyrann[yie]|tiran[oi]a|authoritarian\s+regime)\b', 0.35, "conspiração: ditadura/tirania"),
    _Rule(r'\b(?:confiscar|confiscação|apreender\s+(?:bens|armas|propriedade)|seize|confiscate|confiscation)\b', 0.30, "ameaça: confisco"),
    _Rule(r'\b(?:compra\s+de\s+votos?|votos?\s+comprados?|buying\s+votes?|vote\s+buying)\b', 0.45, "conspiração: compra de votos"),

    # ── Hoax / embuste / farsa ───────────────────────────────────────────
    _Rule(r'\b(?:hoax|farsa|embuste|scam|armação|montagem)\b', 0.35, "manipulação: hoax/farsa"),
    _Rule(r'\b(?:invent(?:ed|ou|aram|ado)|fabricat(?:ed|ou))\s+(?:by|p(?:or|ela|elo)|para)\b', 0.30, "manipulação: inventado/fabricado"),
    _Rule(r'\b(?:para|to|por)\s+(?:destruir|destroy|acabar\s+com|undermine|sabotar|sabotage|dominar|dominate)\b', 0.25, "manipulação: para destruir/dominar"),
    _Rule(r'\b(?:é\s+tudo\s+mentira|it\'?s\s+all\s+(?:a\s+)?li[ea]s?|tudo\s+(?:uma\s+)?farsa)\b', 0.40, "manipulação: é tudo mentira"),

    # ── Acorde / abra os olhos ───────────────────────────────────────────
    _Rule(r'\b(?:acorde[mn]?|abr[ae]\s+os\s+olhos|wake\s+up|open\s+your\s+eyes|red\s+pill)\b', 0.30, "manipulação: acorde/abra os olhos"),
    _Rule(r'\b(?:lavagem\s+cerebral|brain\s*wash(?:ing|ed)?)\b', 0.35, "manipulação: lavagem cerebral"),

    # ── Cura milagrosa / negação científica ──────────────────────────────
    _Rule(r'\b(?:cura\s+(?:milagrosa|definitiva|secreta|natural|caseira)|miracle\s+cure|secret\s+(?:cure|remedy))\b', 0.40, "manipulação: cura milagrosa"),
    _Rule(r'\b(?:médicos?\s+não\s+(?:querem|vão)\s+(?:te\s+)?(?:contar|dizer|revelar)|doctors?\s+(?:don\'?t|won\'?t)\s+(?:tell|want\s+you\s+to\s+know))\b', 0.45, "conspiração: médicos não contam"),
    _Rule(r'\b(?:a\s+indústria\s+(?:farmacêutica|alimentar|da\s+saúde)|big\s+pharma|big\s+(?:food|tech|oil))\b', 0.30, "conspiração: indústria/big pharma"),
    _Rule(r'\b(?:para\s+(?:vender|lucrar|ganhar\s+dinheiro)|to\s+(?:sell|profit|make\s+money))\b', 0.25, "conspiração: motivo de lucro"),

    # ── Obrigar / forçar a população ─────────────────────────────────────
    _Rule(r'\b(?:obrigar\s+(?:todos|a\s+população)|forçar\s+(?:todos|as\s+pessoas|o\s+povo))\b', 0.30, "ameaça: obrigar todos (PT)"),
    _Rule(r'\b(?:force\s+everyone|mandatory\s+for\s+(?:all|everyone)|compulsory|obrigatório\s+para\s+todos)\b', 0.30, "ameaça: mandatory for all (EN)"),

    # ── Não querem que você saiba (broader) ──────────────────────────────
    _Rule(r'\b(?:não\s+querem\s+que\s+(?:você|vocês|nós|o\s+povo)\s+(?:saiba|veja|descubra))\b', 0.40, "conspiração: não querem que saiba (PT)"),
    _Rule(r'\b(?:you\'?re\s+not\s+(?:supposed|allowed)\s+to\s+(?:know|see|hear))\b', 0.40, "conspiração: not supposed to know (EN)"),

    # ── Agenda oculta / hidden agenda ────────────────────────────────────
    _Rule(r'\b(?:agenda\s+(?:oculta|secreta|globalista)|hidden\s+agenda|great\s+reset)\b', 0.40, "conspiração: agenda oculta"),

    # ══════════════════════════════════════════════════════════════════════
    # NOVOS PADRÕES — baseados em datasets acadêmicos (LIAR, FakeNewsNet,
    # CHECKED, NELA-GT, PHEME, FakevsSatire, Garg & Sharma 2022,
    # Choudhary & Arora 2021, Horne & Adali 2017)
    # ══════════════════════════════════════════════════════════════════════

    # ── Anti-vacina (PT) — baseado em CHECKED, CoAID, COVID Misinfo ────
    _Rule(r'\bnão\s+vacin[ea]\b',                                          0.50, "anti-vax: não vacine (PT)"),
    _Rule(r'\bvacina\s+(?:mata|matou|matando|mata(?:r[aá])?)\b',           0.50, "anti-vax: vacina mata (PT)"),
    _Rule(r'\bvacina\s+(?:é|são)\s+(?:veneno|tóxica|perigosa|experimental)\b', 0.50, "anti-vax: vacina é veneno (PT)"),
    _Rule(r'\befeitos?\s+colaterais?\s+(?:escondidos?|ocultos?|graves?|mortais?)\b', 0.45, "anti-vax: efeitos colaterais escondidos (PT)"),
    _Rule(r'\b(?:ingredientes?\s+tóxicos?|substâncias?\s+tóxicas?)\b',     0.40, "anti-vax: ingredientes tóxicos (PT)"),
    _Rule(r'\bautismo\b.*\bvacina\b|\bvacina\b.*\bautismo\b',             0.50, "anti-vax: vacina-autismo (PT)"),
    _Rule(r'\b(?:contém|contem)\s+(?:mercúrio|alumínio|formaldeído|grafeno)\b', 0.40, "anti-vax: substância perigosa (PT)"),
    _Rule(r'\bcobaias?\b',                                                 0.35, "anti-vax: cobaias (PT)"),
    _Rule(r'\b(?:vacina|vacinação)\s+(?:apressada|experimental|não\s+testada)\b', 0.40, "anti-vax: vacina não testada (PT)"),
    _Rule(r'\bmortes?\s+(?:após|depois\s+d[ae]|pós)\s+vacina(?:ção)?\b',   0.45, "anti-vax: mortes pós-vacina (PT)"),
    _Rule(r'\b(?:recus[ea]|rejeitar?)\s+(?:a\s+)?vacina(?:ção)?\b',        0.30, "anti-vax: recusar vacina (PT)"),
    _Rule(r'\b(?:imunidade\s+natural|imunizar\s+naturalmente)\b',          0.25, "anti-vax: imunidade natural (PT)"),

    # ── Anti-vacina (EN) ───────────────────────────────────────────────
    _Rule(r'\bdon\'?t\s+vaccinate\b',                                      0.50, "anti-vax: don't vaccinate (EN)"),
    _Rule(r'\bvaccine\s+(?:kills?|is\s+killing|deadly|lethal)\b',          0.50, "anti-vax: vaccine kills (EN)"),
    _Rule(r'\bvaccine\s+(?:is|are)\s+(?:poison|toxic|dangerous|experimental)\b', 0.50, "anti-vax: vaccine is poison (EN)"),
    _Rule(r'\bhidden\s+side\s+effects?\b',                                0.45, "anti-vax: hidden side effects (EN)"),
    _Rule(r'\btoxic\s+ingredients?\b',                                     0.40, "anti-vax: toxic ingredients (EN)"),
    _Rule(r'\bautism\b.*\bvaccine\b|\bvaccine\b.*\bautism\b',             0.50, "anti-vax: vaccine-autism (EN)"),
    _Rule(r'\b(?:contains?|laced\s+with)\s+(?:mercury|aluminum|formaldehyde|graphene)\b', 0.40, "anti-vax: dangerous substance (EN)"),
    _Rule(r'\bguinea\s+pigs?\b',                                           0.35, "anti-vax: guinea pigs (EN)"),
    _Rule(r'\brushed\s+vaccine\b',                                         0.40, "anti-vax: rushed vaccine (EN)"),
    _Rule(r'\bdeaths?\s+(?:after|following|from)\s+vaccin(?:e|ation)\b',   0.45, "anti-vax: deaths after vaccination (EN)"),
    _Rule(r'\bnatural\s+immunity\b',                                       0.25, "anti-vax: natural immunity (EN)"),

    # ── Negação Científica (PT) — baseado em FakevsSatire, NELA-GT ─────
    _Rule(r'\b(?:NASA|OMS|WHO)\s+(?:admitiu|confessou|revelou|confirmou)\b', 0.45, "negação científica: autoridade admitiu (PT)"),
    _Rule(r'\baquecimento\s+global\s+(?:é|não\s+(?:existe|é\s+real)).*(?:farsa|mentira|fraude|hoax)\b', 0.50, "negação científica: aquecimento global farsa (PT)"),
    _Rule(r'\bmudança\s+climática\s+(?:é\s+)?(?:natural|não\s+existe|mentira)\b', 0.40, "negação científica: mudança climática (PT)"),
    _Rule(r'\b(?:ciência|ciencia)\s+(?:é\s+)?(?:mentira|fraude|manipulada|comprada)\b', 0.45, "negação científica: ciência é mentira (PT)"),
    _Rule(r'\bcientistas?\s+(?:mentem|mentiram|estão\s+mentindo|escondem|são\s+pagos)\b', 0.45, "negação científica: cientistas mentem (PT)"),
    _Rule(r'\bnunca\s+(?:foi|foram)\s+(?:provado|comprovado|demonstrado)\b', 0.35, "negação científica: nunca provado (PT)"),
    _Rule(r'\bdados?\s+(?:foram|são|estão)\s+(?:manipulados?|falsificados?|inventados?)\b', 0.40, "negação científica: dados manipulados (PT)"),
    _Rule(r'\bconsenso\s+científico\s+(?:é\s+)?(?:falso|mentira|comprado|manipulado)\b', 0.45, "negação científica: consenso falso (PT)"),
    _Rule(r'\b(?:teoria\s+d[ae]\s+evolução|evolucionismo)\s+(?:é\s+)?(?:mentira|fraude|falso)\b', 0.40, "negação científica: evolução falsa (PT)"),

    # ── Negação Científica (EN) ──────────────────────────────────────────
    _Rule(r'\b(?:NASA|WHO|CDC)\s+(?:admitted|confessed|revealed|confirmed)\b', 0.45, "negação científica: authority admitted (EN)"),
    _Rule(r'\bglobal\s+warming\s+(?:is\s+(?:a\s+)?)?(?:hoax|lie|fraud|fake|scam)\b', 0.50, "negação científica: global warming hoax (EN)"),
    _Rule(r'\bclimate\s+change\s+(?:is\s+)?(?:natural|not\s+real|a\s+lie|fake|hoax)\b', 0.40, "negação científica: climate change denial (EN)"),
    _Rule(r'\bscience\s+(?:is\s+)?(?:a\s+lie|fraud|bought|corrupted|manipulated)\b', 0.45, "negação científica: science is a lie (EN)"),
    _Rule(r'\bscientists?\s+(?:lie|are\s+lying|are\s+paid|are\s+corrupt|hide)\b', 0.45, "negação científica: scientists lie (EN)"),
    _Rule(r'\bnever\s+(?:been\s+)?(?:proven|demonstrated|shown)\b',        0.35, "negação científica: never proven (EN)"),
    _Rule(r'\bdata\s+(?:was|were|is|has\s+been)\s+(?:manipulated|fabricated|falsified|faked)\b', 0.40, "negação científica: data manipulated (EN)"),
    _Rule(r'\bscientific\s+consensus\s+(?:is\s+)?(?:wrong|false|bought|a\s+lie)\b', 0.45, "negação científica: consensus wrong (EN)"),
    _Rule(r'\bevolution\s+is\s+(?:just\s+)?(?:a\s+)?(?:theory|lie|false)\b', 0.40, "negação científica: evolution is a theory (EN)"),

    # ── Desinformação de Saúde (PT) — baseado em CoAID, CHECKED ────────
    _Rule(r'\b(?:ivermectina|cloroquina|hidroxicloroquina)\s+(?:cura|trata|previne|funciona)\b', 0.45, "saúde: medicamento milagroso (PT)"),
    _Rule(r'\btratamento\s+precoce\b',                                     0.25, "saúde: tratamento precoce (PT)"),
    _Rule(r'\b(?:remédio|remedio)\s+caseiro\b',                            0.30, "saúde: remédio caseiro (PT)"),
    _Rule(r'\b(?:chá|suco|óleo)\s+(?:de\s+)?(?:\w+)\s+(?:cura|trata|combate|previne)\b', 0.40, "saúde: chá/suco cura (PT)"),
    _Rule(r'\bmédicos?\s+(?:proibidos?|impedidos?|censurados?)\s+de\s+(?:falar|revelar|contar)\b', 0.45, "saúde: médicos proibidos de falar (PT)"),
    _Rule(r'\bprotocolo\s+(?:proibido|censurado|secreto)\b',              0.40, "saúde: protocolo proibido (PT)"),
    _Rule(r'\bcura\s+d[oe]\s+câncer\s+(?:escondida|oculta|censurada?)\b', 0.50, "saúde: cura do câncer escondida (PT)"),
    _Rule(r'\bágua\s+com\s+(?:limão|bicarbonato|vinagre)\s+(?:cura|trata|combate)\b', 0.45, "saúde: água com X cura (PT)"),
    _Rule(r'\b(?:quimioterapia|quimio)\s+(?:é\s+)?(?:veneno|mata|perigosa)\b', 0.45, "saúde: quimioterapia é veneno (PT)"),
    _Rule(r'\bnão\s+existe\s+(?:vírus|virus|pandemia|covid|doença)\b',    0.50, "saúde: negacionismo de doença (PT)"),
    _Rule(r'\bgripe\s+(?:comum|normal|simples)\b.*\bcovid\b|\bcovid\b.*\bgripe\s+(?:comum|normal|simples)\b', 0.40, "saúde: covid é gripe (PT)"),
    _Rule(r'\bdesintoxica[rç]?\b',                                         0.20, "saúde: desintoxicar (PT)"),

    # ── Desinformação de Saúde (EN) ──────────────────────────────────────
    _Rule(r'\b(?:ivermectin|chloroquine|hydroxychloroquine)\s+(?:cures?|treats?|prevents?|works?)\b', 0.45, "saúde: miracle drug (EN)"),
    _Rule(r'\bhome\s+remed(?:y|ies)\b',                                    0.30, "saúde: home remedy (EN)"),
    _Rule(r'\b(?:tea|juice|oil)\s+(?:that\s+)?(?:cures?|treats?|fights?|prevents?)\b', 0.40, "saúde: tea/juice cures (EN)"),
    _Rule(r'\bdoctors?\s+(?:banned|silenced|censored)\s+from\s+(?:speaking|telling)\b', 0.45, "saúde: doctors banned (EN)"),
    _Rule(r'\b(?:banned|forbidden|censored)\s+(?:treatment|protocol|cure)\b', 0.40, "saúde: banned treatment (EN)"),
    _Rule(r'\bcancer\s+cure\s+(?:hidden|suppressed|covered\s+up)\b',      0.50, "saúde: cancer cure hidden (EN)"),
    _Rule(r'\b(?:lemon\s+water|baking\s+soda|apple\s+cider)\s+(?:cures?|treats?)\b', 0.45, "saúde: lemon water cures (EN)"),
    _Rule(r'\b(?:chemotherapy|chemo)\s+(?:is\s+)?(?:poison|kills?|dangerous)\b', 0.45, "saúde: chemo is poison (EN)"),
    _Rule(r'\b(?:virus|pandemic|covid)\s+(?:doesn\'?t|does\s+not|don\'?t)\s+exist\b', 0.50, "saúde: disease denial (EN)"),
    _Rule(r'\bcovid\s+(?:is\s+)?(?:just\s+)?(?:a\s+)?(?:flu|cold|hoax)\b', 0.40, "saúde: covid is flu (EN)"),
    _Rule(r'\bdetox\b',                                                    0.20, "saúde: detox (EN)"),

    # ── Apelo Emocional Infantil (PT + EN) — baseado em FakevsSatire ─
    _Rule(r'\bproteja\s+(?:seus?\s+)?(?:filhos?|crianças?|bebês?)\b',     0.30, "emocional: proteja seus filhos (PT)"),
    _Rule(r'\bprotect\s+(?:your\s+)?(?:children|kids?|babies?)\b',        0.30, "emocional: protect your children (EN)"),
    _Rule(r'\bcrianças?\s+(?:estão|vão)\s+(?:morrendo|morrer|sofrendo)\b', 0.40, "emocional: crianças morrendo (PT)"),
    _Rule(r'\bchildren\s+are\s+(?:dying|suffering|being\s+killed)\b',     0.40, "emocional: children are dying (EN)"),
    _Rule(r'\b(?:envenenando|intoxicando)\s+(?:as\s+)?(?:crianças|nossos?\s+filhos?)\b', 0.45, "emocional: envenenando crianças (PT)"),
    _Rule(r'\bpoisoning\s+(?:the\s+|our\s+)?(?:children|kids)\b',        0.45, "emocional: poisoning children (EN)"),
    _Rule(r'\bpense\s+n[oa]s?\s+(?:seus?\s+)?(?:filhos?|crianças?)\b',   0.30, "emocional: pense nos filhos (PT)"),
    _Rule(r'\bthink\s+(?:of|about)\s+(?:your\s+)?(?:children|kids)\b',   0.30, "emocional: think of your children (EN)"),

    # ── Atribuição Vaga de Fontes (PT) — baseado em LIAR, Emergent ────
    _Rule(r'\b(?:dizem\s+(?:que|por\s+aí)|andam\s+dizendo)\b',           0.25, "fonte vaga: dizem que (PT)"),
    _Rule(r'\b(?:li\s+na\s+internet|vi\s+no\s+(?:Facebook|WhatsApp|Instagram|Telegram|YouTube))\b', 0.30, "fonte vaga: li na internet (PT)"),
    _Rule(r'\bum\s+(?:amigo|conhecido)\s+(?:médico|enfermeiro|cientista)\s+(?:disse|falou|contou)\b', 0.30, "fonte vaga: amigo médico disse (PT)"),
    _Rule(r'\bfonte\s+(?:confiável|segura|de\s+confiança)\s+(?:disse|revelou|informou)\b', 0.25, "fonte vaga: fonte confiável disse (PT)"),
    _Rule(r'\btodo\s+mundo\s+sabe\b',                                     0.25, "fonte vaga: todo mundo sabe (PT)"),
    _Rule(r'\bé\s+de\s+conhecimento\s+público\b',                        0.20, "fonte vaga: conhecimento público (PT)"),
    _Rule(r'\b(?:pesquisem?|busquem?|procurem?)\s+(?:vocês?\s+mesmos?|por\s+conta\s+própria)\b', 0.35, "fonte vaga: pesquisem vocês mesmos (PT)"),
    _Rule(r'\binformação\s+(?:censurada|proibida|banida|bloqueada)\b',    0.30, "fonte vaga: informação censurada (PT)"),

    # ── Atribuição Vaga de Fontes (EN) ──────────────────────────────────
    _Rule(r'\b(?:they\s+say|people\s+say|some\s+say|many\s+say)\b',      0.25, "fonte vaga: they say (EN)"),
    _Rule(r'\b(?:I\s+(?:saw|read|found)\s+(?:on|in)\s+(?:Facebook|WhatsApp|Instagram|Telegram|YouTube))\b', 0.30, "fonte vaga: I saw on social media (EN)"),
    _Rule(r'\ba\s+(?:doctor|nurse|scientist)\s+(?:friend|I\s+know)\s+(?:said|told)\b', 0.30, "fonte vaga: a doctor friend said (EN)"),
    _Rule(r'\ba\s+reliable\s+source\s+(?:said|told|confirmed)\b',        0.25, "fonte vaga: reliable source said (EN)"),
    _Rule(r'\beverybody\s+knows\b',                                       0.25, "fonte vaga: everybody knows (EN)"),
    _Rule(r'\b(?:do\s+your\s+own\s+research|DYOR)\b',                    0.35, "fonte vaga: do your own research (EN)"),
    _Rule(r'\b(?:censored|banned|suppressed)\s+information\b',            0.30, "fonte vaga: censored information (EN)"),

    # ── Manipulação Financeira / Golpe (PT + EN) — baseado em PHEME ──
    _Rule(r'\b(?:ganhe|ganhar)\s+dinheiro\s+(?:fácil|rápido|sem\s+trabalhar)\b', 0.40, "golpe: dinheiro fácil (PT)"),
    _Rule(r'\brenda\s+extra\s+(?:garantida|fácil|sem\s+risco)\b',        0.35, "golpe: renda extra garantida (PT)"),
    _Rule(r'\bmake\s+(?:easy|quick|fast)\s+money\b',                     0.40, "golpe: easy money (EN)"),
    _Rule(r'\bguaranteed\s+(?:income|return|profit)\b',                   0.35, "golpe: guaranteed income (EN)"),
    _Rule(r'\b(?:esquema|pirâmide|piramide)\b',                           0.40, "golpe: esquema/pirâmide (PT)"),
    _Rule(r'\b(?:pyramid|ponzi)\s+scheme\b',                              0.40, "golpe: pyramid scheme (EN)"),
    _Rule(r'\bclique\s+(?:no|neste|nesse)\s+link\b',                     0.25, "golpe: clique no link (PT)"),
    _Rule(r'\bclick\s+(?:this|the)\s+link\b',                            0.25, "golpe: click the link (EN)"),
    _Rule(r'\binvista\s+agora\s+antes\b',                                0.35, "golpe: invista agora (PT)"),
    _Rule(r'\binvest\s+now\s+before\b',                                  0.35, "golpe: invest now (EN)"),

    # ── Padrões estilísticos de fake news — baseado em Horne & Adali 2017 ─
    _Rule(r'\b(?:URGENTE|ATENÇÃO|ALERTA|CUIDADO|BOMBA|BREAKING|ALERT)\s*[!:]+', 0.35, "estilo fake: palavra-chave + pontuação"),
    _Rule(r'(?:^|\n)\s*[A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]{10,}(?:!|\?|$)',         0.30, "estilo fake: título em CAPS"),
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

# ── Hedging markers — baseado em Garg & Sharma 2022, Choudhary & Arora 2021 ──
# Textos legítimos usam hedging; fake news faz afirmações categóricas.
_HEDGING_MARKERS: set[str] = {
    # PT
    "pode", "poderia", "poderiam", "poderá", "talvez", "provavelmente",
    "possivelmente", "sugere", "indica", "aparentemente", "supostamente",
    "parece", "segundo", "alegadamente", "hipoteticamente", "eventualmente",
    # EN
    "may", "might", "could", "possibly", "probably", "perhaps",
    "suggests", "indicates", "apparently", "seemingly", "allegedly",
    "reportedly", "hypothetically", "potentially", "likely",
    # ES
    "quizás", "posiblemente", "probablemente", "aparentemente",
    # FR
    "peut-être", "possiblement", "probablement", "apparemment",
}


def _apply_rules(text: str, rules: list[_Rule]) -> tuple[float, list[str]]:
    """Aplica lista de regras ao texto e retorna (score capped, evidências)."""
    text_lower = text.lower()
    total = 0.0
    evidence: list[str] = []

    for rule in rules:
        try:
            # CAIXA ALTA rule must match against original (not lowered) text
            # so it only catches truly ALL-CAPS words
            if "CAIXA ALTA" in rule.label:
                matches = re.findall(rule.pattern, text, re.UNICODE)
            else:
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

    # CAPS ratio reforça urgência — thresholds adaptativos (Horne & Adali 2017)
    if caps > 0.10:
        u_score = min(u_score + 0.10, 1.0)
        u_evidence.append(f"CAPS elevado ({caps:.0%} das palavras)")
    if caps > 0.20:
        u_score = min(u_score + 0.05, 1.0)  # cumulative: +0.15 total at >20%
        m_score = min(m_score + 0.08, 1.0)
        m_evidence.append(f"CAPS alto ({caps:.0%})")
    if caps > 0.40:
        m_score = min(m_score + 0.10, 1.0)
        m_evidence.append(f"CAPS muito alto ({caps:.0%})")

    # ── Hedging analysis (Garg & Sharma 2022, Choudhary & Arora 2021) ────
    # Textos legítimos usam hedging; fake news faz afirmações categóricas.
    text_words = set(re.findall(r'\b[a-záéíóúàâêôãõüçñ]+\b', text.lower()))
    hedging_found = text_words & _HEDGING_MARKERS
    has_claims = c_score > 0.25
    has_manipulation = m_score > 0.15

    if has_claims and not hedging_found and has_manipulation:
        # No hedging + claims + manipulation = stronger fake signal
        m_score = min(m_score + 0.10, 1.0)
        m_evidence.append("sem hedging em texto com afirmações (sinal forte)")
    elif hedging_found and len(hedging_found) >= 2:
        # Multiple hedging markers = more nuanced text, slightly reduce manipulation
        m_score = max(m_score - 0.05, 0.0)
        if m_evidence:
            m_evidence.append(f"hedging presente ({', '.join(list(hedging_found)[:3])})")

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
