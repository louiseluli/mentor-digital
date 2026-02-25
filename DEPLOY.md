# Deploy — Mentor Digital

Guia completo para colocar o Mentor Digital em produção: bot (Railway) + web (Vercel).

---

## Pré-requisitos

Tenha em mãos antes de começar:

| Item | Como obter |
|------|-----------|
| `TELEGRAM_BOT_TOKEN` | BotFather → `/newbot` |
| `WEBHOOK_SECRET` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PSEUDONYMIZATION_PEPPER` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ANALYTICS_PEPPER` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| Conta Railway | [railway.app](https://railway.app) (plano Hobby $5/mês — Redis persistente) |
| Conta Vercel | [vercel.com](https://vercel.com) (free tier suficiente) |

**Opcionais** (análise de conteúdo aprimorada):

| Var | Serviço |
|-----|---------|
| `GOOGLE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) → Fact Check Tools API |
| `VIRUSTOTAL_API_KEY` | [virustotal.com](https://virustotal.com) → API Key (free: 4 req/min) |
| `OPENPAGERANK_API_KEY` | [domcop.com/openpagerank](https://domcop.com/openpagerank/signup) (free: 100 req/dia) |
| `WHATSAPP_*` | Meta Business Suite → WhatsApp Cloud API |

---

## Passo 1 — Railway: Bot + Redis

### 1.1 Criar projeto

1. Acesse [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Autorize o Railway a acessar o repositório e selecione-o
3. Railway detecta o `railway.toml` em `apps/bot` — confirme

> **Root Directory:** Em _Settings → Source Repo_, defina `Root Directory` como `apps/bot`.
> O Railway usará o `Dockerfile` de `apps/bot/` para construir a imagem.

### 1.2 Adicionar Redis

1. No projeto Railway → **+ New** → **Database** → **Redis**
2. O Railway cria o serviço e injeta `REDIS_URL` automaticamente no serviço do bot

### 1.3 Variáveis de ambiente

No serviço do bot → **Variables** → adicione:

| Variável | Valor |
|----------|-------|
| `PSEUDONYMIZATION_PEPPER` | string aleatória longa (32+ chars) |
| `ANALYTICS_PEPPER` | outra string aleatória diferente |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `WEBHOOK_SECRET` | token hex gerado no pré-requisito |
| `WEB_PLATFORM_URL` | `https://mentor-digital.vercel.app` (preencher após Passo 3) |
| `ALLOWED_ORIGINS` | `https://mentor-digital.vercel.app` (preencher após Passo 3) |
| `ENVIRONMENT` | `production` |

Opcionais (se disponíveis):

| Variável | Valor |
|----------|-------|
| `GOOGLE_API_KEY` | chave da API Fact Check |
| `VIRUSTOTAL_API_KEY` | chave VirusTotal |
| `OPENPAGERANK_API_KEY` | chave Open PageRank |
| `WHATSAPP_VERIFY_TOKEN` | token de verificação Meta |
| `WHATSAPP_APP_SECRET` | app secret Meta |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do número WhatsApp |
| `WHATSAPP_ACCESS_TOKEN` | access token Meta |

### 1.4 Deploy inicial

1. Railway faz deploy automático ao salvar variáveis
2. Aguarde o build (1-3 minutos) — acompanhe em **Deployments**
3. Copie o domínio público: `https://xxx.up.railway.app`

### 1.5 Verificar saúde

```bash
curl https://xxx.up.railway.app/health
# Esperado: {"status":"ok","service":"mentor-digital-bot"}
```

---

## Passo 2 — Registrar webhook Telegram

Com o Railway rodando, registre o endpoint do bot:

```bash
TELEGRAM_BOT_TOKEN=seu-token \
WEBHOOK_URL=https://xxx.up.railway.app \
WEBHOOK_SECRET=seu-webhook-secret \
python apps/bot/scripts/register_telegram_webhook.py
```

Saída esperada:
```
→ Validando token do bot...
✅ Token válido — bot: @MentorDigitalBot (id=...)
→ Registrando webhook:
  Callback  : https://xxx.up.railway.app/webhook/telegram
  Secret    : ********...
✅ Webhook registrado: Webhook was set
→ Confirmando registro...
  URL             : https://xxx.up.railway.app/webhook/telegram
  Pending updates : 0
✅ Webhook ativo e confirmado.
✅ Mentor Digital Telegram configurado!
```

**Alternativa via curl** (se o script não estiver disponível):
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://xxx.up.railway.app/webhook/telegram\",
    \"secret_token\": \"${WEBHOOK_SECRET}\",
    \"allowed_updates\": [\"message\", \"callback_query\"],
    \"drop_pending_updates\": true
  }"
```

---

## Passo 3 — Vercel: Plataforma Web

### 3.1 Importar projeto

1. Acesse [vercel.com](https://vercel.com) → **Add New** → **Project** → **Import Git Repository**
2. Selecione o repositório
3. O Vercel lê `vercel.json` e detecta `rootDirectory: apps/web` e `framework: nextjs` automaticamente

### 3.2 Variáveis de ambiente

Em **Environment Variables** antes de fazer deploy:

| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_BOT_API_URL` | `https://xxx.up.railway.app` (URL do Railway) |

> **Nota:** A variável `NEXT_PUBLIC_BOT_API_URL` é usada por `apps/web/lib/api.ts` para
> chamar a API do bot. Verifique a variável `BASE_URL` em `lib/api.ts` para confirmar o nome exato.

### 3.3 Deploy

Clique em **Deploy** — a primeira build leva 1-3 minutos.

Copie o domínio: `https://mentor-digital.vercel.app` (ou o gerado pelo Vercel).

---

## Passo 4 — Atualizar Railway com URL do Vercel

Volte ao Railway → Variables e atualize:

| Variável | Valor |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://mentor-digital.vercel.app` |
| `WEB_PLATFORM_URL` | `https://mentor-digital.vercel.app` |

O Railway faz redeploy automático ao salvar. Isso habilita:
- CORS entre web e bot
- Links corretos nas mensagens de notificação do bot

---

## Passo 5 — Registrar webhook WhatsApp (opcional)

Se você tiver as credenciais WhatsApp Cloud API:

```bash
WEBHOOK_URL=https://xxx.up.railway.app \
WHATSAPP_APP_ID=seu-app-id \
WHATSAPP_ACCESS_TOKEN=seu-access-token \
WHATSAPP_VERIFY_TOKEN=seu-verify-token \
python apps/bot/scripts/register_whatsapp_webhook.py
```

Alternativa: configure manualmente em
[developers.facebook.com](https://developers.facebook.com) → seu app → WhatsApp → Configuração → Webhooks:
- **URL de callback:** `https://xxx.up.railway.app/webhook/whatsapp`
- **Token de verificação:** valor de `WHATSAPP_VERIFY_TOKEN`
- **Campos:** marque `messages`

---

## Checklist de verificação final

Após concluir todos os passos:

- [ ] `GET https://xxx.up.railway.app/health` → `{"status":"ok"}`
- [ ] `GET https://xxx.up.railway.app/analytics/summary` → JSON com `total`, `by_risk_level`, etc.
- [ ] Telegram: enviar `/start` ao bot → resposta imediata
- [ ] Telegram: enviar uma notícia suspeita → bot inicia questionamento FSM
- [ ] Telegram: aguardar análise (30s-2min) → bot envia link `✅ Análise pronta!`
- [ ] Web: `https://mentor-digital.vercel.app/analise/{content_id}` → página de análise carrega
- [ ] Web: `https://mentor-digital.vercel.app/analytics` → painel de impacto visível
- [ ] (Se WhatsApp configurado) WhatsApp: enviar mensagem → bot responde

---

## Deploy contínuo

Tanto Railway quanto Vercel detectam novos commits no branch `main` e fazem redeploy automaticamente.

O GitHub Actions (`.github/workflows/ci.yml`) valida cada push/PR com:
- Testes Python (`pytest`) — falha bloqueia merge
- Type-check TypeScript (`tsc --noEmit`) — falha bloqueia merge
- Docker build — confirma que a imagem builda sem erros

---

## Troubleshooting

### Bot não responde no Telegram

1. Verificar logs no Railway: **Deployments → View Logs**
2. Verificar webhook: `GET https://api.telegram.org/bot{TOKEN}/getWebhookInfo`
3. Confirmar que `WEBHOOK_SECRET` no Railway bate com o registrado no Telegram

### CORS error na web

- Confirmar que `ALLOWED_ORIGINS` no Railway inclui a URL exata do Vercel (sem barra no final)
- Verificar se houve redeploy após salvar as vars

### Análise não salva / link quebrado

- Verificar que `REDIS_URL` está injetada pelo serviço Redis do Railway
- Verificar logs de erro: buscar `Falha na análise background` nos logs do Railway

### Analytics vazio

- `GET .../analytics/summary` retorna `{"total":0,...}` até que o primeiro conteúdo seja analisado com sucesso
