# SESSION LOG — Mentor Digital Bot

## Último Micro-Batch Completado
**10.x — Analysis Pipeline v1.0** ✅ (2 mar 2026)

## Status Atual
- **Branch**: `feat/platform-v2-analytics-learning-persistence`
- **Base estável**: `main` @ commit `a397427` — 357 testes passando
- **GDELT**: fora do ar desde fev/2026 (100% packet loss, TLS handshake timeout)
- **NewsAPI**: HTTP 426 (free tier expirado)

## Melhorias feitas na sessão atual (10.x)

### Fontes de notícias
- **Google News RSS** (`google_news.py`): cliente PT-BR + EN-US como fallback ao GDELT
- **NewsAPI.org** (`newsapi.py`): cliente internacional (atualmente 426)
- **Wikipedia API** (`wikipedia_api.py`): contexto enciclopédico
- **Brazilian FC RSS** (`brazilian_fc.py`): Aos Fatos + Agência Lupa
- Keyword extraction com prioridade a nomes próprios, reduzido a 4-6 palavras
- English stopwords adicionadas: "that", "will", "in", "and", etc.

### NLP & Scoring
- **50+ regras de manipulação**: political conspiracy, health denial, progressive tense hiding, hoax/fabrication, wake up patterns, suppressed info
- **CAPS bugfix**: regex com `re.IGNORECASE` fazia match em qualquer palavra 4+ chars → corrigido para usar texto original
- **Scoring multidimensional**: `claim_penalty` dimension, manipulation floors (≥0.50 → min 0.55), combined signal boost
- **Fórmula COM fact-checks**: `linguistic×0.25 + fc_signal×0.65 + (1−coverage)×0.10`
- **Fórmula SEM fact-checks**: `linguistic×0.55 + claim_penalty×0.15 + (1−coverage×0.30)×0.30`

### Web UX
- **Fix 404 race condition**: backend retorna 202 enquanto análise processa; frontend mostra "ANALISANDO FONTES…" animado; link só aparece quando `analysisReady`
- **Polling**: 30 retries × 2s (60s total) com suporte a HTTP 202
- **analysis-content.tsx**: client-side fallback para quando SSR não alcança localhost:8000
- CORS fix para porta 3001, Wikipedia User-Agent fix

### Resultados de testes ao vivo
| Claim | Score | Nível | Fact-checks |
|-------|-------|-------|-------------|
| Ivermectina cura COVID | 0.68 | ALTO | — |
| Climate change is a hoax | 0.64 | ALTO | — |
| Fraude eleitoral urnas eletrônicas | 0.80 | CRÍTICO | 12 (7 falso + 3 misto) |

## Status dos Testes (bot — Python) — 357 total
| Arquivo | Status | Testes |
|---------|--------|--------|
| test_models.py | ✅ PASS | 5/5 |
| test_flows.py | ✅ PASS | 7/7 |
| test_fsm.py | ✅ PASS | 15/15 |
| test_security.py | ✅ PASS | 8/8 |
| test_content_detector.py | ✅ PASS | 16/16 |
| test_session_manager.py | ✅ PASS | 19/19 |
| test_telegram.py | ✅ PASS | 13/13 |
| test_whatsapp.py | ✅ PASS | 20/20 |
| test_e2e_flow.py | ✅ PASS | 7/7 |
| test_webhook.py | ✅ PASS | 8/8 |
| test_analysis_endpoint.py | ✅ PASS | 17/17 |
| test_fact_checker.py | ✅ PASS | 13/13 |
| test_analysis_service.py | ✅ PASS | 23/23 |
| test_analytics.py | ✅ PASS | 20/20 |
| test_notifications.py | ✅ PASS | 8/8 |
| test_domain_checker.py | ✅ PASS | 28/28 |
| test_gdelt.py | ✅ PASS | 23/23 |
| test_nlp.py | ✅ PASS | 44/44 |
| test_google_news.py | ✅ PASS | 27/27 |
| test_newsapi.py | ✅ PASS | 42/42 |
| **Total** | ✅ | **357/357** |

## Estrutura da Plataforma Web (8.3)
```
apps/web/
├── app/
│   ├── analytics/page.tsx             ← Painel de impacto (Server Component, revalidate: 300s)
│   └── analise/[content_id]/page.tsx  ← Página de análise
├── components/
│   ├── analytics-dashboard.tsx        ← Dashboard: total, risco, plataforma, tipo, cobertura
│   └── header.tsx                     ← Link "Impacto" adicionado
└── lib/api.ts                         ← AnalyticsSummary + fetchAnalyticsSummary()
```

## Estrutura da Plataforma Web (5.3)
```
apps/web/                          ← Next.js 16.1.6 · React 19 · TailwindCSS v4
├── app/
│   ├── layout.tsx                 ← lang="pt-BR", metadata, viewport, <Header />
│   ├── page.tsx                   ← Landing: instrução de uso
│   ├── manifest.ts                ← Web App Manifest (PWA)
│   ├── icon.tsx                   ← Favicon 32×32 (ImageResponse)
│   ├── apple-icon.tsx             ← Apple touch icon 180×180 (ImageResponse)
│   └── analise/[content_id]/
│       └── page.tsx               ← Balança + FactCheck + GDELT + rodapé
├── components/
│   ├── header.tsx                 ← Sticky top bar com branding
│   ├── evidence-scale.tsx         ← Balança da Evidência (NLP visual)
│   ├── factcheck-section.tsx      ← Verificações Google Fact Check
│   ├── gdelt-section.tsx          ← Artigos de mídia global (GDELT)
│   └── ui/
│       ├── card.tsx · badge.tsx · progress.tsx · separator.tsx · skeleton.tsx
├── lib/
│   ├── utils.ts                   ← shadcn/ui utils
│   └── api.ts                     ← fetchAnalysis + tipos completos (FC, GDELT, NLP)
├── .env.example                   ← NEXT_PUBLIC_BOT_API_URL=http://localhost:8000
└── next.config.ts                 ← turbopack.root configurado
```

## Arquivos de Deploy (6.1)
```
apps/bot/
├── Dockerfile                     ← multi-stage build (builder + runtime slim)
├── .dockerignore                  ← exclui tests/, venv/, .env, logs
├── railway.toml                   ← builder=DOCKERFILE, healthcheck /health
└── requirements-prod.txt          ← prod apenas (sem pytest/fakeredis)
vercel.json                        ← rootDirectory: apps/web (monorepo)
```

## Decisões Tomadas (atualizado 6.1)
- **Next.js 16** (create-next-app@16.1.6 disponível em fev/2026)
- **App Router** com Server Components — fetch direto no servidor, sem useEffect
- **shadcn/ui v3** + Tailwind v4 — paleta Neutral (acessível)
- `fetchAnalysis()` usa `next: { revalidate: 60 }` — cache de 60s, sem rebuild manual
- Rota `/analise/[content_id]` retorna 404 amigável se análise não encontrada/expirada
- **PWA**: `manifest.ts` (display: standalone, theme_color #171717), ícones via `ImageResponse`
- **Balança da Evidência**: score = urgência×0.4 + manipulação×0.6; 4 níveis; linguagem pedagógica
- **FactCheckSection**: mescla PT+EN; oculta sem resultados/erro; badge por `rating_value`
- **GDELTSection**: deduplicação por URL, mescla PT+EN, top 5
- **Deploy bot**: Railway (Docker multi-stage) + Redis como serviço separado no Railway
- **Deploy web**: Vercel com `vercel.json` apontando `rootDirectory: apps/web`
- **requirements-prod.txt** separado do requirements.txt (sem pytest/fakeredis na imagem)
- `PORT` env var injetado pelo Railway — CMD usa `${PORT}` via `sh -c`
- **CORS por origem** (`ALLOWED_ORIGINS` env var, vírgula-separado): dev default `http://localhost:3000`
- **Rate limiting** (`slowapi==0.1.9`): 60 req/min por IP em `GET /analysis/`; storage in-memory MVP
- **Logging JSON** (`_JSONFormatter`): sem dep extra; emite `{"ts","level","logger","msg"}` por linha
- Testes: 253/253 passando (adição de slowapi + WhatsApp)
- **Canal WhatsApp** (7.1): `src/webhooks/whatsapp.py` reutiliza FSM Telegram; buttons ≤3 opções, list >3; HMAC-SHA256 em main.py; GET /webhook/whatsapp para verificação Meta
- **Testes e2e** (7.2): `test_e2e_flow.py` — FSM real + fakeredis; sem mock de SessionManager; cobre mensagem→sessão→análise→recuperação API
- **Script de registro** (7.2): `scripts/register_whatsapp_webhook.py` — verifica endpoint + registra via Graph API v22.0
- **CI/CD** (8.1): `.github/workflows/ci.yml` — 3 jobs: test-bot (Python 3.12 + pytest), typecheck-web (Node 20 + tsc --noEmit), docker-build (buildx, push=false, GHA cache; depende de test-bot)
- **Analytics** (8.2): `src/analytics.py` — `AnalyticsEvent.from_analysis()`, `record_event()` (ZADD sorted set, máx 10k eventos), `get_summary()` (ZRANGEBYSCORE por período); hookado em `_analyze_and_persist` de telegram.py e whatsapp.py; endpoint `GET /analytics/summary?days=30`; fórmula de risco = urgência×0.4 + manipulação×0.6 (idêntica ao frontend); zero PII
- **Painel de analytics** (8.3): `app/analytics/page.tsx` Server Component + `components/analytics-dashboard.tsx`; dados via `fetchAnalyticsSummary()` (revalidate: 300s); exibe total, distribuição por risco/plataforma/tipo de conteúdo, cobertura FC+GDELT, médias de sinais; link "Impacto" no header; empty state pedagógico
- **Notificação de resultado** (8.4): `_analyze_and_persist` ganha parâmetro `notify=None` (coroutine opcional); handlers Telegram e WhatsApp criam closures que capturam `chat_id`/`from_phone` + `phone_number_id` em memória (sem persistir PII); envia "✅ Análise pronta! {link}" ao fim da análise; exceção em notify silenciada; 8 novos testes em `test_notifications.py`

## Como iniciar (desenvolvimento)
```bash
# Terminal 1 — Bot FastAPI
cd apps/bot && uvicorn src.main:app --reload --port 8000

# Terminal 2 — Plataforma Web
cd apps/web && npm run dev   # → http://localhost:3000
```

## Deploy — Passo a Passo

### 1. Railway (Bot + Redis)
```bash
# Instalar Railway CLI (opcional)
npm i -g @railway/cli && railway login

# Ou via dashboard: railway.app → New Project → Deploy from GitHub
# Settings → Source Repo → Root Directory: apps/bot
# New → Database → Add Redis
```

Variáveis de ambiente no Railway (Settings → Variables):
| Variável | Valor |
|----------|-------|
| `REDIS_URL` | injetado automaticamente pelo serviço Redis |
| `TELEGRAM_BOT_TOKEN` | token do @BotFather |
| `WEBHOOK_SECRET` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `WEB_PLATFORM_URL` | URL do Vercel (preencher após step 2) |
| `PSEUDONYMIZATION_PEPPER` | string aleatória longa |
| `ANALYTICS_PEPPER` | string aleatória longa |
| `GOOGLE_API_KEY` | opcional — fact-check |
| `ENVIRONMENT` | `production` |

### 2. Vercel (Web)
```bash
# Via CLI
npx vercel --cwd apps/web
# → detecta Next.js automaticamente

# Ou: vercel.com → New Project → Import repo → Root Directory: apps/web (já em vercel.json)
```

Variável de ambiente no Vercel:
| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_BOT_API_URL` | URL pública do Railway (ex: `https://mentor-digital-bot.up.railway.app`) |

### 3. Registrar webhook do Telegram
```bash
# Após Railway estar online
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<railway-url>/webhook/telegram", "secret_token": "<WEBHOOK_SECRET>"}'
```

### 4. Atualizar CORS em produção
Em `apps/bot/src/main.py`, substituir `allow_origins=["*"]` pela URL real do Vercel:
```python
allow_origins=["https://mentor-digital.vercel.app"],
```

## Chaves de API — Status
| API | Chave | Gratuito |
|-----|-------|--------|
| Google Fact Check | `GOOGLE_API_KEY` | sim — adicionar depois |
| VirusTotal | `VIRUSTOTAL_API_KEY` | sim — virustotal.com |
| Open PageRank | `OPENPAGERANK_API_KEY` | sim — domcop.com/openpagerank |
| RDAP | — | sem chave |
| urlscan.io (busca) | — | sem chave |
| GDELT | — | sem chave |
| NLP | — | sem chave (local) |

## Próximo Micro-Batch
**9.x — Deploy real** (Railway + Vercel + registro webhooks Telegram e WhatsApp em produção)
