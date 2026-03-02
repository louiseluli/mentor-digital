# AGENT BLUEPRINT: FAKE NEWS REPORTING AGENT
## Documento Executável para Construção por LLM — Versão Completa

> **INSTRUÇÃO PARA O LLM AGENTE**: Este documento é a sua fonte única de verdade. Ele contém TODA a informação necessária para projetar, construir e implementar o sistema. Siga cada seção sequencialmente. Não invente funcionalidades que não estão aqui. Não omita funcionalidades que estão aqui. Quando houver dúvida, priorize a experiência do usuário vulnerável.

---

## SEÇÃO 0: CONTEXTO INVIOLÁVEL

### 0.1 O Que Você Está Construindo
Um sistema híbrido (Bot de WhatsApp/Telegram + Plataforma Web PWA) que atua como **mentor digital** para ajudar minorias interseccionais brasileiras — especialmente mulheres negras — a questionar, analisar e decidir conscientemente sobre informações antes de compartilhá-las. O sistema usa uma abordagem pedagógica de "mais perguntas que respostas".

### 0.2 Princípios Invioláveis de Design
Toda decisão técnica DEVE respeitar estes princípios. Se houver conflito entre performance técnica e estes princípios, os princípios vencem:

1. **NUNCA dar vereditos prontos.** O sistema guia, não julga. A conclusão é SEMPRE do usuário.
2. **Linguagem SEMPRE acolhedora, neutra em gênero, não acusatória.** Nunca faça o usuário se sentir julgado ou ignorante.
3. **Acessibilidade primeiro.** Tudo deve funcionar em smartphones básicos Android com 3G e planos de dados limitados.
4. **Privacidade como direito fundamental.** Dados de minorias são classificados como dados sensíveis pela LGPD. Trate-os como tal.
5. **Empoderamento, não dependência.** O objetivo final é que o usuário não precise mais do sistema.
6. **WhatsApp é rei.** No Brasil, especialmente para o público-alvo, WhatsApp É a internet. É o canal primário.

### 0.3 Persona de Referência: Maria
Toda decisão de UX deve ser validada contra esta persona:
- **Quem**: Mulher negra, 35 anos, moradora de periferia urbana, ativa em 8+ grupos de WhatsApp (família, igreja, trabalho, comunidade).
- **Dispositivo**: Android básico (Samsung Galaxy A04 ou similar), plano pré-pago com 5–10GB/mês.
- **Comportamento digital**: Consome conteúdo via WhatsApp e Instagram. Compartilha conteúdo emocional rapidamente. Confia em mensagens encaminhadas por pessoas próximas.
- **Dor**: Recebe muita desinformação que a afeta emocionalmente. Quer proteger sua família e comunidade mas não sabe como verificar.
- **Contexto de ameaça**: É frequentemente alvo de desinformação sobre saúde (ex: tratamentos falsos), política (ex: narrativas racistas disfarçadas), religião, e segurança pública.

---

## SEÇÃO 1: ARQUITETURA DO SISTEMA

### 1.1 Diagrama de Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CANAIS DE ENTRADA                           │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│   │  WhatsApp     │    │  Telegram     │    │  Web Platform (PWA)  │ │
│   │  Cloud API    │    │  Bot API 9.4  │    │  Next.js 15          │ │
│   │  (Primário)   │    │  (Secundário) │    │  (Aprofundamento)    │ │
│   └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘ │
│          │                   │                       │              │
└──────────┼───────────────────┼───────────────────────┼──────────────┘
           │                   │                       │
           ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CAMADA DE GATEWAY                             │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              FastAPI Gateway (Python 3.11+)                  │  │
│   │  • Webhook handler (HMAC-SHA256 verification)               │  │
│   │  • Rate limiting (slowapi)                                   │  │
│   │  • Request routing                                           │  │
│   │  • Input sanitization                                        │  │
│   └──────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAMADA DE ORQUESTRAÇÃO                           │
│                                                                     │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│   │ Session Mgr   │  │  FSM Engine   │  │  Conversation         │ │
│   │ (Redis)       │  │  (transitions │  │  Context Tracker      │ │
│   │ TTL: 24h      │  │   library)    │  │  (user state,         │ │
│   │               │  │               │  │   history, scores)    │ │
│   └───────┬───────┘  └───────┬───────┘  └───────────┬───────────┘ │
│           │                  │                       │              │
└───────────┼──────────────────┼───────────────────────┼──────────────┘
            │                  │                       │
            ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CAMADA DE ANÁLISE (ML/NLP)                        │
│                                                                     │
│   ┌────────────────┐  ┌────────────────┐  ┌──────────────────────┐│
│   │ Text Analyzer  │  │ Source Verifier│  │ Deepfake Detector    ││
│   │ • BERTimbau    │  │ • WHOIS lookup │  │ • DeepfakeBench      ││
│   │ • Sentiment    │  │ • Domain age   │  │ • XceptionNet        ││
│   │ • Propaganda   │  │ • SSL check    │  │ • Perceptual hash    ││
│   │   detection    │  │ • Credibility  │  │ • CLIP embeddings    ││
│   │ • Claim extract│  │   scoring      │  │                      ││
│   └────────┬───────┘  └────────┬───────┘  └──────────┬───────────┘│
│            │                   │                      │             │
│            ▼                   ▼                      ▼             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              Evidence Aggregator (Balance of Evidence)       │  │
│   │  • Google Fact Check Tools API                               │  │
│   │  • Brazilian fact-checkers (Lupa, Aos Fatos, Comprova)      │  │
│   │  • GDELT Project API                                         │  │
│   │  • Stance detection (XLM-RoBERTa + NLI)                    │  │
│   │  • Weighted credibility scoring                              │  │
│   └──────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                                   │
│                                                                     │
│   ┌────────────────┐  ┌────────────────┐  ┌──────────────────────┐│
│   │ PostgreSQL 16  │  │ Redis 7+       │  │ S3 / MinIO           ││
│   │ (Supabase)     │  │ • Sessions     │  │ • Media uploads      ││
│   │ • Users        │  │ • Cache        │  │ • Deepfake analysis  ││
│   │ • Conversations│  │ • Job queue    │  │ • Evidence snapshots ││
│   │ • Claims       │  │   (BullMQ)     │  │                      ││
│   │ • Evidence     │  │                │  │                      ││
│   │ • Learning     │  │                │  │                      ││
│   └────────────────┘  └────────────────┘  └──────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Repositório — Estrutura de Diretórios

```
fake-news-agent/
├── apps/
│   ├── bot/                          # Chatbot service (Python/FastAPI)
│   │   ├── src/
│   │   │   ├── main.py               # FastAPI app entry point
│   │   │   ├── webhooks/
│   │   │   │   ├── whatsapp.py        # WhatsApp Cloud API webhook handler
│   │   │   │   └── telegram.py        # Telegram Bot API webhook handler
│   │   │   ├── engine/
│   │   │   │   ├── fsm.py             # Finite State Machine (transitions lib)
│   │   │   │   ├── states.py          # All conversation states
│   │   │   │   ├── transitions.py     # State transition rules
│   │   │   │   └── flows/
│   │   │   │       ├── questioning.yaml  # Questioning flow definitions
│   │   │   │       └── responses.yaml    # Response templates (PT-BR)
│   │   │   ├── services/
│   │   │   │   ├── session.py         # Redis session management
│   │   │   │   ├── message_sender.py  # Platform-agnostic message sending
│   │   │   │   └── content_processor.py # Input content type detection
│   │   │   ├── analysis/
│   │   │   │   ├── text_analyzer.py   # NLP pipeline (BERTimbau)
│   │   │   │   ├── source_verifier.py # Domain/source credibility
│   │   │   │   ├── claim_extractor.py # Claim decomposition
│   │   │   │   └── fact_checker.py    # Fact-check API integration
│   │   │   └── config.py             # Environment config
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── web/                           # Web platform (Next.js 15)
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx         # Root layout with PWA config
│       │   │   ├── page.tsx           # Landing page
│       │   │   ├── analise/
│       │   │   │   └── [id]/page.tsx  # Content analysis page
│       │   │   ├── balanca/
│       │   │   │   └── [id]/page.tsx  # Balance of Evidence view
│       │   │   ├── guia-fontes/
│       │   │   │   └── page.tsx       # Source Analysis Guide
│       │   │   ├── radar/
│       │   │   │   └── page.tsx       # Trend Radar dashboard
│       │   │   ├── guia-acao/
│       │   │   │   └── page.tsx       # Criminal Content Action Guide
│       │   │   ├── aprender/
│       │   │   │   ├── page.tsx       # Learning modules hub
│       │   │   │   └── [module]/page.tsx  # Individual module
│       │   │   └── api/
│       │   │       ├── analyze/route.ts
│       │   │       ├── evidence/route.ts
│       │   │       └── feedback/route.ts
│       │   ├── components/
│       │   │   ├── evidence-balance.tsx   # Balança da Evidência visual
│       │   │   ├── source-card.tsx        # Evidence source card
│       │   │   ├── credibility-meter.tsx  # Source credibility gauge
│       │   │   ├── trend-alert.tsx        # Radar de Tendências alert
│       │   │   ├── quiz-module.tsx        # Interactive quiz component
│       │   │   └── decision-prompt.tsx    # Final user decision UI
│       │   ├── lib/
│       │   │   ├── api.ts             # API client
│       │   │   ├── storage.ts         # Dexie.js offline storage
│       │   │   └── analytics.ts       # Privacy-first analytics
│       │   └── i18n/
│       │       └── pt-BR.json         # Brazilian Portuguese strings
│       ├── public/
│       │   ├── manifest.json          # PWA manifest
│       │   └── sw.js                  # Service worker (Workbox)
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       └── package.json
│
├── packages/
│   ├── ml/                            # Machine Learning pipeline
│   │   ├── models/
│   │   │   ├── fake_news_classifier/  # Fine-tuned BERTimbau
│   │   │   ├── sentiment/             # pysentimiento wrapper
│   │   │   ├── propaganda/            # Propaganda technique detector
│   │   │   ├── stance/                # Stance detection (NLI)
│   │   │   └── deepfake/              # DeepfakeBench integration
│   │   ├── pipelines/
│   │   │   ├── text_pipeline.py       # Full text analysis pipeline
│   │   │   ├── evidence_pipeline.py   # Evidence gathering & scoring
│   │   │   └── media_pipeline.py      # Image/video analysis
│   │   └── training/
│   │       ├── fine_tune_bertimbau.py # Fake.BR corpus training
│   │       └── datasets/              # Training data management
│   │
│   └── shared/                        # Shared types and utilities
│       ├── types.py
│       └── constants.py
│
├── infra/                             # Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── ecs.tf                     # ECS Fargate services
│   │   ├── lambda.tf                  # Webhook Lambdas
│   │   ├── rds.tf                     # PostgreSQL
│   │   ├── elasticache.tf             # Redis
│   │   └── variables.tf
│   └── docker-compose.yml             # Local development
│
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Lint, test, security scan
│       └── deploy.yml                 # Staging → Production
│
└── docs/
    ├── ARCHITECTURE.md
    ├── LGPD_COMPLIANCE.md
    └── QUESTIONING_LOGIC.md
```

---

## SEÇÃO 2: BOT — MOTOR DE CONVERSAÇÃO

### 2.1 Finite State Machine — Estados e Transições

O coração do bot é uma FSM que gerencia a jornada de reflexão do usuário. Cada conversa é uma instância independente com estado persistido em Redis.

```yaml
# questioning.yaml — Definição completa do fluxo de questionamento

fsm:
  initial_state: AWAITING_CONTENT

  states:
    AWAITING_CONTENT:
      description: "Aguardando o usuário enviar conteúdo para análise"
      on_enter:
        message: null  # Silêncio — o usuário inicia

    GREETING:
      description: "Boas-vindas e primeira pergunta sobre motivação"
      on_enter:
        message: "Obrigada por compartilhar! 🙏 Para te ajudar a pensar um pouco mais sobre este conteúdo, tenho uma pergunta para você:"
        delay_ms: 1000
        follow_up:
          message: "Qual o seu principal motivo para querer compartilhar este conteúdo?"
          type: interactive_list
          options:
            - id: inform
              title: "Para informar as pessoas"
            - id: alert
              title: "Para alertar sobre algo importante"
            - id: opinion
              title: "Para expressar minha opinião"
            - id: identify
              title: "Me identifico com a mensagem"
            - id: seen_many
              title: "Vi em vários lugares"
            - id: other
              title: "Outro motivo"

    EXPLORING_MOTIVATION:
      description: "Aprofundando na motivação — adaptativo por resposta"
      branches:
        inform:
          message: "Que bom que você quer informar! Para que a informação seja a mais precisa e útil possível, você já pensou de onde ela veio e quem a produziu?"
          type: quick_reply
          options:
            - id: trust_source
              title: "Confio na fonte"
            - id: unknown_source
              title: "Não sei bem a fonte"
            - id: didnt_think
              title: "Não pensei nisso"

        alert:
          message: "É ótimo querer alertar! Que emoção essa notícia te provoca? Identificar o que sentimos ajuda a pensar com mais clareza."
          type: quick_reply
          options:
            - id: fear
              title: "Medo ou preocupação"
            - id: anger
              title: "Raiva ou indignação"
            - id: surprise
              title: "Surpresa ou choque"

        opinion:
          message: "Sua opinião é importante! Quando sentimos algo forte sobre um assunto, às vezes isso pode influenciar como vemos as informações. Você acha que essa notícia confirma algo que você já acreditava?"
          type: quick_reply
          options:
            - id: yes_confirms
              title: "Sim, confirma"
            - id: no_new
              title: "Não, é informação nova"
            - id: not_sure
              title: "Não tenho certeza"

        identify:
          message: "É natural nos conectarmos com mensagens que falam da nossa experiência. Você sabe quem criou esse conteúdo originalmente? Às vezes, mensagens são criadas para parecer que vêm da 'nossa gente' quando na verdade não vêm."
          type: quick_reply
          options:
            - id: know_origin
              title: "Sei quem criou"
            - id: forwarded
              title: "Foi encaminhada"
            - id: social_media
              title: "Vi em rede social"

        seen_many:
          message: "Quando vemos algo em muitos lugares, parece mais verdadeiro, não é? Mas a repetição nem sempre significa que é real. Você viu essa informação em fontes diferentes ou sempre nos mesmos tipos de grupos?"
          type: quick_reply
          options:
            - id: different_sources
              title: "Fontes diferentes"
            - id: same_groups
              title: "Mesmos tipos de grupo"
            - id: not_sure
              title: "Não reparei"

        other:
          message: "Entendo! Independente do motivo, é sempre bom refletir antes de compartilhar. Esse conteúdo menciona alguma fonte, autor ou organização que você pode verificar?"
          type: quick_reply
          options:
            - id: has_source
              title: "Sim, menciona"
            - id: no_source
              title: "Não menciona"
            - id: not_sure
              title: "Não sei dizer"

    DEEPENING_REFLECTION:
      description: "Segunda camada de perguntas baseada nas respostas anteriores"
      conditional_messages:
        trust_source:
          message: "Entendi. O que te faz confiar tanto nessa fonte? Ela costuma ser precisa? Já viu alguma correção ou desmentido dela antes?"
          type: quick_reply
          options:
            - id: always_right
              title: "Sempre é precisa"
            - id: sometimes_wrong
              title: "Às vezes erra"
            - id: never_checked
              title: "Nunca verifiquei"

        fear:
          message: "Quando sentimos medo, nosso cérebro quer agir rápido para proteger quem amamos. Isso é lindo, mas também pode nos levar a compartilhar sem verificar. Esse conteúdo pede que você aja com urgência?"
          type: quick_reply
          options:
            - id: yes_urgent
              title: "Sim, é urgente"
            - id: no_not_urgent
              title: "Não é urgente"
            - id: thinking
              title: "Estou pensando..."

        anger:
          message: "A indignação é um motor poderoso de mudança. Mas às vezes conteúdos são criados justamente para nos deixar com raiva e fazer a gente compartilhar sem pensar. Quem se beneficia se muitas pessoas ficarem com raiva por causa dessa mensagem?"
          type: quick_reply
          options:
            - id: community
              title: "A comunidade"
            - id: politicians
              title: "Políticos ou empresas"
            - id: dont_know
              title: "Não sei"

        yes_confirms:
          message: "Isso é o que chamamos de 'viés de confirmação' — tendemos a acreditar mais no que já pensamos. Não tem nada de errado nisso, é humano! Mas será que existe alguma informação diferente sobre esse assunto que você ainda não viu?"
          type: quick_reply
          options:
            - id: maybe
              title: "Talvez exista"
            - id: no_its_true
              title: "Tenho certeza que é verdade"
            - id: want_to_check
              title: "Quero verificar"

        forwarded:
          message: "Mensagens encaminhadas muitas vezes são alteradas no caminho. Cada pessoa que encaminha pode, sem querer, mudar o contexto. Quando algo é encaminhado muitas vezes, o WhatsApp mostra uma setinha dupla ↩️↩️. Você viu isso nessa mensagem?"
          type: quick_reply
          options:
            - id: yes_forwarded_many
              title: "Sim, muito encaminhada"
            - id: not_sure
              title: "Não reparei"
            - id: direct_from_someone
              title: "Recebi direto de alguém"

    CLOSING_REFLECTION:
      description: "Pergunta final de certeza — feita UMA única vez"
      on_enter:
        message: "Suas reflexões são muito valiosas! 💛 Agora, com base em tudo o que você pensou, você ainda quer compartilhar este conteúdo?"
        type: quick_reply
        options:
          - id: yes_share
            title: "Sim, quero compartilhar"
          - id: no_changed_mind
            title: "Não, mudei de ideia"
          - id: want_deeper
            title: "Quero investigar mais"

    EMPOWERMENT_FEEDBACK:
      description: "Reforço positivo independente da decisão"
      conditional_messages:
        yes_share:
          message: "Tudo bem! O importante é que você pensou sobre isso antes. Se quiser, nosso espaço de investigação na web tem ferramentas para analisar fontes e ver o que dizem outros veículos. Fica aqui o link caso precise: {web_platform_url}"
        no_changed_mind:
          message: "Sua capacidade de questionar e refletir é poderosa! 💪 Você acaba de proteger sua comunidade de uma possível informação incorreta. Continue usando essa habilidade!"
        want_deeper:
          message: "Que incrível! Sua vontade de investigar mostra maturidade e cuidado. Preparei um espaço especial de investigação para você. Lá, você vai encontrar ferramentas para analisar fontes, ver evidências a favor e contra, e muito mais:"
          follow_up:
            message: "👉 {web_platform_url}/analise/{content_id}\n\nO conteúdo que você enviou já está lá, pronto para ser investigado!"
            type: text

    CONVERSATION_END:
      description: "Fim da conversa com convite para futuro uso"
      on_enter:
        message: "Lembre-se: questionar não é desconfiar de tudo. É cuidar de si e de quem você ama. Sempre que receber algo que te faça duvidar, pode me enviar aqui. 🤗"

  transitions:
    - trigger: content_received
      source: AWAITING_CONTENT
      dest: GREETING
      conditions: [content_is_valid]

    - trigger: motivation_selected
      source: GREETING
      dest: EXPLORING_MOTIVATION

    - trigger: exploration_answered
      source: EXPLORING_MOTIVATION
      dest: DEEPENING_REFLECTION

    - trigger: reflection_answered
      source: DEEPENING_REFLECTION
      dest: CLOSING_REFLECTION

    - trigger: decision_made
      source: CLOSING_REFLECTION
      dest: EMPOWERMENT_FEEDBACK

    - trigger: feedback_delivered
      source: EMPOWERMENT_FEEDBACK
      dest: CONVERSATION_END

  rules:
    max_interactions_before_close: 4  # Máximo 4 trocas no bot
    timeout_minutes: 30               # Sessão expira em 30 min
    allow_restart: true                # Usuário pode enviar novo conteúdo a qualquer momento
    fallback_message: "Desculpe, não entendi. Pode escolher uma das opções acima? 😊"
```

### 2.2 Implementação do Bot — Código de Referência

```python
# src/engine/fsm.py — Motor de estados principal

from transitions import Machine
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import yaml

@dataclass
class ConversationContext:
    """Contexto completo de uma conversa — persistido em Redis como JSON."""
    user_id: str                          # Pseudonymized ID (NEVER phone number)
    platform: str                         # 'whatsapp' | 'telegram'
    content_type: str = ''                # 'text' | 'link' | 'image' | 'video' | 'audio'
    content_raw: str = ''                 # Original content submitted
    content_id: str = ''                  # UUID for web platform reference
    motivation: str = ''                  # User's stated motivation
    emotion: str = ''                     # Detected or stated emotion
    source_trust: str = ''               # User's trust in source
    reflection_answers: list = field(default_factory=list)
    final_decision: str = ''             # 'share' | 'not_share' | 'investigate'
    analysis_results: dict = field(default_factory=dict)
    started_at: str = ''
    last_interaction_at: str = ''
    interaction_count: int = 0

class QuestioningFSM:
    """Finite State Machine for the guided questioning flow."""

    states = [
        'awaiting_content',
        'greeting',
        'exploring_motivation',
        'deepening_reflection',
        'closing_reflection',
        'empowerment_feedback',
        'conversation_end'
    ]

    def __init__(self, context: ConversationContext):
        self.context = context
        self.machine = Machine(
            model=self,
            states=self.states,
            initial='awaiting_content',
            send_event=True,
            auto_transitions=False
        )
        # Define transitions
        self.machine.add_transition('receive_content', 'awaiting_content', 'greeting')
        self.machine.add_transition('select_motivation', 'greeting', 'exploring_motivation')
        self.machine.add_transition('answer_exploration', 'exploring_motivation', 'deepening_reflection')
        self.machine.add_transition('answer_reflection', 'deepening_reflection', 'closing_reflection')
        self.machine.add_transition('make_decision', 'closing_reflection', 'empowerment_feedback')
        self.machine.add_transition('deliver_feedback', 'empowerment_feedback', 'conversation_end')
        # Allow restart from any state
        self.machine.add_transition('restart', '*', 'awaiting_content')

    def get_response(self, user_input: str) -> dict:
        """Process user input and return the next message(s) to send."""
        self.context.interaction_count += 1
        self.context.last_interaction_at = datetime.utcnow().isoformat()

        # Route to appropriate handler based on current state
        handler = getattr(self, f'handle_{self.state}', self.handle_fallback)
        return handler(user_input)

    def handle_awaiting_content(self, content: str) -> dict:
        self.context.content_raw = content
        self.context.content_type = detect_content_type(content)
        self.context.content_id = generate_content_uuid()
        self.context.started_at = datetime.utcnow().isoformat()
        self.receive_content()

        # Trigger background analysis
        enqueue_analysis(self.context.content_id, content, self.context.content_type)

        return {
            'messages': [
                {
                    'type': 'text',
                    'body': 'Obrigada por compartilhar! 🙏 Para te ajudar a pensar um pouco mais sobre este conteúdo, tenho uma pergunta para você:'
                },
                {
                    'type': 'interactive_list',
                    'body': 'Qual o seu principal motivo para querer compartilhar este conteúdo?',
                    'button_text': 'Escolher motivo',
                    'sections': [{
                        'title': 'Motivos',
                        'rows': [
                            {'id': 'inform', 'title': 'Para informar as pessoas'},
                            {'id': 'alert', 'title': 'Para alertar sobre algo importante'},
                            {'id': 'opinion', 'title': 'Para expressar minha opinião'},
                            {'id': 'identify', 'title': 'Me identifico com a mensagem'},
                            {'id': 'seen_many', 'title': 'Vi em vários lugares'},
                            {'id': 'other', 'title': 'Outro motivo'}
                        ]
                    }]
                }
            ]
        }

    # ... (handlers for each state follow the same pattern)
```

### 2.3 WhatsApp Cloud API — Integração Específica

```python
# src/webhooks/whatsapp.py

from fastapi import APIRouter, Request, HTTPException
import hmac, hashlib, json, httpx

router = APIRouter(prefix="/webhook/whatsapp")

VERIFY_TOKEN = config.WHATSAPP_VERIFY_TOKEN
APP_SECRET = config.WHATSAPP_APP_SECRET
PHONE_NUMBER_ID = config.WHATSAPP_PHONE_NUMBER_ID
ACCESS_TOKEN = config.WHATSAPP_ACCESS_TOKEN
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

@router.get("")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification (GET)."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("")
async def receive_message(request: Request):
    """WhatsApp incoming message handler (POST)."""
    # 1. Verify HMAC-SHA256 signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse the webhook payload
    data = json.loads(body)
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                await process_whatsapp_message(message, value.get("contacts", []))

    return {"status": "ok"}

async def process_whatsapp_message(message: dict, contacts: list):
    """Route incoming WhatsApp message to FSM engine."""
    wa_id = message["from"]  # Phone number
    user_id = pseudonymize(wa_id)  # NEVER store raw phone number

    msg_type = message["type"]
    content = extract_content(message, msg_type)

    # Load or create session
    session = await session_manager.get_or_create(user_id, platform="whatsapp")
    fsm = QuestioningFSM(session.context)
    if session.state:
        fsm.machine.set_state(session.state)

    # Get response from FSM
    response = fsm.get_response(content)

    # Send response messages
    for msg in response["messages"]:
        await send_whatsapp_message(wa_id, msg)

    # Persist session
    await session_manager.save(user_id, fsm.state, fsm.context)

async def send_whatsapp_message(to: str, msg: dict):
    """Send a message via WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    if msg["type"] == "text":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": msg["body"]}
        }
    elif msg["type"] == "interactive_list":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": msg["body"]},
                "action": {
                    "button": msg["button_text"],
                    "sections": msg["sections"]
                }
            }
        }
    elif msg["type"] == "quick_reply":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": msg["body"]},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": opt["id"], "title": opt["title"]}}
                        for opt in msg["options"][:3]  # WhatsApp max 3 buttons
                    ]
                }
            }
        }

    async with httpx.AsyncClient() as client:
        resp = await client.post(API_URL, headers=headers, json=payload)
        resp.raise_for_status()
```

### 2.4 Telegram Bot API — Integração Específica

```python
# src/webhooks/telegram.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)

async def start(update: Update, context):
    """Handle /start command."""
    await update.message.reply_text(
        "Olá! 👋 Sou o seu mentor digital contra desinformação.\n\n"
        "Me envie qualquer conteúdo (texto, link, foto ou vídeo) "
        "que você recebeu e gostaria de pensar melhor antes de compartilhar."
    )

async def handle_content(update: Update, context):
    """Handle any content sent by the user."""
    user_id = pseudonymize(str(update.effective_user.id))
    content = update.message.text or update.message.caption or ""

    session = await session_manager.get_or_create(user_id, platform="telegram")
    fsm = QuestioningFSM(session.context)
    response = fsm.get_response(content)

    for msg in response["messages"]:
        if msg["type"] == "text":
            await update.message.reply_text(msg["body"])
        elif msg["type"] in ("interactive_list", "quick_reply"):
            keyboard = [
                [InlineKeyboardButton(opt["title"], callback_data=opt["id"])]
                for opt in msg.get("options", msg.get("sections", [{}])[0].get("rows", []))
            ]
            await update.message.reply_text(
                msg["body"],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    await session_manager.save(user_id, fsm.state, fsm.context)
```

---

## SEÇÃO 3: PIPELINE DE ANÁLISE NLP

### 3.1 Modelos e Suas Funções Específicas

```python
# packages/ml/pipelines/text_pipeline.py

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from pysentimiento import create_analyzer
import spacy

class TextAnalysisPipeline:
    """Pipeline completo de análise de texto para português brasileiro."""

    def __init__(self):
        # 1. Fake News Classifier — BERTimbau fine-tuned on Fake.BR
        self.fake_news_tokenizer = AutoTokenizer.from_pretrained(
            "neuralmind/bert-base-portuguese-cased"
        )
        self.fake_news_model = AutoModelForSequenceClassification.from_pretrained(
            "./models/fake_news_classifier"  # Fine-tuned locally
        )

        # 2. Sentiment Analyzer — pysentimiento (ready-to-use for PT-BR)
        self.sentiment_analyzer = create_analyzer(
            task="sentiment", lang="pt"
        )
        # Returns: SentimentOutput(output='POS'|'NEG'|'NEU', probas={...})

        # 3. Emotion Detector — pysentimiento
        self.emotion_analyzer = create_analyzer(
            task="emotion", lang="pt"
        )
        # Returns: joy, sadness, anger, surprise, disgust, fear, others

        # 4. Hate Speech Detector — pysentimiento
        self.hate_speech_analyzer = create_analyzer(
            task="hate_speech", lang="pt"
        )

        # 5. Named Entity Recognition — spaCy PT model
        self.nlp = spacy.load("pt_core_news_lg")

        # 6. Propaganda Technique Detector (multilingual)
        self.propaganda_detector = pipeline(
            "text-classification",
            model="xlm-roberta-large",  # Fine-tuned on SemEval 2020 Task 11
            tokenizer="xlm-roberta-large"
        )

    async def analyze(self, text: str) -> dict:
        """Run full analysis pipeline on input text."""
        results = {}

        # Extract claims and entities
        doc = self.nlp(text)
        results["entities"] = [
            {"text": ent.text, "label": ent.label_}
            for ent in doc.ents
        ]
        results["claims"] = extract_checkable_claims(doc)

        # Sentiment and emotion
        sentiment = self.sentiment_analyzer.predict(text)
        results["sentiment"] = {
            "label": sentiment.output,
            "scores": sentiment.probas
        }

        emotion = self.emotion_analyzer.predict(text)
        results["emotion"] = {
            "label": emotion.output,
            "scores": emotion.probas
        }

        # Hate speech check
        hate = self.hate_speech_analyzer.predict(text)
        results["hate_speech"] = {
            "is_hateful": hate.output == "hateful",
            "scores": hate.probas
        }

        # Fake news probability
        results["fake_news_score"] = await self.classify_fake_news(text)

        # Manipulation indicators
        results["manipulation_indicators"] = detect_manipulation_patterns(text)

        return results

    def detect_manipulation_patterns(self, text: str) -> list:
        """Rule-based detection of common manipulation tactics in PT-BR."""
        indicators = []

        patterns = {
            "urgency": [
                r"compartilhe antes que",
                r"apaguem isso",
                r"urgente",
                r"não deixe de",
                r"repasse para todo mundo"
            ],
            "false_authority": [
                r"médico(?:a)?s? (?:afirmam|dizem|confirmam)",
                r"segundo especialistas",
                r"(?:estudos|pesquisas) (?:comprovam|mostram)",
                # Without actual citation
            ],
            "emotional_appeal": [
                r"[A-Z]{5,}",          # ALL CAPS words
                r"!{2,}",              # Multiple exclamation marks
                r"🚨|⚠️|❗|‼️",        # Alert emojis
            ],
            "conspiracy_markers": [
                r"(?:a mídia|eles) não (?:querem|vão) (?:mostrar|divulgar)",
                r"o que não (?:te contam|querem que você saiba)",
                r"verdade que (?:escondem|ninguém fala)"
            ]
        }

        for category, regex_list in patterns.items():
            for pattern in regex_list:
                if re.search(pattern, text, re.IGNORECASE):
                    indicators.append({
                        "type": category,
                        "pattern": pattern,
                        "explanation": INDICATOR_EXPLANATIONS[category]
                    })

        return indicators
```

### 3.2 Balança da Evidência — Pipeline Completo

```python
# packages/ml/pipelines/evidence_pipeline.py

import httpx
from dataclasses import dataclass

@dataclass
class EvidenceItem:
    source_name: str
    source_url: str
    source_domain: str
    credibility_score: float  # 0.0 to 1.0
    stance: str               # 'supports' | 'contradicts' | 'neutral'
    stance_confidence: float  # 0.0 to 1.0
    excerpt: str
    published_date: str
    is_fact_checker: bool

class EvidencePipeline:
    """Gathers and scores evidence for the Balance of Evidence feature."""

    async def gather_evidence(self, claims: list[str], original_text: str) -> dict:
        """Full evidence gathering pipeline."""

        all_evidence = []

        # 1. Query Google Fact Check Tools API (FREE, no key needed for basic use)
        for claim in claims:
            fact_checks = await self.query_google_factcheck(claim)
            all_evidence.extend(fact_checks)

        # 2. Query Brazilian fact-checker databases
        for claim in claims:
            br_checks = await self.query_brazilian_factcheckers(claim)
            all_evidence.extend(br_checks)

        # 3. Query GDELT for news coverage
        gdelt_results = await self.query_gdelt(claims, original_text)
        all_evidence.extend(gdelt_results)

        # 4. Score source credibility
        for evidence in all_evidence:
            evidence.credibility_score = await self.score_source_credibility(
                evidence.source_domain
            )

        # 5. Detect stance (supports/contradicts/neutral)
        for evidence in all_evidence:
            evidence.stance, evidence.stance_confidence = await self.detect_stance(
                original_text, evidence.excerpt
            )

        # 6. Compute balance score
        balance = self.compute_balance(all_evidence)

        return {
            "balance_score": balance,  # -1.0 (all contradict) to +1.0 (all support)
            "supporting": [e for e in all_evidence if e.stance == "supports"],
            "contradicting": [e for e in all_evidence if e.stance == "contradicts"],
            "neutral": [e for e in all_evidence if e.stance == "neutral"],
            "total_sources": len(all_evidence),
            "fact_checker_verdict": self.get_fact_checker_verdict(all_evidence)
        }

    async def query_google_factcheck(self, claim: str) -> list[EvidenceItem]:
        """Query Google Fact Check Tools API."""
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim,
            "languageCode": "pt",
            "key": config.GOOGLE_API_KEY  # Free, no per-query charge
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        results = []
        for item in data.get("claims", []):
            for review in item.get("claimReview", []):
                results.append(EvidenceItem(
                    source_name=review.get("publisher", {}).get("name", ""),
                    source_url=review.get("url", ""),
                    source_domain=extract_domain(review.get("url", "")),
                    credibility_score=0.0,  # Scored later
                    stance=map_factcheck_rating_to_stance(review.get("textualRating", "")),
                    stance_confidence=0.9,  # High confidence for fact-checkers
                    excerpt=review.get("title", ""),
                    published_date=review.get("reviewDate", ""),
                    is_fact_checker=True
                ))
        return results

    async def query_brazilian_factcheckers(self, claim: str) -> list[EvidenceItem]:
        """Query Brazilian fact-checking organizations."""
        sources = [
            {"name": "Agência Lupa", "rss": "https://lupa.uol.com.br/feed"},
            {"name": "Aos Fatos", "rss": "https://aosfatos.org/rss"},
            {"name": "Fato ou Fake", "base": "https://g1.globo.com/fato-ou-fake/"},
        ]
        # Search via RSS feeds + PostgreSQL cache of previously indexed articles
        results = await self.search_local_factcheck_db(claim)
        return results

    def compute_balance(self, evidence: list[EvidenceItem]) -> float:
        """
        Compute weighted balance score.
        Formula: Σ(stance_value × stance_confidence × credibility) / Σ(credibility)
        Where stance_value: supports=+1, contradicts=-1, neutral=0
        """
        if not evidence:
            return 0.0

        stance_map = {"supports": 1.0, "contradicts": -1.0, "neutral": 0.0}
        numerator = sum(
            stance_map[e.stance] * e.stance_confidence * e.credibility_score
            for e in evidence
        )
        denominator = sum(e.credibility_score for e in evidence)

        if denominator == 0:
            return 0.0
        return max(-1.0, min(1.0, numerator / denominator))
```

---

## SEÇÃO 4: BANCO DE DADOS — SCHEMA POSTGRESQL

```sql
-- Schema PostgreSQL completo para o Fake News Reporting Agent
-- Projetado para LGPD compliance, performance e flexibilidade

-- ============================================================
-- EXTENSÕES NECESSÁRIAS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Fuzzy text matching

-- ============================================================
-- TABELA: users (DADOS ANONIMIZADOS)
-- LGPD: Nunca armazenar telefone, nome, ou dados identificáveis
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pseudonymous_id VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 do phone/user_id
    platform VARCHAR(20) NOT NULL,                 -- 'whatsapp' | 'telegram' | 'web'
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    total_interactions INTEGER DEFAULT 0,
    preferred_language VARCHAR(5) DEFAULT 'pt-BR',
    consent_given_at TIMESTAMPTZ,                  -- LGPD: registro de consentimento
    consent_version VARCHAR(10),
    deleted_at TIMESTAMPTZ                         -- Soft delete para LGPD right to erasure
);

-- ============================================================
-- TABELA: conversations
-- ============================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    final_decision VARCHAR(20),  -- 'share' | 'not_share' | 'investigate' | 'abandoned'
    interaction_count INTEGER DEFAULT 0,
    transitioned_to_web BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb  -- FSM state history, timing data
);

-- ============================================================
-- TABELA: submissions (conteúdo enviado pelo usuário)
-- ============================================================
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL,  -- 'text' | 'link' | 'image' | 'video' | 'audio'
    content_text TEXT,                   -- Texto ou URL
    content_hash VARCHAR(64),            -- SHA-256 do conteúdo (deduplicação)
    media_storage_key VARCHAR(255),      -- S3/MinIO key para mídia
    analysis_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_submissions_content_hash ON submissions(content_hash);

-- ============================================================
-- TABELA: claims (afirmações extraídas para verificação)
-- ============================================================
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    normalized_text TEXT,
    search_vector TSVECTOR,  -- Full-text search em português
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_search ON claims USING GIN(search_vector);
CREATE INDEX idx_claims_trgm ON claims USING GIN(normalized_text gin_trgm_ops);

-- ============================================================
-- TABELA: sources (repositório de fontes conhecidas)
-- ============================================================
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    is_fact_checker BOOLEAN DEFAULT FALSE,
    credibility_score DECIMAL(3,2) DEFAULT 0.50,  -- 0.00 to 1.00
    domain_age_days INTEGER,
    has_ssl BOOLEAN,
    whois_data JSONB,
    last_evaluated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: evidence (evidências coletadas para cada claim)
-- ============================================================
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    source_id UUID REFERENCES sources(id),
    source_url TEXT NOT NULL,
    excerpt TEXT,
    stance VARCHAR(20) NOT NULL,           -- 'supports' | 'contradicts' | 'neutral'
    stance_confidence DECIMAL(3,2),
    fact_check_rating VARCHAR(100),        -- Rating original do fact-checker
    published_date TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb     -- ML scores, additional signals
);

-- ============================================================
-- TABELA: analysis_results (resultados ML consolidados)
-- ============================================================
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    fake_news_score DECIMAL(3,2),          -- 0.00 (real) to 1.00 (fake)
    sentiment JSONB,                        -- {label, scores}
    emotion JSONB,                          -- {label, scores}
    hate_speech JSONB,                      -- {is_hateful, scores}
    manipulation_indicators JSONB,          -- [{type, pattern, explanation}]
    balance_score DECIMAL(3,2),            -- -1.00 to +1.00
    deepfake_score DECIMAL(3,2),           -- 0.00 to 1.00 (for media)
    entities JSONB,                         -- [{text, label}]
    processing_time_ms INTEGER,
    model_versions JSONB,                   -- Track which models were used
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: learning_modules
-- ============================================================
CREATE TABLE learning_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    title_pt VARCHAR(255) NOT NULL,
    description_pt TEXT,
    content JSONB NOT NULL,  -- Structured content: sections, quizzes, examples
    difficulty VARCHAR(20),   -- 'beginner' | 'intermediate' | 'advanced'
    estimated_minutes INTEGER,
    topic VARCHAR(50),        -- 'bias' | 'sources' | 'deepfakes' | 'algorithms' | 'rights'
    order_index INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: user_learning_progress
-- ============================================================
CREATE TABLE user_learning_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    module_id UUID REFERENCES learning_modules(id),
    status VARCHAR(20) DEFAULT 'not_started',  -- 'not_started' | 'in_progress' | 'completed'
    score DECIMAL(5,2),
    quiz_answers JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(user_id, module_id)
);

-- ============================================================
-- TABELA: trend_alerts (Radar de Tendências)
-- ============================================================
CREATE TABLE trend_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title_pt VARCHAR(255) NOT NULL,
    description_pt TEXT,
    affected_communities JSONB,        -- ['mulheres_negras', 'lgbtqia', etc.]
    threat_level VARCHAR(20),          -- 'low' | 'medium' | 'high' | 'critical'
    related_claims UUID[],
    source_data JSONB,                 -- GDELT, social media data
    is_active BOOLEAN DEFAULT TRUE,
    first_detected_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: feedback (dados de impacto, anonimizados)
-- ============================================================
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    feeling_after VARCHAR(50),       -- 'empowered' | 'confused' | 'grateful' | 'frustrated'
    usefulness_rating INTEGER,       -- 1-5
    would_recommend BOOLEAN,
    free_text TEXT,                   -- Optional open feedback
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- VIEWS para Analytics (anonimizadas)
-- ============================================================
CREATE VIEW v_impact_metrics AS
SELECT
    DATE_TRUNC('week', c.started_at) AS week,
    COUNT(DISTINCT c.id) AS total_conversations,
    COUNT(DISTINCT c.user_id) AS unique_users,
    ROUND(AVG(c.interaction_count), 1) AS avg_interactions,
    COUNT(CASE WHEN c.final_decision = 'not_share' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(CASE WHEN c.final_decision IS NOT NULL THEN 1 END), 0) AS not_share_rate,
    COUNT(CASE WHEN c.transitioned_to_web THEN 1 END)::DECIMAL /
        NULLIF(COUNT(*), 0) AS web_transition_rate
FROM conversations c
WHERE c.ended_at IS NOT NULL
GROUP BY DATE_TRUNC('week', c.started_at)
ORDER BY week DESC;
```

---

## SEÇÃO 5: PLATAFORMA WEB — COMPONENTES PRINCIPAIS

### 5.1 Balança da Evidência — Componente React

```tsx
// components/evidence-balance.tsx
// O componente mais importante da plataforma web

"use client";
import { useState } from "react";

interface EvidenceItem {
  source_name: string;
  source_url: string;
  credibility_score: number;
  stance: "supports" | "contradicts" | "neutral";
  stance_confidence: number;
  excerpt: string;
  published_date: string;
  is_fact_checker: boolean;
}

interface BalanceData {
  balance_score: number;     // -1.0 to +1.0
  supporting: EvidenceItem[];
  contradicting: EvidenceItem[];
  neutral: EvidenceItem[];
  fact_checker_verdict: string | null;
}

export function EvidenceBalance({ data }: { data: BalanceData }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  // Map balance score to visual position and label
  const position = ((data.balance_score + 1) / 2) * 100; // 0-100%
  const getLabel = (score: number) => {
    if (score < -0.6) return "A maioria das fontes contradiz";
    if (score < -0.2) return "Mais fontes contradizem do que confirmam";
    if (score < 0.2) return "Evidências divididas";
    if (score < 0.6) return "Mais fontes confirmam do que contradizem";
    return "A maioria das fontes confirma";
  };

  return (
    <div className="space-y-6" role="region" aria-label="Balança da Evidência">
      {/* Guiding question — NOT a verdict */}
      <p className="text-lg font-medium text-center text-gray-800">
        Ao observar essas evidências, o que VOCÊ conclui?
      </p>

      {/* Visual balance bar */}
      <div className="relative h-8 bg-gradient-to-r from-red-200 via-yellow-100 to-green-200 rounded-full overflow-hidden">
        <div
          className="absolute top-0 w-4 h-8 bg-gray-800 rounded-full transform -translate-x-1/2 transition-all duration-700"
          style={{ left: `${position}%` }}
          aria-label={`Indicador de equilíbrio: ${getLabel(data.balance_score)}`}
        />
      </div>
      <p className="text-center text-sm text-gray-600 font-medium">
        {getLabel(data.balance_score)}
      </p>

      {/* Fact-checker verdict if available */}
      {data.fact_checker_verdict && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-medium text-blue-800">
            🔍 Agências de verificação de fatos dizem:
          </p>
          <p className="text-blue-700 mt-1">{data.fact_checker_verdict}</p>
        </div>
      )}

      {/* Two columns: Supporting vs Contradicting */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Contradicting sources */}
        <div>
          <h3 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
            <span className="w-3 h-3 bg-red-500 rounded-full" />
            Fontes que questionam ({data.contradicting.length})
          </h3>
          {data.contradicting.map((item, i) => (
            <SourceCard key={i} item={item} variant="contradicts" />
          ))}
        </div>

        {/* Supporting sources */}
        <div>
          <h3 className="font-semibold text-green-700 mb-2 flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full" />
            Fontes que confirmam ({data.supporting.length})
          </h3>
          {data.supporting.map((item, i) => (
            <SourceCard key={i} item={item} variant="supports" />
          ))}
        </div>
      </div>

      {/* Call to action — empowerment, not verdict */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
        <p className="text-amber-800 font-medium">
          💡 Lembre-se: quanto mais fontes diferentes você consultar,
          mais segura será sua conclusão.
        </p>
        <button className="mt-2 text-sm text-amber-700 underline">
          Aprenda a analisar fontes com nosso guia →
        </button>
      </div>
    </div>
  );
}
```

### 5.2 PWA Configuration

```json
// public/manifest.json
{
  "name": "Mentor Digital — Verificação de Informação",
  "short_name": "Mentor Digital",
  "description": "Seu mentor contra desinformação. Questione, investigue, decida.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFF8F0",
  "theme_color": "#D97706",
  "lang": "pt-BR",
  "dir": "ltr",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "categories": ["education", "news"],
  "screenshots": [
    { "src": "/screenshots/balance.png", "sizes": "375x812", "type": "image/png", "form_factor": "narrow" }
  ]
}
```

---

## SEÇÃO 6: SEGURANÇA E LGPD

### 6.1 Checklist de Compliance LGPD

```yaml
lgpd_compliance:
  legal_basis:
    fact_checking_core: "legitimate_interest"  # Art. 10 — verificação de fatos
    optional_learning: "consent"                # Art. 7, I — módulos educativos
    analytics: "legitimate_interest"            # Art. 10 — anonimizado
    trend_alerts: "consent"                     # Art. 7, I — notificações

  data_subject_rights:  # Art. 18 — prazo: 15 dias
    - confirmation_of_processing     # 18.I
    - access_to_data                 # 18.II
    - correction                     # 18.III
    - anonymization_or_deletion      # 18.IV
    - data_portability               # 18.V
    - deletion_of_unnecessary        # 18.VI
    - information_about_sharing      # 18.VII
    - revocation_of_consent          # 18.VIII
    - opposition_to_processing       # 18.IX

  sensitive_data:  # Art. 11
    - racial_ethnic_origin: "NEVER stored, NEVER inferred from content"
    - religious_belief: "NEVER stored"
    - political_opinion: "NEVER stored"

  data_minimization:
    phone_numbers: "NEVER stored — only pseudonymous hash"
    names: "NEVER stored"
    location: "NEVER stored"
    ip_addresses: "Stripped at gateway level"
    message_content: "Stored only during analysis, purged after 30 days"
    media_files: "Purged after analysis (max 72 hours)"

  anonymization_techniques:
    identity_activity_separation: true  # Different stores for ID vs behavior
    k_anonymity: "k >= 10"
    differential_privacy: "epsilon >= 1.0 for published analytics"
    timestamp_noise: "+/- 30 minutes for stored timestamps"
    community_suppression: "Groups < 50 users not reported in analytics"

  encryption:
    at_rest: "AES-256-GCM via AWS KMS"
    in_transit: "TLS 1.3 only, HSTS enabled"
    database_fields: "pgcrypto for sensitive columns"
    backups: "Encrypted with separate key"

  breach_notification:
    anpd_deadline: "3 business days"
    user_notification: "Immediate if high risk"
    incident_log_retention: "5 years minimum"
```

### 6.2 Pseudonymization Implementation

```python
# Função de pseudonimização — NUNCA armazenar dados identificáveis

import hashlib
import os

PEPPER = os.environ["PSEUDONYMIZATION_PEPPER"]  # Rotated annually

def pseudonymize(identifier: str) -> str:
    """
    Convert phone number or user ID to irreversible pseudonym.
    Uses SHA-256 with pepper — one-way, consistent across sessions.
    """
    salted = f"{PEPPER}:{identifier}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()

def pseudonymize_for_analytics(identifier: str) -> str:
    """
    Separate pseudonym for analytics — prevents cross-referencing
    between operational and analytical databases.
    """
    analytics_pepper = os.environ["ANALYTICS_PEPPER"]
    salted = f"{analytics_pepper}:{identifier}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()
```

---

## SEÇÃO 7: INFRAESTRUTURA E CUSTOS

### 7.1 Custos Estimados por Fase

```
┌─────────────────────────────────────────────────────────────┐
│                    ESTIMATIVA DE CUSTOS                      │
├──────────────┬──────────────┬───────────────┬───────────────┤
│ Componente   │ MVP (100u)   │ Growth (1Ku)  │ Scale (10Ku)  │
├──────────────┼──────────────┼───────────────┼───────────────┤
│ WhatsApp API │ $0 (service) │ $0 (service)  │ $0 (service)  │
│ Telegram API │ $0           │ $0            │ $0            │
│ Compute      │ $0 (Lambda)  │ $35 (Fargate) │ $200 (Fargate)│
│ PostgreSQL   │ $0 (Supabase)│ $25 (RDS)     │ $100 (RDS)    │
│ Redis        │ $0 (local)   │ $15 (Elasti)  │ $50 (Elasti)  │
│ S3 Storage   │ $0 (free)    │ $5            │ $30           │
│ CDN/Hosting  │ $0 (Vercel)  │ $0 (Vercel)   │ $20 (CF Pro)  │
│ ML Inference │ $0 (CPU)     │ $50 (RunPod)  │ $200 (RunPod) │
│ Monitoring   │ $0           │ $0            │ $0            │
│ Domain + SSL │ $12/yr       │ $12/yr        │ $12/yr        │
├──────────────┼──────────────┼───────────────┼───────────────┤
│ TOTAL/MÊS    │ ~$1          │ ~$130         │ ~$600         │
└──────────────┴──────────────┴───────────────┴───────────────┘

Nota: AWS Activate Founders ($1,000 créditos) cobre 8-12 meses de MVP+Growth.
```

---

## SEÇÃO 8: MÓDULOS DE APRENDIZAGEM

### 8.1 Conteúdo dos Módulos (estrutura JSON para cada módulo)

```json
{
  "modules": [
    {
      "slug": "vies-de-confirmacao",
      "title": "Por que acreditamos no que já pensamos?",
      "topic": "bias",
      "difficulty": "beginner",
      "estimated_minutes": 5,
      "sections": [
        {
          "type": "explanation",
          "content": "Nosso cérebro tem um atalho: ele prefere informações que confirmam o que já acreditamos. Isso se chama viés de confirmação. Não é falta de inteligência — é como o cérebro funciona para economizar energia."
        },
        {
          "type": "example",
          "scenario": "Imagine que você acredita que um certo alimento faz mal. Quando vê uma notícia dizendo que faz mal, você pensa 'eu sabia!'. Mas quando vê uma pesquisa dizendo que é seguro, você pensa 'deve ser propaganda'. Nos dois casos, o viés está agindo.",
          "question": "Você já sentiu isso com algum tema?",
          "reflection": true
        },
        {
          "type": "quiz",
          "question": "O viés de confirmação acontece porque:",
          "options": [
            {"text": "Somos ignorantes", "correct": false, "feedback": "Não! Acontece com todas as pessoas, independente de educação."},
            {"text": "Nosso cérebro busca atalhos", "correct": true, "feedback": "Isso! É um mecanismo natural do cérebro. Reconhecer isso é o primeiro passo."},
            {"text": "As redes sociais nos manipulam", "correct": false, "feedback": "As redes amplificam o viés, mas ele existe naturalmente em nós."}
          ]
        },
        {
          "type": "practical_tip",
          "tip": "Quando uma notícia confirmar exatamente o que você já pensa, isso é um sinal para investigar MAIS, não menos. Tente buscar uma fonte que diga o contrário e compare."
        }
      ]
    },
    {
      "slug": "como-avaliar-fontes",
      "title": "Essa fonte é confiável?",
      "topic": "sources",
      "difficulty": "beginner",
      "estimated_minutes": 7
    },
    {
      "slug": "deepfakes-como-identificar",
      "title": "Quando o vídeo mente: deepfakes",
      "topic": "deepfakes",
      "difficulty": "intermediate",
      "estimated_minutes": 8
    },
    {
      "slug": "algoritmos-e-bolhas",
      "title": "Por que você só vê o que já gosta?",
      "topic": "algorithms",
      "difficulty": "intermediate",
      "estimated_minutes": 6
    },
    {
      "slug": "seus-direitos-digitais",
      "title": "Conteúdo criminoso: como denunciar e se proteger",
      "topic": "rights",
      "difficulty": "beginner",
      "estimated_minutes": 10
    }
  ]
}
```

---

## SEÇÃO 9: RADAR DE TENDÊNCIAS

### 9.1 Pipeline de Monitoramento

```python
# Executado a cada 6 horas via cron / EventBridge

class TrendRadarPipeline:
    """Monitors for disinformation trends targeting minority communities."""

    MONITORED_TOPICS = [
        "saúde mulher negra", "vacina periferia", "violência policial",
        "religião afro", "cotas raciais", "feminismo negro",
        "lgbtqia direitos", "indígena terra", "imigrante refugiado"
    ]

    DISINFORMATION_SIGNALS = [
        "coordinated_sharing",     # Muitos compartilhamentos em curto período
        "bot_like_patterns",       # Contas novas, sem foto, nomes genéricos
        "cross_platform_spread",   # Mesmo conteúdo em múltiplas plataformas
        "emotional_manipulation",  # Alto score de manipulação emocional
        "source_unreliable",       # Fontes com baixo credibility_score
        "fact_checked_false"       # Já verificado como falso por fact-checkers
    ]

    async def scan(self):
        """Full trend scan cycle."""
        for topic in self.MONITORED_TOPICS:
            # 1. Query GDELT for recent coverage
            gdelt_data = await self.query_gdelt_trends(topic)

            # 2. Query YouTube for related videos
            youtube_data = await self.query_youtube_trends(topic)

            # 3. Analyze for disinformation signals
            signals = await self.detect_signals(gdelt_data + youtube_data)

            # 4. If signals detected, create or update alert
            if signals:
                await self.create_or_update_alert(topic, signals)

    async def query_gdelt_trends(self, topic: str) -> list:
        """Query GDELT DOC 2.0 API for recent articles."""
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": f'"{topic}" sourcelang:por',
            "mode": "ArtList",
            "maxrecords": 50,
            "timespan": "6h",
            "format": "json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            return resp.json().get("articles", [])
```

---

## SEÇÃO 10: MÉTRICAS DE IMPACTO

### 10.1 KPIs Primários (medidos automaticamente)

```yaml
product_kpis:
  bot:
    flow_completion_rate: "% de usuários que completam o fluxo de perguntas"
    target: ">70%"
    query: "SELECT COUNT(CASE WHEN final_decision IS NOT NULL THEN 1 END)::float / COUNT(*) FROM conversations"

    not_share_rate: "% que decidem NÃO compartilhar após reflexão"
    target: ">30%"
    query: "SELECT COUNT(CASE WHEN final_decision = 'not_share' THEN 1 END)::float / COUNT(CASE WHEN final_decision IS NOT NULL THEN 1 END) FROM conversations"

    web_transition_rate: "% que escolhem aprofundar na web"
    target: ">20%"
    query: "SELECT COUNT(CASE WHEN transitioned_to_web THEN 1 END)::float / COUNT(*) FROM conversations"

  web:
    balance_interaction_rate: "% que clicam em fontes na Balança"
    time_on_analysis: "Tempo médio na página de análise"
    module_completion_rate: "% que completam módulos de aprendizagem"
    return_user_rate: "% de usuários que voltam em 7 dias"

  impact:
    empowerment_score: "Média de 'feeling_after' = 'empowered' no feedback"
    target: ">60%"
    recommendation_rate: "% que recomendariam a ferramenta"
    target: ">80%"
```

---

## SEÇÃO 11: INSTRUÇÕES FINAIS PARA O LLM AGENTE

### 11.1 Prioridades de Implementação
1. **PRIMEIRO**: Bot WhatsApp com fluxo completo de questionamento (sem ML, apenas FSM + regras).
2. **SEGUNDO**: Plataforma Web PWA com Balança da Evidência usando Google Fact Check API.
3. **TERCEIRO**: Integração NLP (BERTimbau, sentiment, manipulation detection).
4. **QUARTO**: Módulos de aprendizagem e Radar de Tendências.
5. **QUINTO**: Detecção de deepfakes e análise de vieses algorítmicos.

### 11.2 Regras de Geração de Código
- Todo código em **Python 3.11+** (bot) e **TypeScript** (web).
- Todo texto voltado ao usuário em **português brasileiro** informal-acolhedor.
- Todo componente React com **acessibilidade WCAG 2.2 AA** (aria-labels, keyboard nav, touch targets 24px+).
- Todo endpoint com **rate limiting**, **input validation**, e **HMAC verification**.
- Todo dado de usuário **pseudonimizado** antes de armazenar.
- **ZERO** dependência de serviços pagos no MVP — usar apenas free tiers.
- Cada mensagem do bot deve ter **no máximo 300 caracteres** (WhatsApp readability).
- **NUNCA** usar a palavra "falso" ou "fake" nas mensagens ao usuário. Usar "questionar", "investigar", "refletir".

### 11.3 Tom de Voz do Agente
- Falar como uma **amiga mais velha sábia**, não como um professor ou autoridade.
- Usar **"você"** (nunca "tu" ou "senhor/senhora").
- Emojis com moderação: máximo 1-2 por mensagem, nunca no meio de frases importantes.
- **Nunca** soar condescendente, paternalista ou acusatório.
- **Sempre** validar o sentimento do usuário antes de desafiar a crença.
- **Sempre** dar ao usuário a sensação de que ELE está no controle da decisão.

---

*Documento de referência completo para construção do Fake News Reporting Agent — Versão 1.0 — Fevereiro 2026*
*Este documento deve ser tratado como a fonte única de verdade por qualquer LLM agente que o consuma.*
