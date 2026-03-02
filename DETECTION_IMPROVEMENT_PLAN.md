# Plano de Melhoria do Motor de Detecção — Mentor Digital

## Referências Acadêmicas Consultadas

| # | Fonte | Contribuição para o plano |
|---|-------|--------------------------|
| 1 | **LIAR Dataset** (Wang 2017) — 12.8K afirmações rotuladas do PolitiFact com 6 graus de falsidade | Padrões de afirmações absolutas, hedging ausente, atribuição vaga de fontes |
| 2 | **FakeNewsNet** (Shu et al. 2018) — PolitiFact + GossipCop com contexto social | Padrões de sensacionalismo, clickbait, apelo emocional |
| 3 | **NELA-GT-2018** (Nørregaard et al. 2019) — 713K artigos de 194 fontes | Features linguísticas: complexidade, repetição, estilo; distinção entre fontes mainstream vs. conspiração |
| 4 | **CHECKED** (Yang et al. 2021) — COVID-19 fake news chinês do Weibo | Padrões de desinformação sobre saúde/COVID, estrutura de rumores |
| 5 | **COVID Misinfo Videos** (Knuutila 2021, Zenodo) — 8.122 vídeos removidos do YouTube | Vocabulário de desinformação COVID, narrativas anti-vacina |
| 6 | **Emergent** (Ferreira & Vlachos 2016) — 300 rumores + 2.595 artigos classificados | Stance classification: patterns "for/against" claim |
| 7 | **PHEME** (Zubiaga et al. 2017) — Rumores do Twitter em breaking news | Propagação de rumores, padrões de verificabilidade |
| 8 | **FakevsSatire** (Golbeck et al. 2018) — Fake news vs. sátira | Temas: conspirações, racismo, descrédito de fontes confiáveis |
| 9 | **Horne & Adali (2017)** — "Fake news packs a lot in title, uses simpler content" | Fake news usa linguagem mais simples e repetitiva; títulos sensacionalistas |
| 10 | **Garg & Sharma (2022)** — Linguistic features framework for fake news detection | N-grams, POS tags, sentiment scores, features estilísticas |
| 11 | **Choudhary & Arora (2021)** — Linguistic feature based learning model | Features de complexidade textual, modais de certeza |
| 12 | **MDPI Survey** (Kuntur et al. 2026) — "Fake News Detection: It's All in the Data!" | Compilação de 93 estudos; importância de multilinguismo e cross-domain |

---

## Diagnóstico: Gaps Identificados no NLP Atual

### 1. Anti-vacina (manipulation = 0.0 para "Vacina dengue mata crianças")
- **Causa**: Sem padrões específicos anti-vax (ex: "não vacine", "efeitos colaterais escondidos")
- **Impacto**: Conteúdo anti-vacina não é detectado como manipulação

### 2. Negação Científica (manipulation = 0.0 para "Terra plana comprovada")
- **Causa**: Padrão `terra plana` existe (0.40) mas exige exatamente essa string; versões como "NASA admitiu que a Terra é plana" não são capturadas
- **Impacto**: Textos que usam autoridades falsas + negação científica escapam

### 3. Desinformação sobre Saúde
- **Causa**: Sem padrões para curas caseiras comuns, automedicação, negação de tratamento (exceto "cura milagrosa")
- **Impacto**: Um universo enorme de fake news de saúde não é detectado

### 4. CAPS Parciais
- **Causa**: CAPS boost exige >20% das palavras; palavras individuais em CAPS contribuem só 0.08 cada
- **Impacto**: Um texto com 3-4 palavras em CAPS não recebe boost adequado

### 5. Hedging Ausente como Sinal
- **Causa**: Sem métrica para ausência de hedging (linguagem de incerteza)
- **Impacto**: Afirmações categóricas sem "pode", "talvez", "provavelmente" passam despercebidas

### 6. Atribuição Vaga de Fontes
- **Causa**: Sem padrões para "dizem que", "experts say", "studies show" sem especificar
- **Impacto**: Fontes vagas são marcador forte de fake news (LIAR dataset)

---

## Plano de Implementação

### Fase 1: Novos Padrões NLP (nlp.py)

#### 1.1 Anti-Vacina (PT + EN) — 12 novas regras
```
- "não vacine" / "don't vaccinate" → 0.50
- "vacina mata|kill" / "vaccine kills" → 0.50
- "efeitos colaterais escondidos|ocultos" / "hidden side effects" → 0.45
- "ingredientes tóxicos" / "toxic ingredients" → 0.40
- "autismo" + "vacina" / "autism" + "vaccine" → 0.50
- "imunidade natural" / "natural immunity" (em contexto anti-vax) → 0.30
- "contém mercúrio|alumínio|formaldeído" / "contains mercury|aluminum" → 0.40
- "cobaias" / "guinea pigs" (para testes) → 0.35
- "testada em poucos meses" / "rushed vaccine" → 0.35
- "mortes após vacinação" / "deaths after vaccination" → 0.40
- "reação adversa" / "adverse reaction" (com apelo emocional) → 0.30
- "não aprovada" / "not approved" (fora de contexto) → 0.35
```

#### 1.2 Negação Científica (PT + EN) — 10 novas regras
```
- "NASA admitiu|confessou|revelou" / "NASA admitted" → 0.45
- "aquecimento global é farsa|mentira" / "global warming is a hoax" → 0.50
- "mudança climática é natural" / "climate change is natural" → 0.35
- "evolução é uma teoria" / "evolution is just a theory" → 0.40
- "cientistas mentem|mentiam" / "scientists lie|are lying" → 0.45
- "a ciência não prova" / "science doesn't prove" → 0.35
- "estudos refutam|desmentem" / "studies debunk|disprove" → 0.30
- "nunca foi provado" / "never been proven" → 0.35
- "dados foram manipulados|falsificados" / "data was manipulated" → 0.40
- "consenso científico é falso" / "scientific consensus is wrong" → 0.45
```

#### 1.3 Desinformação de Saúde (PT + EN) — 14 novas regras
```
- "ivermectina cura|trata|previne" / "ivermectin cures|treats" → 0.45
- "cloroquina|hidroxicloroquina" / "chloroquine|hydroxychloroquine" → 0.35
- "tratamento precoce" / "early treatment" (em contexto COVID) → 0.30
- "remédio caseiro" / "home remedy" (para doenças graves) → 0.35
- "chá de [X] cura" / "[X] tea cures" → 0.40
- "médicos proibidos de falar" / "doctors banned from speaking" → 0.45
- "protocolo proibido" / "banned protocol" → 0.40
- "cura do câncer escondida" / "cancer cure hidden" → 0.50
- "indústria farmacêutica esconde a cura" / "pharma hides the cure" → 0.50
- "água com limão|bicarbonato cura" / "lemon water|baking soda cures" → 0.45
- "quimioterapia é veneno" / "chemotherapy is poison" → 0.45
- "alimento proibido|banido" / "banned food" → 0.30
- "saúde mental é invenção" / "mental health is made up" → 0.40
- "não existe vírus|pandemia" / "virus|pandemic doesn't exist" → 0.50
```

#### 1.4 Apelo Emocional Infantil (PT + EN) — 6 novas regras
```
- "proteja seus filhos|crianças" / "protect your children" → 0.30
- "crianças estão morrendo" / "children are dying" → 0.40
- "pense nos seus filhos" / "think of your children" → 0.30
- "estão envenenando as crianças" / "poisoning the children" → 0.45
- "futuro dos nossos filhos" / "our children's future" → 0.25
- "pedofilia|tráfico de crianças" / "pedophilia|child trafficking" → 0.40
```

#### 1.5 Atribuição Vaga de Fontes (PT + EN) — 8 novas regras
```
- "dizem que|dizem por aí" / "they say|people say" → 0.25
- "li na internet|vi no Facebook|recebi no WhatsApp" → 0.30
- "um amigo médico disse" / "a doctor friend told me" → 0.30
- "fonte confiável|de confiança disse" / "a reliable source said" → 0.25
- "todo mundo sabe" / "everyone knows" → 0.25
- "é de conhecimento público" / "it's common knowledge" → 0.20
- "pesquisem vocês mesmos" / "do your own research" → 0.35
- "informação censurada" / "censored information" → 0.30
```

#### 1.6 Manipulação Financeira/Golpe (PT + EN) — 6 novas regras
```
- "ganhe dinheiro fácil|rápido" / "make easy|quick money" → 0.40
- "renda extra garantida" / "guaranteed extra income" → 0.35
- "governo vai confiscar|bloquear" / "government will seize" → 0.35
- "invista agora antes que" / "invest now before" → 0.35
- "esquema|pirâmide" / "scheme|pyramid" → 0.40
- "clique no link" / "click the link" → 0.25
```

#### 1.7 Hedging Score (nova dimensão no NLP)
Baseado em Garg & Sharma (2022) e Choudhary & Arora (2021):
- Textos legítimos usam hedging: "pode", "talvez", "provavelmente", "sugere", "indica"
- Textos falsos fazem afirmações categóricas sem hedging
- **Implementação**: Contar marcadores de hedging e reduzir manipulation score quando presentes, ou boostar quando ausentes em textos com muitas claims

```python
HEDGING_MARKERS_PT = {"pode", "poderia", "talvez", "provavelmente", "possivelmente",
                       "sugere", "indica", "aparentemente", "supostamente", "parece"}
HEDGING_MARKERS_EN = {"may", "might", "could", "possibly", "probably",
                       "suggests", "indicates", "apparently", "seemingly", "perhaps"}
```
- Se claim_score > 0.3 e nenhum hedging encontrado → boost manipulation +0.10
- Se hedging presente → reduzir manipulation por -0.05 (mín 0.0)

---

### Fase 2: Melhorias no Sistema de Scoring (scoring.py)

#### 2.1 CAPS Adaptativo
- Reduzir threshold de 20% para 10%
- Adicionar boost mais granular: >10% → +0.10, >20% → +0.15, >40% → +0.20 (urgência)

#### 2.2 Combo de Sinais (Sinergia)
Baseado em NELA-GT e cross-feature analysis:
- se manipulation > 0.30 E claim_score > 0.25: boost overall
- se urgency > 0.20 E manipulation > 0.20 E claims > 0.20: triplo sinal = boost extra

#### 2.3 Ajuste da Fórmula sem FC
Atual: `linguistic * 0.55 + claim_penalty * 0.15 + (1 - coverage * 0.30) * 0.30`
- Problema: Weight de coverage muito alto quando não há cobertura (quase sempre 0.30)
- Proposta: `linguistic * 0.60 + claim_penalty * 0.15 + (1 - coverage) * 0.25`

---

### Fase 3: Testes

#### 3.1 Testes Unitários (test_nlp.py)
- Testar cada nova categoria de padrão
- Validar scores esperados para textos anti-vax, negação científica, saúde
- Garantir que textos legítimos não disparam false positives

#### 3.2 Testes de Integração
- 3 textos completos classificados corretamente:
  - Anti-vax → HIGH ou CRITICAL
  - Negação científica → HIGH
  - Cura milagrosa → HIGH ou CRITICAL

#### 3.3 Teste Live
- 3 textos novos e inéditos na web

---

### Fase 4: Validação

- Rodar todos os 395+ testes existentes
- Build do frontend sem erros
- Live test com 3 textos novos
- Verificar que as 6 afirmações anteriores mantêm ou melhoram seus scores

---

## Resumo de Impacto Esperado

| Cenário | Score Atual | Score Esperado |
|---------|-------------|----------------|
| "Vacina dengue mata crianças" | 0.377 MODERATE | ≥0.55 HIGH |
| "Terra plana comprovada pela NASA" | 0.362 MODERATE | ≥0.55 HIGH |
| Anti-vax genérico PT | ~0.30 LOW-MOD | ≥0.60 HIGH |
| Cura milagrosa chá | ~0.30 LOW-MOD | ≥0.55 HIGH |
| Texto legítimo (notícia real) | <0.25 LOW | <0.25 LOW ✓ |

## Princípios de Design

1. **Rule-based only** — sem ML, sem custos de API, sem dependências pesadas
2. **Bilíngue PT+EN** — cada padrão em ambos os idiomas
3. **Zero cost** — nada além de regex e Python stdlib
4. **Backward-compatible** — nenhum teste existente deve quebrar
5. **Evidência citada** — cada padrão referenciado to a dataset/paper

---

*Plano criado com base na análise de 12 fontes acadêmicas e 9 bases de dados de fake news.*
