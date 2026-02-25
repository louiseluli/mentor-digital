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
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


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
