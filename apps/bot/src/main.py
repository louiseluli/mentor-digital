"""
main.py — FastAPI Gateway (Micro-Batch 2.5 · Hardening 6.2)

Em desenvolvimento: use polling (python -m src.webhooks.telegram).
Em produção: configure WEBHOOK_SECRET e inicie com uvicorn src.main:app.
Após deploy, registre o webhook uma vez:
    POST https://api.telegram.org/bot<TOKEN>/setWebhook
    {"url": "https://seu-dominio.com/webhook/telegram", "secret_token": "<WEBHOOK_SECRET>"}
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from telegram import Update

from src.session_manager import SessionManager

load_dotenv()


# ── Logging estruturado (JSON) ─────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """Emite cada log como uma linha JSON — compatível com Railway / Vercel."""

    def format(self, record: logging.LogRecord) -> str:
        obj: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


_configure_logging()
logger = logging.getLogger(__name__)


# ── Instâncias globais — inicializadas lazily ──────────────────────────────────

_telegram_app = None
_session_mgr: "SessionManager | None" = None


def _get_session_mgr() -> SessionManager:
    global _session_mgr
    if _session_mgr is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _session_mgr = SessionManager.from_url(redis_url)
    return _session_mgr


def _build_telegram_app():
    """Factory isolado para facilitar mock nos testes."""
    from src.webhooks.telegram import build_application
    return build_application()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _telegram_app
    _telegram_app = _build_telegram_app()
    await _telegram_app.initialize()
    logger.info("Telegram Application inicializada (webhook mode).")
    yield
    if _telegram_app:
        await _telegram_app.shutdown()
        logger.info("Telegram Application encerrada.")


# ── Rate limiting ──────────────────────────────────────────────────────────────
# MVP: in-memory (single instance). Para multi-instância, trocar storage_uri
# para REDIS_URL e adicionar a lib `limits[redis]` ao requirements-prod.txt.

limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mentor Digital — Fake News Reporting Agent",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origens lidas de ALLOWED_ORIGINS (vírgula-separado)
# Dev default: http://localhost:3000
# Prod: definir ALLOWED_ORIGINS=https://mentor-digital.vercel.app no Railway
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────────

# ── Web Chat helpers ───────────────────────────────────────────────────────────

_WEB_CHAT_PREFIX = "mentor:webchat:"
_WEB_CHAT_TTL = 3600  # 1 hora


def _save_web_chat(session_id: str, fsm, analysis_ready: bool) -> None:
    data = json.dumps({
        "context": fsm.context.to_json(),
        "state": fsm.state,
        "nlp_data": fsm.nlp_data,
        "analysis_ready": analysis_ready,
    })
    _get_session_mgr().redis.set(f"{_WEB_CHAT_PREFIX}{session_id}", data, ex=_WEB_CHAT_TTL)


def _load_web_chat(session_id: str) -> "dict | None":
    raw = _get_session_mgr().redis.get(f"{_WEB_CHAT_PREFIX}{session_id}")
    if not raw:
        return None
    from src.models import ConversationContext
    from src.engine.fsm import QuestioningFSM
    data = json.loads(raw)
    ctx = ConversationContext.from_json(data["context"])
    fsm = QuestioningFSM(ctx)
    fsm.state = data["state"]
    fsm.nlp_data = data.get("nlp_data")
    return {"fsm": fsm, "analysis_ready": data["analysis_ready"]}


def _collect_web_messages(fsm, initial_response: dict) -> list:
    """Auto-avança estados sem opções (mesmo padrão do telegram.py)."""
    all_msgs = list(initial_response.get("messages", []))
    while True:
        state_data = fsm._flow.get(fsm.state, {})
        has_options = (
            state_data.get("options")
            or state_data.get("follow_up", {}).get("options", [])
        )
        if not has_options and "next_state" in state_data:
            next_resp = fsm._handle_yaml_state("")
            all_msgs.extend(next_resp.get("messages", []))
        else:
            break
    return all_msgs


def _format_findings_for_chat(results: dict) -> str:
    """Formata achados de análise (com risk_score) para injetar no fechamento da conversa web."""
    risk = results.get("risk_score") or {}
    level = risk.get("level", "")
    verdict = risk.get("verdict", "no_data")
    verdict_pt = risk.get("verdict_pt", "Sem verificações específicas encontradas")
    overall = risk.get("overall", 0.0)
    confidence = risk.get("confidence", 0.0)
    breakdown = risk.get("fc_verdict_breakdown", {})

    level_emoji = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}.get(level, "⚪")

    lines = ["🔍 Enquanto conversávamos, analisamos o conteúdo:"]
    lines.append(f"\n{level_emoji} Risco geral: {overall * 100:.0f}% — {verdict_pt}")
    lines.append(f"📊 Confiança da análise: {confidence * 100:.0f}%")

    total = breakdown.get("total", 0)
    if total > 0:
        false_c = breakdown.get("false", 0)
        true_c = breakdown.get("true", 0)
        mixed_c = breakdown.get("mixed", 0)
        lines.append(f"\n✅ {total} verificação(ões) encontrada(s): "
                     f"{false_c} falso, {mixed_c} misto, {true_c} verdadeiro")
        # Mostrar detalhes de até 2 claims
        fc = results.get("fact_check", {})
        claims = fc.get("pt", {}).get("results", []) + fc.get("en", {}).get("results", [])
        for claim in claims[:2]:
            reviews = claim.get("reviews", [])
            if reviews:
                r = reviews[0]
                text = claim.get("text", "")[:70]
                lines.append(f'  • "{text}…"\n    {r.get("publisher_name", "")}: {r.get("text_rating", "")}')
    else:
        lines.append("\n  Não encontramos fact-checks específicos para este conteúdo.")

    # Verificadores brasileiros via RSS
    br_fc = results.get("brazilian_fc", {}).get("results", [])
    if br_fc:
        sources = list({r.get("source", "") for r in br_fc})
        lines.append(f"\n🇧🇷 Mencionado em {len(br_fc)} artigo(s) de verificadores brasileiros "
                     f"({', '.join(sources)})")

    # GDELT
    gdelt = results.get("gdelt", {})
    total_articles = (
        len(gdelt.get("por", {}).get("articles", []))
        + len(gdelt.get("en", {}).get("articles", []))
    )
    if total_articles:
        lines.append(f"\n📰 {total_articles} artigo(s) na mídia sobre o tema.")

    # Wikipedia
    wiki = results.get("wikipedia", {})
    wiki_results = wiki.get("pt", {}).get("results", []) + wiki.get("en", {}).get("results", [])
    if wiki_results:
        w = wiki_results[0]
        extract = w.get("extract", "")[:100]
        lines.append(f"\n📚 Wikipedia — {w.get('title', '')}: {extract}…")

    return "\n".join(lines)


async def _analyze_web_session(ctx, session_id: str) -> None:
    """Roda análise completa em background e marca sessão web como pronta."""
    try:
        from src.analysis.analysis_service import analyze_content
        results = await analyze_content(ctx)
        _get_session_mgr().save_analysis(ctx.content_id, results)
        raw = _get_session_mgr().redis.get(f"{_WEB_CHAT_PREFIX}{session_id}")
        if raw:
            data = json.loads(raw)
            data["analysis_ready"] = True
            _get_session_mgr().redis.set(
                f"{_WEB_CHAT_PREFIX}{session_id}", json.dumps(data), ex=_WEB_CHAT_TTL
            )
        logger.info("Web session analysis ready | session=%s | content=%s", session_id, ctx.content_id)
    except Exception as exc:
        logger.error("Web session analysis failed | session=%s | error=%s", session_id, exc)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mentor-digital-bot"}


@app.get("/analysis/{content_id}")
@limiter.limit("60/minute")
async def get_analysis(request: Request, content_id: str):
    """Retorna resultados de análise para a plataforma web.

    O content_id (UUID v4) actua como token de acesso — 122 bits de entropia.
    Resultados disponíveis por 7 dias após a análise ser completada pelo bot.
    Não contém dados pessoais identificáveis (LGPD).

    Rate limit: 60 req/min por IP.
    """
    data = _get_session_mgr().get_analysis(content_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada ou expirada")
    return data


@app.post("/analyze")
@limiter.limit("10/minute")
async def submit_analysis(request: Request):
    """Análise direta via plataforma web — sem necessidade do bot.

    Aceita texto livre, roda análise completa (NLP + fact-check + GDELT),
    persiste resultado no Redis e retorna content_id para acesso via /analise/{id}.

    Rate limit: 10 req/min por IP.
    """
    from src.models import ConversationContext
    from src.analysis.analysis_service import analyze_content

    body = await request.json()
    text = (body.get("text") or "").strip()
    if len(text) < 10:
        raise HTTPException(status_code=422, detail="Texto muito curto (mínimo 10 caracteres)")
    if len(text) > 5000:
        raise HTTPException(status_code=422, detail="Texto muito longo (máximo 5000 caracteres)")

    ctx = ConversationContext(user_id="web", platform="web", content_raw=text)
    results = await analyze_content(ctx)
    _get_session_mgr().save_analysis(ctx.content_id, results)
    return {"content_id": ctx.content_id}


@app.post("/chat/start")
@limiter.limit("5/minute")
async def chat_start(request: Request):
    """Inicia conversa educativa via web — NLP imediato + análise completa em background.

    Retorna primeiras mensagens FSM (sinais NLP + saudação) e session_id para continuação.
    Rate limit: 5 req/min por IP.
    """
    from src.models import ConversationContext
    from src.engine.fsm import QuestioningFSM
    from src.analysis.nlp import analyze_text, serialize_nlp_result
    from src.content_detector import detect_text_type

    body = await request.json()
    text = (body.get("text") or "").strip()
    if len(text) < 10:
        raise HTTPException(status_code=422, detail="Texto muito curto (mínimo 10 caracteres)")
    if len(text) > 5000:
        raise HTTPException(status_code=422, detail="Texto muito longo (máximo 5000 caracteres)")

    ctx = ConversationContext(user_id="web", platform="web", content_raw=text)
    fsm = QuestioningFSM(ctx)

    # NLP síncrono (<5ms) — alimenta mensagem educativa de boas-vindas
    nlp_result = analyze_text(text)
    fsm.nlp_data = serialize_nlp_result(nlp_result)

    content_type = detect_text_type(text)
    response = fsm.process_input(text, content_type)
    messages = _collect_web_messages(fsm, response)

    session_id = ctx.content_id  # UUID compartilhado entre sessão e análise
    _save_web_chat(session_id, fsm, analysis_ready=False)

    # Análise completa (FC + GDELT + Wikipedia + NLP) em background
    asyncio.create_task(_analyze_web_session(ctx, session_id))

    return {
        "session_id": session_id,
        "content_id": ctx.content_id,
        "state": fsm.state,
        "messages": messages,
    }


@app.post("/chat/reply/{session_id}")
@limiter.limit("30/minute")
async def chat_reply(request: Request, session_id: str):
    """Processa resposta do usuário e avança o FSM da conversa web.

    Ao atingir o estado 'closing' com análise já concluída, injeta um resumo
    dos achados (fact-checks, artigos, Wikipedia) antes das mensagens do FSM.
    Rate limit: 30 req/min por IP.
    """
    from src.engine.fsm import QuestioningFSM

    body = await request.json()
    option_id = (body.get("option_id") or "").strip()

    session_data = _load_web_chat(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada")

    fsm = session_data["fsm"]
    analysis_ready = session_data["analysis_ready"]

    response = fsm.process_input(option_id)
    messages = _collect_web_messages(fsm, response)

    # Ao fechar a conversa, injeta achados da análise se já estiverem disponíveis
    if fsm.state == "closing" and analysis_ready:
        results = _get_session_mgr().get_analysis(fsm.context.content_id)
        if results:
            findings = _format_findings_for_chat(results)
            messages.insert(0, {"type": "text", "body": findings})

    _save_web_chat(session_id, fsm, analysis_ready=analysis_ready)

    return {
        "session_id": session_id,
        "state": fsm.state,
        "messages": messages,
        "analysis_ready": analysis_ready,
        "content_id": fsm.context.content_id,
    }


@app.get("/chat/{session_id}/status")
async def chat_status(session_id: str):
    """Verifica se a análise background foi concluída — usado para polling pelo frontend."""
    session_data = _load_web_chat(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada")
    return {
        "ready": session_data["analysis_ready"],
        "content_id": session_data["fsm"].context.content_id,
    }


@app.get("/analytics/summary")
async def analytics_summary(days: int = 30):
    """Sumário anonimizado de eventos de análise para relatórios de impacto.

    Retorna métricas agregadas (sem dados pessoais) dos últimos N dias:
    total de análises, distribuição por plataforma/tipo/risco/idioma,
    cobertura de fact-check e GDELT, médias de urgência e manipulação.

    Parâmetros:
        days: Janela de tempo em dias (padrão 30, máximo 365).
    """
    from src.analytics import get_summary
    mgr = _get_session_mgr()
    return get_summary(mgr.redis, days=min(days, 365))


@app.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> PlainTextResponse:
    """Verificação de webhook exigida pela Meta ao registrar o endpoint."""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificação inválido")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Recebe updates enviados pela WhatsApp Cloud API.

    Valida assinatura HMAC-SHA256 (X-Hub-Signature-256) se WHATSAPP_APP_SECRET
    estiver configurado. Processa o update em background e retorna 200 imediatamente.
    """
    from src.webhooks.whatsapp import handle_whatsapp_message

    body_bytes = await request.body()

    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
    if app_secret:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            app_secret.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            raise HTTPException(status_code=403, detail="Assinatura inválida")

    payload = json.loads(body_bytes)
    asyncio.create_task(handle_whatsapp_message(payload))
    return {"status": "ok"}


@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Recebe updates enviados pelo Telegram via webhook."""
    secret = os.getenv("WEBHOOK_SECRET")
    if secret and x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    if _telegram_app is None:
        raise HTTPException(status_code=503, detail="Serviço não inicializado")

    data = await request.json()
    update = Update.de_json(data, _telegram_app.bot)
    await _telegram_app.process_update(update)
    return {"ok": True}
