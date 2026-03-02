# BUILD PROTOCOL: FAKE NEWS REPORTING AGENT
## Protocolo de Construção Iterativa — Guia para o LLM Agente Construtor

> **INSTRUÇÃO PRIMÁRIA**: Você é um agente construtor de software. Este documento é a sua ordem de execução. Siga cada Micro-Batch sequencialmente. **NUNCA** avance para o próximo Micro-Batch sem confirmação explícita do usuário. **SEMPRE** teste antes de pedir confirmação. **SEMPRE** mostre ao usuário o que foi construído. **SEMPRE** pergunte antes de decisões arquiteturais.

---

## PROTOCOLO 0: REGRAS INVIOLÁVEIS DO AGENTE CONSTRUTOR

### 0.1 Comportamento Obrigatório

Estas regras governam TODA interação durante a construção. O agente construtor DEVE:

```
REGRA 1 — UM PASSO DE CADA VEZ
  Nunca implemente mais de um componente por interação.
  Nunca pule para o próximo passo sem testar o atual.
  Nunca adicione funcionalidade não solicitada.

REGRA 2 — CÓDIGO PRIMEIRO, EXPLICAÇÃO DEPOIS
  Responda com o bloco de código PRIMEIRO.
  Adicione explicação BREVE apenas se necessário.
  Pergunte "Quer que eu explique alguma parte?" no final.

REGRA 3 — TESTAR SEMPRE, ANTES DE AVANÇAR
  Proponha testes para cada componente implementado.
  Ofereça inputs de exemplo e outputs esperados.
  Peça para o usuário rodar o código ou confirme que rodou.
  Só avance quando testes passarem OU o usuário aprovar.

REGRA 4 — PERGUNTAR ANTES DE DECIDIR
  Antes de escolher uma biblioteca: pergunte.
  Antes de mudar a arquitetura: pergunte.
  Antes de refatorar código existente: pergunte.
  Antes de adicionar dependência nova: pergunte.

REGRA 5 — SEGURANÇA NÃO É OPCIONAL
  NUNCA hardcodar credenciais, API keys, tokens ou senhas.
  SEMPRE usar variáveis de ambiente para segredos.
  SEMPRE pseudonimizar identificadores de usuário.
  SEMPRE validar inputs antes de processar.
  NUNCA armazenar dados identificáveis de minorias (LGPD).

REGRA 6 — LINGUAGEM DO PRODUTO
  Todo texto voltado ao usuário final: português brasileiro.
  Tom: amiga mais velha sábia (nunca professoral).
  NUNCA usar "falso" ou "fake" nas mensagens ao usuário final.
  NUNCA julgar ou acusar o usuário.
  Máximo 300 caracteres por mensagem de bot.

REGRA 7 — CONFIRMAR SEMPRE
  Ao final de CADA Micro-Batch, perguntar:
    "✅ Este passo está completo. Posso avançar para [próximo passo]?"
  Se o usuário disser NÃO → corrigir, ajustar, retestar.
  Se o usuário disser SIM → avançar para próximo Micro-Batch.
```

### 0.2 Formato de Resposta do Agente

Toda resposta do agente durante a construção DEVE seguir este template:

```
📦 MICRO-BATCH [X.Y]: [Nome do passo]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Bloco de código]

🧪 TESTE PROPOSTO:
  - Input: [exemplo]
  - Output esperado: [exemplo]
  - Como rodar: [comando ou instrução]

🔍 O QUE FOI FEITO:
  - [1 linha resumindo o que o código faz]

⚠️ DECISÕES QUE PRECISO DA SUA APROVAÇÃO:
  - [Listar qualquer escolha técnica que exige confirmação]

✅ Posso avançar para [próximo Micro-Batch]?
```

### 0.3 Protocolo de Erro e Debug

Quando um erro ocorrer durante a construção:

```
PASSO 1 — COLETAR INFORMAÇÃO
  Pedir: mensagem de erro completa, stack trace, input usado.
  NUNCA adivinhar a causa sem dados.

PASSO 2 — EXPLICAR O ERRO
  Traduzir a mensagem de erro em linguagem clara.
  Indicar a linha e o componente provável.

PASSO 3 — FORMULAR HIPÓTESE
  Propor uma causa provável com linguagem tentativa ("pode ser", "provavelmente").
  NUNCA fazer mudanças aleatórias esperando que funcionem.

PASSO 4 — PROPOR CORREÇÃO
  Apresentar a correção como diff (antes/depois).
  Explicar POR QUE a correção resolve o problema.

PASSO 5 — RETESTAR
  Rodar os mesmos testes que falharam.
  Confirmar que testes anteriores não quebraram.

PASSO 6 — CONFIRMAR COM USUÁRIO
  "O erro foi corrigido. Quer que eu continue ou precisa de mais explicação?"
```

### 0.4 Protocolo de "Quando Parar e Perguntar"

O agente DEVE parar e perguntar ao usuário nestes cenários:

```
CENÁRIO 1 — AMBIGUIDADE
  Se um requisito tem mais de uma interpretação possível:
  PARAR → perguntar qual interpretação seguir.

CENÁRIO 2 — ESCOPO CRESCENDO
  Se o passo atual está ficando maior do que o planejado:
  PARAR → alertar: "Isso está ficando mais complexo que o previsto.
  Quer que eu simplifique ou seguimos com a versão mais completa?"

CENÁRIO 3 — DEPENDÊNCIA NOVA
  Se o código precisa de uma biblioteca não listada no stack:
  PARAR → "Preciso usar [biblioteca X] para [motivo]. Posso adicionar?"

CENÁRIO 4 — RISCO DE SEGURANÇA
  Se qualquer operação toca dados sensíveis:
  PARAR → "Este passo envolve [tipo de dado]. Confirma que posso prosseguir?"

CENÁRIO 5 — DECISÃO ARQUITETURAL
  Se existem 2+ formas válidas de implementar algo:
  PARAR → apresentar opções com prós e contras → deixar o usuário escolher.

CENÁRIO 6 — INCERTEZA TÉCNICA
  Se o agente não tem certeza de como implementar algo:
  PARAR → ser honesto: "Não tenho 100% de certeza sobre [X].
  Aqui está minha melhor abordagem, mas gostaria que você validasse."
```

---

## PROTOCOLO 1: DOCUMENTOS DE REFERÊNCIA

O agente construtor DEVE consultar estes documentos (já entregues ao usuário) como fonte de verdade:

| Documento | Contém | Consultar quando |
|-----------|--------|------------------|
| **AGENT_BLUEPRINT.md** | Arquitetura completa, código de referência, schema SQL, componentes React, FSM, pipelines ML, segurança, custos | Implementando qualquer componente técnico |
| **plano_agente_fake_news.md** | Visão estratégica, jornada do usuário, 8 batches, métricas, personas, sustentabilidade | Tomando decisões de produto ou UX |
| **Detector_de_Fake_News.pdf** | Visão original da fundadora, filosofia pedagógica, categorias de perguntas, diferenciação competitiva | Validando se uma decisão respeita a missão do projeto |
| **Technical Deep Dive** | Stack completo, modelos NLP, APIs, custos detalhados, PWA, LGPD | Escolhendo tecnologias, estimando custos, configurando infra |
| **Agent Code Generation Protocol** | Como o agente construtor deve se comportar, workflow iterativo, testing, debugging | Governando COMO o agente age em cada passo |

---

## PROTOCOLO 2: MAPA DE CONSTRUÇÃO — VISÃO GERAL DOS MICRO-BATCHES

A construção é dividida em **Fases**, cada Fase em **Micro-Batches**, cada Micro-Batch em **Passos**. Cada Passo produz um artefato testável.

```
FASE 1: FUNDAÇÃO (Micro-Batches 1.1 a 1.6)
  Objetivo: Projeto rodando localmente com bot simulado
  Duração estimada: 2-3 sessões de trabalho
  Resultado: Bot funcional em terminal que executa o fluxo completo de questionamento

FASE 2: CANAIS DE COMUNICAÇÃO (Micro-Batches 2.1 a 2.5)
  Objetivo: Bot conectado ao Telegram (grátis, mais fácil de testar)
  Duração estimada: 2-3 sessões de trabalho
  Resultado: Bot real no Telegram executando o fluxo de questionamento

FASE 3: PERSISTÊNCIA (Micro-Batches 3.1 a 3.5)
  Objetivo: Dados salvos em banco, sessões persistentes
  Duração estimada: 2-3 sessões de trabalho
  Resultado: Conversas sobrevivem a reinícios, métricas básicas disponíveis

FASE 4: INTELIGÊNCIA (Micro-Batches 4.1 a 4.6)
  Objetivo: NLP e análise de conteúdo integrados ao fluxo
  Duração estimada: 3-4 sessões de trabalho
  Resultado: Bot analisa texto, detecta manipulação, consulta fact-checkers

FASE 5: PLATAFORMA WEB (Micro-Batches 5.1 a 5.8)
  Objetivo: PWA funcional com Balança da Evidência
  Duração estimada: 4-5 sessões de trabalho
  Resultado: Web app acessível via link do bot com análise visual

FASE 6: INTEGRAÇÃO COMPLETA (Micro-Batches 6.1 a 6.4)
  Objetivo: Bot + Web integrados, transição fluida, analytics
  Duração estimada: 2-3 sessões de trabalho
  Resultado: Sistema end-to-end funcional

FASE 7: WHATSAPP E PRODUÇÃO (Micro-Batches 7.1 a 7.5)
  Objetivo: WhatsApp Cloud API integrado, deploy em nuvem
  Duração estimada: 3-4 sessões de trabalho
  Resultado: Sistema em produção no WhatsApp

FASE 8: FUNCIONALIDADES AVANÇADAS (Micro-Batches 8.1 a 8.6)
  Objetivo: Deepfakes, Radar de Tendências, Módulos de Aprendizagem
  Duração estimada: 4-5 sessões de trabalho
  Resultado: Plataforma completa conforme AGENT_BLUEPRINT.md
```

---

## FASE 1: FUNDAÇÃO

### Micro-Batch 1.1 — Estrutura do Projeto e Ambiente

**Objetivo**: Criar a estrutura de diretórios, configurar ambiente Python, instalar dependências base.

**O que construir**:
```
fake-news-agent/
├── apps/
│   └── bot/
│       ├── src/
│       │   ├── __init__.py
│       │   ├── main.py            # Entry point (vazio por ora)
│       │   └── config.py          # Configuração via env vars
│       ├── tests/
│       │   └── __init__.py
│       ├── requirements.txt
│       └── .env.example
├── .gitignore
└── README.md
```

**Dependências iniciais** (requirements.txt):
```
fastapi==0.115.6
uvicorn==0.34.0
python-dotenv==1.0.1
pydantic==2.10.0
redis==5.2.1
transitions==0.9.2
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.25.0
```

**Teste para este passo**:
```bash
# Criar virtualenv, instalar deps, confirmar que importa sem erro
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "import fastapi, transitions, redis, httpx; print('✅ Todas dependências OK')"
```

**Gate de confirmação**: "Ambiente configurado e dependências instaladas com sucesso. Posso avançar para o Micro-Batch 1.2 (Modelo de Dados da Conversa)?"

---

### Micro-Batch 1.2 — Modelo de Dados da Conversa

**Objetivo**: Criar a dataclass `ConversationContext` que carrega todo o estado de uma conversa.

**O que construir**: `apps/bot/src/models.py`

**Referência**: Seção 2.2 do AGENT_BLUEPRINT.md — `ConversationContext` dataclass

**Campos obrigatórios**:
- `user_id` (str) — ID pseudonimizado, NUNCA o telefone real
- `platform` (str) — 'whatsapp' | 'telegram' | 'terminal'
- `content_type` (str) — 'text' | 'link' | 'image' | 'video' | 'audio'
- `content_raw` (str) — conteúdo original enviado
- `content_id` (str) — UUID para referência na web
- `motivation` (str) — motivação selecionada pelo usuário
- `emotion` (str) — emoção detectada ou declarada
- `source_trust` (str) — nível de confiança na fonte
- `reflection_answers` (list) — histórico de respostas
- `final_decision` (str) — 'share' | 'not_share' | 'investigate'
- `started_at` (str) — ISO timestamp
- `last_interaction_at` (str) — ISO timestamp
- `interaction_count` (int)

**Testes para este passo**:
```python
# tests/test_models.py
def test_conversation_context_creation():
    """Contexto cria com defaults corretos."""
    ctx = ConversationContext(user_id="abc123", platform="telegram")
    assert ctx.user_id == "abc123"
    assert ctx.platform == "telegram"
    assert ctx.interaction_count == 0
    assert ctx.reflection_answers == []
    assert ctx.final_decision == ''

def test_conversation_context_serialization():
    """Contexto serializa para JSON e deserializa corretamente (para Redis)."""
    ctx = ConversationContext(user_id="abc123", platform="whatsapp")
    ctx.motivation = "inform"
    json_str = ctx.to_json()
    restored = ConversationContext.from_json(json_str)
    assert restored.motivation == "inform"
    assert restored.user_id == "abc123"
```

**Comando para rodar testes**:
```bash
cd apps/bot && python -m pytest tests/test_models.py -v
```

**Gate de confirmação**: "Modelo de dados criado e testado. Posso avançar para 1.3 (Definição dos Fluxos de Questionamento)?"

---

### Micro-Batch 1.3 — Definição dos Fluxos de Questionamento (YAML)

**Objetivo**: Criar o arquivo YAML com TODAS as perguntas, opções e respostas do bot, seguindo a lógica definida no AGENT_BLUEPRINT.md Seção 2.1.

**O que construir**: `apps/bot/src/engine/flows/questioning.yaml`

**Este é o arquivo mais importante do projeto.** Ele define TODA a experiência do usuário no bot. Cada pergunta, cada opção, cada resposta condicional.

**Estrutura do YAML**:
```yaml
flow:
  greeting:
    message: "Obrigada por compartilhar! 🙏 Para te ajudar a pensar um pouco mais sobre este conteúdo, tenho uma pergunta para você:"
    follow_up:
      message: "Qual o seu principal motivo para querer compartilhar este conteúdo?"
      type: "list"  # list | buttons | text
      options:
        - id: "inform"
          title: "Para informar as pessoas"
          next_state: "exploring_inform"
        - id: "alert"
          title: "Para alertar sobre algo importante"
          next_state: "exploring_alert"
        # ... (todas as 6 opções do AGENT_BLUEPRINT.md)

  exploring_inform:
    message: "Que bom que você quer informar! Para que a informação seja a mais precisa possível, você já pensou de onde ela veio e quem a produziu?"
    type: "buttons"
    options:
      - id: "trust_source"
        title: "Confio na fonte"
        next_state: "deepening_trust"
      - id: "unknown_source"
        title: "Não sei bem a fonte"
        next_state: "deepening_unknown"
      - id: "didnt_think"
        title: "Não pensei nisso"
        next_state: "deepening_unknown"

  # ... (todos os estados do AGENT_BLUEPRINT.md Seção 2.1)

  closing:
    message: "Suas reflexões são muito valiosas! 💛 Agora, com base em tudo o que você pensou, você ainda quer compartilhar este conteúdo?"
    type: "buttons"
    options:
      - id: "yes_share"
        title: "Sim, quero compartilhar"
        next_state: "feedback_share"
      - id: "no_changed_mind"
        title: "Não, mudei de ideia"
        next_state: "feedback_not_share"
      - id: "want_deeper"
        title: "Quero investigar mais"
        next_state: "feedback_investigate"

  feedback_share:
    message: "Tudo bem! O importante é que você pensou sobre isso antes. Se quiser, nosso espaço de investigação na web tem ferramentas para analisar fontes."
    next_state: "end"

  feedback_not_share:
    message: "Sua capacidade de questionar e refletir é poderosa! 💪 Você acaba de proteger sua comunidade de uma possível informação incorreta."
    next_state: "end"

  feedback_investigate:
    message: "Que incrível! Preparei um espaço especial de investigação para você:"
    follow_up:
      message: "👉 {web_url}/analise/{content_id}"
      type: "text"
    next_state: "end"

  end:
    message: "Lembre-se: questionar não é desconfiar de tudo. É cuidar de si e de quem você ama. 🤗"
```

**Testes para este passo**:
```python
# tests/test_flows.py
import yaml

def test_yaml_loads_correctly():
    """YAML carrega sem erros de sintaxe."""
    with open("src/engine/flows/questioning.yaml") as f:
        flow = yaml.safe_load(f)
    assert "flow" in flow
    assert "greeting" in flow["flow"]
    assert "closing" in flow["flow"]
    assert "end" in flow["flow"]

def test_all_next_states_exist():
    """Todo next_state referenciado existe como state no YAML."""
    with open("src/engine/flows/questioning.yaml") as f:
        flow = yaml.safe_load(f)["flow"]
    all_states = set(flow.keys())
    for state_name, state_data in flow.items():
        if "options" in state_data:
            for opt in state_data["options"]:
                if "next_state" in opt:
                    assert opt["next_state"] in all_states, \
                        f"State '{opt['next_state']}' referenced by '{state_name}' doesn't exist"

def test_no_message_exceeds_300_chars():
    """Nenhuma mensagem ultrapassa 300 caracteres (WhatsApp readability)."""
    with open("src/engine/flows/questioning.yaml") as f:
        flow = yaml.safe_load(f)["flow"]
    for state_name, state_data in flow.items():
        if "message" in state_data:
            assert len(state_data["message"]) <= 300, \
                f"Message in '{state_name}' has {len(state_data['message'])} chars (max 300)"

def test_closing_exists_and_has_three_options():
    """O estado de fechamento tem exatamente 3 opções."""
    with open("src/engine/flows/questioning.yaml") as f:
        flow = yaml.safe_load(f)["flow"]
    assert "closing" in flow
    assert len(flow["closing"]["options"]) == 3

def test_no_judgmental_language():
    """Nenhuma mensagem contém linguagem acusatória ou julgadora."""
    forbidden = ["falso", "fake", "mentira", "errado", "burro", "ignorante", "ingênuo"]
    with open("src/engine/flows/questioning.yaml") as f:
        flow = yaml.safe_load(f)["flow"]
    for state_name, state_data in flow.items():
        if "message" in state_data:
            msg_lower = state_data["message"].lower()
            for word in forbidden:
                assert word not in msg_lower, \
                    f"Forbidden word '{word}' found in state '{state_name}'"
```

**Gate de confirmação**: "Fluxo de questionamento definido com [N] estados e [N] transições. Todos os testes passam. Posso avançar para 1.4 (Motor FSM)?"

---

### Micro-Batch 1.4 — Motor FSM (Finite State Machine)

**Objetivo**: Implementar a classe `QuestioningFSM` que lê o YAML e gerencia estados.

**O que construir**: `apps/bot/src/engine/fsm.py`

**Referência**: AGENT_BLUEPRINT.md Seção 2.2

**Comportamento esperado**:
1. Inicializa no estado `awaiting_content`
2. Quando recebe conteúdo, transiciona para `greeting`
3. Quando recebe seleção de opção, transiciona para o `next_state` correspondente
4. Quando chega ao estado `end`, a conversa termina
5. Cada transição atualiza o `ConversationContext`
6. Se recebe input inesperado, retorna mensagem de fallback
7. Máximo 4 interações antes de ir para `closing`
8. Timeout de 30 minutos por sessão

**Testes para este passo**:
```python
# tests/test_fsm.py

def test_fsm_starts_in_awaiting_content():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    assert fsm.state == "awaiting_content"

def test_fsm_transitions_to_greeting_on_content():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    response = fsm.process_input("Olha essa notícia sobre saúde")
    assert fsm.state == "greeting"
    assert len(response["messages"]) >= 1
    assert "options" in response["messages"][-1] or "seguir" in str(response)

def test_fsm_transitions_based_on_option_selection():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    fsm.process_input("Uma notícia qualquer")  # → greeting
    response = fsm.process_input("inform")      # → exploring_inform
    assert fsm.state == "exploring_inform"
    assert ctx.motivation == "inform"

def test_fsm_reaches_closing():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    fsm.process_input("notícia")        # → greeting
    fsm.process_input("inform")          # → exploring_inform
    fsm.process_input("trust_source")    # → deepening_trust
    response = fsm.process_input("always_right")  # → closing
    assert fsm.state == "closing"

def test_fsm_records_final_decision():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    # Walk through full flow...
    fsm.process_input("notícia")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    fsm.process_input("always_right")
    fsm.process_input("no_changed_mind")   # → feedback_not_share
    assert ctx.final_decision == "not_share"

def test_fsm_handles_invalid_input():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    fsm.process_input("notícia")  # → greeting
    response = fsm.process_input("xyzzy_nonsense")  # Invalid
    assert fsm.state == "greeting"  # Should NOT advance
    assert "fallback" in str(response).lower() or "escolher" in str(response).lower()

def test_fsm_interaction_count_increments():
    ctx = ConversationContext(user_id="test", platform="terminal")
    fsm = QuestioningFSM(ctx)
    fsm.process_input("notícia")
    assert ctx.interaction_count == 1
    fsm.process_input("inform")
    assert ctx.interaction_count == 2
```

**Gate de confirmação**: "FSM implementado com [N] estados. Todos os [N] testes passam. Posso avançar para 1.5 (Interface de Terminal)?"

---

### Micro-Batch 1.5 — Interface de Terminal (Bot Humano Simulado)

**Objetivo**: Criar uma interface interativa de terminal que simula a experiência do bot, permitindo testar o fluxo completo sem nenhuma API externa.

**O que construir**: `apps/bot/src/terminal_runner.py`

**Comportamento**:
```
$ python -m src.terminal_runner

🤖 Mentor Digital — Modo Terminal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Envie qualquer conteúdo para começar.
Digite 'sair' para encerrar.

Você: Recebi uma mensagem dizendo que vacina causa autismo

🤖: Obrigada por compartilhar! 🙏 Para te ajudar a pensar um pouco mais...

   Qual o seu principal motivo para querer compartilhar este conteúdo?

   [1] Para informar as pessoas
   [2] Para alertar sobre algo importante
   [3] Para expressar minha opinião
   [4] Me identifico com a mensagem
   [5] Vi em vários lugares
   [6] Outro motivo

Você: 2

🤖: É ótimo querer alertar! Que emoção essa notícia te provoca?

   [1] Medo ou preocupação
   [2] Raiva ou indignação
   [3] Surpresa ou choque

Você: 1

🤖: Quando sentimos medo, nosso cérebro quer agir rápido para proteger...
   ...
```

**Testes para este passo**:
```python
# Teste manual — o agente DEVE pedir ao usuário que rode:
# python -m src.terminal_runner
# E percorra o fluxo completo respondendo diferentes opções.
# Verificar:
#   ✅ Todas as perguntas aparecem no tom correto?
#   ✅ As opções são clicáveis/selecionáveis?
#   ✅ O fluxo chega ao final corretamente?
#   ✅ Input inválido gera fallback amigável?
#   ✅ Nenhuma mensagem contém linguagem proibida?
```

**Nota para o agente**: Este é um passo de TESTE MANUAL. Peça ao usuário para rodar e reportar. Não avance sem feedback.

**Gate de confirmação**: "Terminal runner funcionando. O usuário testou o fluxo completo. Posso avançar para 1.6 (Pseudonimização e Config de Segurança)?"

---

### Micro-Batch 1.6 — Pseudonimização e Configuração de Segurança

**Objetivo**: Implementar a função de pseudonimização e o sistema de config via environment variables.

**O que construir**:
- `apps/bot/src/security.py` — funções de pseudonimização
- `apps/bot/src/config.py` — config centralizada via .env

**Referência**: AGENT_BLUEPRINT.md Seção 6.2

**Testes para este passo**:
```python
# tests/test_security.py

def test_pseudonymize_is_deterministic():
    """Mesmo input sempre gera mesmo output."""
    result1 = pseudonymize("+5511999998888")
    result2 = pseudonymize("+5511999998888")
    assert result1 == result2

def test_pseudonymize_is_irreversible():
    """Output não contém o input original."""
    phone = "+5511999998888"
    result = pseudonymize(phone)
    assert phone not in result
    assert "999998888" not in result

def test_pseudonymize_different_inputs_different_outputs():
    """Inputs diferentes geram outputs diferentes."""
    result1 = pseudonymize("+5511999998888")
    result2 = pseudonymize("+5511999997777")
    assert result1 != result2

def test_pseudonymize_analytics_separate_from_operational():
    """Pseudônimo analítico é diferente do operacional."""
    result_ops = pseudonymize("+5511999998888")
    result_analytics = pseudonymize_for_analytics("+5511999998888")
    assert result_ops != result_analytics

def test_config_loads_from_env():
    """Configurações carregam de variáveis de ambiente."""
    import os
    os.environ["PSEUDONYMIZATION_PEPPER"] = "test_pepper"
    config = load_config()
    assert config.pseudonymization_pepper == "test_pepper"

def test_config_fails_without_required_vars():
    """Configuração falha se variáveis obrigatórias estão ausentes."""
    import os
    if "PSEUDONYMIZATION_PEPPER" in os.environ:
        del os.environ["PSEUDONYMIZATION_PEPPER"]
    with pytest.raises(ValueError):
        load_config()
```

**Gate de confirmação**: "Segurança base implementada. Todos os testes passam. FASE 1 COMPLETA ✅. Posso avançar para a FASE 2 (Canais de Comunicação — Telegram)?"

---

## FASE 2: CANAIS DE COMUNICAÇÃO

### Micro-Batch 2.1 — Telegram Bot Setup

**Objetivo**: Criar bot no Telegram via @BotFather, configurar token, testar conexão.

**⚠️ REQUER AÇÃO DO USUÁRIO**: O agente DEVE pedir ao usuário para:
1. Abrir @BotFather no Telegram
2. Enviar `/newbot`
3. Escolher nome e username
4. Copiar o token gerado
5. Adicionar o token ao `.env` como `TELEGRAM_BOT_TOKEN=...`

**O que construir**: `apps/bot/src/webhooks/telegram.py` (esqueleto)

**Teste**: Verificar que o bot responde a `/start` no Telegram.

**Gate**: "Bot criado no Telegram e respondendo a /start. Posso avançar para 2.2?"

---

### Micro-Batch 2.2 — Telegram Handler com FSM

**Objetivo**: Conectar o handler do Telegram à FSM existente.

**Comportamento**: Mensagens do Telegram são processadas pela mesma FSM do terminal. Respostas são formatadas com InlineKeyboardButtons.

**Testes**: Enviar conteúdo no Telegram → bot responde com perguntas → percorrer fluxo completo.

**Gate**: "Fluxo completo funciona no Telegram com botões. Posso avançar para 2.3?"

---

### Micro-Batch 2.3 — Session Manager (Redis)

**Objetivo**: Implementar gerenciamento de sessão com Redis para que conversas persistam entre mensagens.

**O que construir**: `apps/bot/src/services/session.py`

**Comportamento**:
- Salva estado da FSM + ConversationContext em Redis
- Key: `session:{user_id}`
- TTL: 24 horas (alinhado com janela do WhatsApp)
- Operações: `get_or_create()`, `save()`, `delete()`

**Testes**:
```python
def test_session_save_and_restore():
    """Sessão salva em Redis e restaura corretamente."""

def test_session_expires_after_ttl():
    """Sessão expira após o TTL configurado."""

def test_session_handles_concurrent_messages():
    """Duas mensagens do mesmo usuário não corrompem a sessão."""
```

**Gate**: "Sessões persistem no Redis. Bot mantém contexto entre mensagens. Posso avançar para 2.4?"

---

### Micro-Batch 2.4 — Content Type Detection

**Objetivo**: Detectar o tipo de conteúdo enviado pelo usuário (texto, link, imagem, vídeo, áudio).

**O que construir**: `apps/bot/src/services/content_processor.py`

**Testes**:
```python
def test_detects_url():
    assert detect_content_type("https://example.com/news") == "link"

def test_detects_plain_text():
    assert detect_content_type("Vacina causa autismo") == "text"

def test_detects_forwarded_message_pattern():
    assert is_likely_forwarded("Encaminhada muitas vezes") == True
```

**Gate**: "Detecção de tipo de conteúdo funcionando. Posso avançar para 2.5?"

---

### Micro-Batch 2.5 — Gateway FastAPI com Webhook

**Objetivo**: Criar o servidor FastAPI que recebe webhooks do Telegram (e futuramente do WhatsApp).

**O que construir**: `apps/bot/src/main.py` (expandir)

**Inclui**:
- Rota `/webhook/telegram` (POST)
- Health check `/health`
- Rate limiting com `slowapi`
- Input validation com Pydantic

**Testes**:
```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_telegram_webhook_rejects_invalid_payload():
    response = client.post("/webhook/telegram", json={"invalid": True})
    assert response.status_code == 422

def test_telegram_webhook_accepts_valid_message():
    payload = make_telegram_update(text="teste")
    response = client.post("/webhook/telegram", json=payload)
    assert response.status_code == 200
```

**Gate**: "FASE 2 COMPLETA ✅. Bot funcional no Telegram com sessões persistentes e gateway FastAPI. Posso avançar para FASE 3 (Persistência)?"

---

## FASE 3: PERSISTÊNCIA

### Micro-Batch 3.1 — Schema PostgreSQL

**Objetivo**: Criar as tabelas do banco de dados conforme AGENT_BLUEPRINT.md Seção 4.

**O que construir**: `infra/database/schema.sql` + SQLAlchemy models

**Tabelas neste batch**: `users`, `conversations`, `submissions`

**Gate**: "Schema criado e migrations rodam sem erro. Posso criar as tabelas de análise (3.2)?"

---

### Micro-Batch 3.2 — Tabelas de Análise

**Tabelas**: `claims`, `sources`, `evidence`, `analysis_results`

**Gate**: "Tabelas de análise criadas. Posso implementar a camada de acesso (3.3)?"

---

### Micro-Batch 3.3 — Camada de Acesso a Dados (Repository Pattern)

**O que construir**: `apps/bot/src/repositories/` com classes que encapsulam queries.

**Gate**: "Repository layer funcional com testes. Posso integrar ao bot (3.4)?"

---

### Micro-Batch 3.4 — Integração Bot → Banco

**Objetivo**: Cada conversa do bot agora salva em PostgreSQL automaticamente.

**Gate**: "Conversas persistem no banco. Posso criar analytics básico (3.5)?"

---

### Micro-Batch 3.5 — Analytics Dashboard SQL

**Objetivo**: Criar a view `v_impact_metrics` e queries para métricas.

**Testes**: Inserir dados fake → rodar queries → confirmar métricas.

**Gate**: "FASE 3 COMPLETA ✅. Dados persistentes, métricas calculáveis. Posso avançar para FASE 4 (Inteligência)?"

---

## FASE 4: INTELIGÊNCIA (NLP)

### Micro-Batch 4.1 — Análise de Sentimento (pysentimiento)

**Objetivo**: Integrar `pysentimiento` para analisar sentimento e emoção do conteúdo.

**O que construir**: `packages/ml/models/sentiment.py`

**Teste**: Analisar 5 textos de exemplo (positivo, negativo, medo, raiva, neutro) → confirmar outputs.

**Gate**: "Sentiment analysis funcionando. Posso adicionar detecção de manipulação (4.2)?"

---

### Micro-Batch 4.2 — Detecção de Manipulação (Rule-Based)

**Objetivo**: Implementar os patterns regex de manipulação do AGENT_BLUEPRINT.md.

**Categorias**: urgência, falsa autoridade, apelo emocional, marcadores de conspiração.

**Teste**: 10 textos de exemplo → confirmar detecção correta.

**Gate**: "Manipulação detectada corretamente. Posso integrar fact-checking (4.3)?"

---

### Micro-Batch 4.3 — Google Fact Check Tools API

**Objetivo**: Integrar a API gratuita do Google para buscar fact-checks existentes.

**O que construir**: `apps/bot/src/analysis/fact_checker.py`

**⚠️ REQUER AÇÃO DO USUÁRIO**: Obter API key do Google Cloud (gratuita).

**Teste**: Buscar 3 claims conhecidos → confirmar que retorna fact-checks.

**Gate**: "Fact-check API integrada. Posso adicionar verificação de fontes (4.4)?"

---

### Micro-Batch 4.4 — Verificação de Fontes (Domain Credibility)

**Objetivo**: Analisar domínios: idade, SSL, WHOIS, presença em listas de fact-checkers.

**Teste**: Verificar 5 domínios (3 confiáveis, 2 suspeitos) → confirmar scores.

**Gate**: "Source verification funcionando. Posso construir a Balança da Evidência (4.5)?"

---

### Micro-Batch 4.5 — Balança da Evidência (Backend)

**Objetivo**: Pipeline completo de coleta e scoring de evidências.

**Referência**: AGENT_BLUEPRINT.md Seção 3.2

**Teste**: Submeter 3 claims → confirmar balance_score e listas de evidências.

**Gate**: "Evidence pipeline funcionando. Posso integrar ao fluxo do bot (4.6)?"

---

### Micro-Batch 4.6 — Integração NLP → Bot

**Objetivo**: Quando o usuário envia conteúdo, a análise NLP roda em background e os resultados informam o fluxo de perguntas.

**Comportamento**: A análise NÃO muda as perguntas — apenas enriquece os dados para a plataforma web.

**Gate**: "FASE 4 COMPLETA ✅. NLP integrado. Posso avançar para FASE 5 (Plataforma Web)?"

---

## FASE 5: PLATAFORMA WEB (PWA)

### Micro-Batch 5.1 — Setup Next.js 15 + Tailwind + shadcn/ui

**Gate**: "Projeto Next.js criado e rodando. Posso criar o layout base (5.2)?"

### Micro-Batch 5.2 — Layout Base e PWA Config

**Inclui**: manifest.json, service worker, layout responsivo, tema.

**Gate**: "PWA instalável no Android. Posso criar a página de análise (5.3)?"

### Micro-Batch 5.3 — Página de Análise de Conteúdo

**A página que o bot linka quando o usuário escolhe "Quero investigar mais".**

**Gate**: "Página de análise renderiza dados. Posso criar o componente Balança (5.4)?"

### Micro-Batch 5.4 — Componente Balança da Evidência

**Referência**: AGENT_BLUEPRINT.md Seção 5.1

**Gate**: "Balança visual funcionando. Posso criar o Guia de Fontes (5.5)?"

### Micro-Batch 5.5 — Guia de Análise de Fontes

**Checklist interativo para o usuário avaliar fontes.**

**Gate**: "Guia de fontes funcionando. Posso criar os Módulos de Aprendizagem (5.6)?"

### Micro-Batch 5.6 — Módulos de Aprendizagem

**Referência**: AGENT_BLUEPRINT.md Seção 8

**Gate**: "Módulos interativos funcionando. Posso criar o Guia de Ação (5.7)?"

### Micro-Batch 5.7 — Guia de Ação para Conteúdo Criminoso

**Links para denúncia, documentação de provas.**

**Gate**: "Guia de ação completo. Posso configurar acessibilidade (5.8)?"

### Micro-Batch 5.8 — Acessibilidade e Performance

**Auditoria WCAG 2.2 AA, Lighthouse score, otimização para 3G.**

**Target**: Lighthouse ≥90 em Performance, ≥95 em Accessibility.

**Gate**: "FASE 5 COMPLETA ✅. Plataforma web acessível e performática. Posso avançar para FASE 6?"

---

## FASE 6: INTEGRAÇÃO COMPLETA

### Micro-Batch 6.1 — Transição Bot → Web

**Objetivo**: Link do bot abre a web com dados da análise pré-carregados.

### Micro-Batch 6.2 — API de Análise (Backend Web)

**Objetivo**: Endpoints REST para a web consumir dados de análise.

### Micro-Batch 6.3 — Analytics e Métricas de Impacto

**Referência**: AGENT_BLUEPRINT.md Seção 10

### Micro-Batch 6.4 — Feedback Loop

**Objetivo**: Coletar feedback do usuário ao final da jornada web.

**Gate**: "FASE 6 COMPLETA ✅. Sistema integrado end-to-end. Posso avançar para FASE 7 (WhatsApp)?"

---

## FASE 7: WHATSAPP E PRODUÇÃO

### Micro-Batch 7.1 — WhatsApp Cloud API Setup

**⚠️ REQUER AÇÕES DO USUÁRIO**: Meta Developer account, Business App, phone number verification.

### Micro-Batch 7.2 — WhatsApp Webhook Handler

**Referência**: AGENT_BLUEPRINT.md Seção 2.3

### Micro-Batch 7.3 — Interactive Messages (Buttons, Lists)

**Adaptar FSM responses para formatos WhatsApp.**

### Micro-Batch 7.4 — Deploy AWS (Terraform)

**Referência**: AGENT_BLUEPRINT.md Seção 7

### Micro-Batch 7.5 — CI/CD Pipeline

**GitHub Actions: lint → test → security scan → deploy.**

**Gate**: "FASE 7 COMPLETA ✅. Sistema em produção no WhatsApp. Posso avançar para FASE 8?"

---

## FASE 8: FUNCIONALIDADES AVANÇADAS

### Micro-Batch 8.1 — BERTimbau Fine-Tuning (Fake.BR Corpus)

### Micro-Batch 8.2 — Detecção de Deepfakes (DeepfakeBench)

### Micro-Batch 8.3 — Radar de Tendências (GDELT + YouTube)

### Micro-Batch 8.4 — Análise de Vieses Algorítmicos (Fairlearn + AIF360)

### Micro-Batch 8.5 — Gamificação e Badges

### Micro-Batch 8.6 — Auditoria Final de Segurança e LGPD

**Gate**: "FASE 8 COMPLETA ✅. SISTEMA COMPLETO CONFORME AGENT_BLUEPRINT.md."

---

## PROTOCOLO 3: CHECKLIST DE QUALIDADE — RODAR EM CADA MICRO-BATCH

Antes de declarar qualquer Micro-Batch como completo, o agente DEVE verificar:

```
□ Código roda sem erros?
□ Testes propostos passam?
□ Nenhum segredo hardcodado no código?
□ Nenhuma mensagem ao usuário final contém linguagem proibida?
□ Código segue PEP 8 (Python) ou ESLint (TypeScript)?
□ Funções têm nomes descritivos (não abreviações)?
□ Inputs são validados antes de processar?
□ Dados de usuário são pseudonimizados?
□ Componentes web são acessíveis (aria-labels, keyboard nav)?
□ Performance aceitável para 3G? (se aplicável)
□ O passo atual NÃO introduziu funcionalidade não solicitada?
□ Usuário foi consultado sobre decisões arquiteturais?
□ Documentação inline (docstrings/comments) nos trechos complexos?
```

---

## PROTOCOLO 4: COMANDOS ESPECIAIS DO USUÁRIO

O usuário pode usar estes comandos a qualquer momento:

```
"PARE"
  → Agente para imediatamente e espera instruções.

"EXPLIQUE"
  → Agente explica o código atual em detalhe.

"SIMPLIFIQUE"
  → Agente reescreve o código atual de forma mais simples.

"TESTE COMPLETO"
  → Agente roda toda a suíte de testes existente e reporta resultados.

"STATUS"
  → Agente mostra: Fase atual, Micro-Batch atual, % completado, próximos passos.

"VOLTE"
  → Agente retorna ao Micro-Batch anterior.

"PULE"
  → Agente marca o Micro-Batch atual como adiado e avança para o próximo.

"MAPA"
  → Agente mostra o mapa completo de Fases e Micro-Batches com status.

"PREOCUPAÇÃO: [texto]"
  → Agente registra a preocupação e propõe como endereçá-la.
```

---

## PROTOCOLO 5: COMO INICIAR A CONSTRUÇÃO

Quando o usuário disser "Vamos começar a construir" ou equivalente, o agente DEVE:

```
1. Confirmar que tem acesso aos documentos de referência.
2. Apresentar o MAPA completo de Fases e Micro-Batches.
3. Perguntar: "Quer começar pela Fase 1, Micro-Batch 1.1
   (Estrutura do Projeto)? Ou prefere pular para outra fase?"
4. Aguardar confirmação ANTES de escrever qualquer código.
5. Ao receber confirmação, seguir o formato de resposta do Protocolo 0.2.
```

**Primeira mensagem do agente ao iniciar**:
```
📋 MAPA DE CONSTRUÇÃO — Fake News Reporting Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⬜ FASE 1: Fundação (6 micro-batches)
⬜ FASE 2: Canais de Comunicação — Telegram (5 micro-batches)
⬜ FASE 3: Persistência — PostgreSQL (5 micro-batches)
⬜ FASE 4: Inteligência — NLP (6 micro-batches)
⬜ FASE 5: Plataforma Web — PWA (8 micro-batches)
⬜ FASE 6: Integração Completa (4 micro-batches)
⬜ FASE 7: WhatsApp e Produção (5 micro-batches)
⬜ FASE 8: Funcionalidades Avançadas (6 micro-batches)

Total: 45 micro-batches · Estimativa: 20-30 sessões de trabalho

Cada micro-batch produz código testável. Eu nunca avanço sem
sua aprovação. Vamos começar pela Fase 1?
```

---

*Build Protocol v1.0 — Fevereiro 2026*
*Este documento governa TODO o processo de construção.*
*O agente construtor DEVE consultá-lo a cada passo.*
*O usuário TEM autoridade final sobre toda decisão.*
