"""
telegram.py — Handler do Telegram Bot com FSM integrada (Micro-Batch 3.1)

Sessões persistidas no Redis via SessionManager.
Suporta texto, links e mídia (foto, vídeo, áudio, documento).
Análise de conteúdo disparada (fire-and-forget) ao receber o primeiro conteúdo.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM
from src.security import pseudonymize
from src.session_manager import SessionManager
from src.content_detector import detect_text_type
from src.analysis.analysis_service import analyze_content
from src.analytics import AnalyticsEvent, record_event

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WEB_URL = os.getenv("WEB_PLATFORM_URL", "http://localhost:3000")

# Singleton — inicializado na primeira chamada
_session_mgr: "SessionManager | None" = None


# ── Session manager ───────────────────────────────────────────────────────────

def _get_session_mgr() -> SessionManager:
    global _session_mgr
    if _session_mgr is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _session_mgr = SessionManager.from_url(redis_url)
    return _session_mgr


# ── Message helpers ──────────────────────────────────────────────────────────

def _fill_placeholders(text: str, ctx: ConversationContext) -> str:
    return text.replace("{web_platform_url}", WEB_URL).replace(
        "{content_id}", ctx.content_id
    )


def _collect_messages(fsm: QuestioningFSM, initial_response: dict) -> list[dict]:
    """Collect messages + auto-advance through states with no options (feedback → end)."""
    all_messages = list(initial_response.get("messages", []))
    while True:
        state_data = fsm._flow.get(fsm.state, {})
        has_options = (
            state_data.get("options")
            or state_data.get("follow_up", {}).get("options", [])
        )
        if not has_options and "next_state" in state_data:
            next_response = fsm._handle_yaml_state("")
            all_messages.extend(next_response.get("messages", []))
        else:
            break
    return all_messages


def _build_keyboard(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt["title"], callback_data=opt["id"])]
         for opt in options]
    )


async def _send_messages(
    messages: list[dict], ctx: ConversationContext, update: Update
) -> None:
    target = (
        update.callback_query.message if update.callback_query else update.message
    )
    for msg in messages:
        body = _fill_placeholders(msg.get("body", ""), ctx)
        options = msg.get("options", [])
        if not body:
            continue
        if options:
            await target.reply_text(body, reply_markup=_build_keyboard(options))
        else:
            await target.reply_text(body)


# ── Background analysis ───────────────────────────────────────────────────────

async def _analyze_and_persist(
    ctx: ConversationContext,
    mgr: SessionManager,
    user_id: str,
    fsm: "QuestioningFSM",
    *,
    notify=None,
) -> None:
    """Roda análise de conteúdo em background e re-persiste a sessão com os resultados.

    notify: coroutine opcional async def _(content_id: str) -> None — chamada após
    a análise terminar para enviar follow-up ao usuário. Exceções em notify são
    silenciadas para não bloquear o fluxo principal.
    """
    try:
        results = await analyze_content(ctx)
        mgr.save(user_id, fsm)
        mgr.save_analysis(ctx.content_id, results)
        logger.info("Análise persistida | content_id=%s", ctx.content_id)
        event = AnalyticsEvent.from_analysis(ctx.platform, ctx.content_type, results)
        record_event(event, mgr.redis)
    except Exception as exc:
        logger.error("Falha na análise background | content_id=%s | erro=%s", ctx.content_id, exc)
        return

    if notify:
        try:
            await notify(ctx.content_id)
        except Exception as exc:
            logger.error("Falha na notificação | content_id=%s | erro=%s", ctx.content_id, exc)


# ── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — apresenta o bot e reseta sessão."""
    user_id = pseudonymize(str(update.effective_user.id))
    _get_session_mgr().delete(user_id)
    await update.message.reply_text(
        "Olá! 👋 Sou o Mentor Digital, seu parceiro contra desinformação.\n\n"
        "Me envie qualquer texto, link ou mensagem que você recebeu "
        "e gostaria de pensar melhor antes de compartilhar. 🤔"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle texto ou link enviado pelo usuário — inicia ou continua o fluxo FSM."""
    user_id = pseudonymize(str(update.effective_user.id))
    text = (update.message.text or "").strip()
    if not text:
        return

    mgr = _get_session_mgr()
    fsm = mgr.get_or_create(user_id)
    is_first_content = fsm.state == "awaiting_content"
    content_type = detect_text_type(text) if is_first_content else "text"
    response = fsm.process_input(text, content_type)
    messages = _collect_messages(fsm, response)

    if fsm.state == "end":
        mgr.delete(user_id)
    else:
        mgr.save(user_id, fsm)

    # Disparar análise em background após salvar — não bloqueia a resposta ao usuário
    if is_first_content:
        _chat_id = update.effective_chat.id
        _bot = context.bot

        async def _notify(content_id: str) -> None:
            link = f"{WEB_URL}/analise/{content_id}"
            await _bot.send_message(
                chat_id=_chat_id,
                text=f"✅ Análise pronta!\n\nAcesse os resultados:\n{link}",
            )

        asyncio.create_task(
            _analyze_and_persist(fsm.context, mgr, user_id, fsm, notify=_notify)
        )

    await _send_messages(messages, fsm.context, update)


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle fotos, vídeos, áudios e documentos — inicia fluxo FSM com tipo correto."""
    user_id = pseudonymize(str(update.effective_user.id))
    msg = update.message

    if msg.photo:
        content_type = "image"
        content_raw = msg.caption or "[imagem sem legenda]"
    elif msg.video:
        content_type = "video"
        content_raw = msg.caption or "[vídeo sem legenda]"
    elif msg.audio or msg.voice:
        content_type = "audio"
        content_raw = msg.caption or "[áudio]"
    elif msg.document:
        content_type = "document"
        content_raw = msg.caption or f"[documento: {msg.document.file_name or 'arquivo'}]"
    else:
        return

    mgr = _get_session_mgr()
    fsm = mgr.get_or_create(user_id)
    is_first_content = fsm.state == "awaiting_content"
    response = fsm.process_input(content_raw, content_type)
    messages = _collect_messages(fsm, response)

    if fsm.state == "end":
        mgr.delete(user_id)
    else:
        mgr.save(user_id, fsm)

    if is_first_content:
        _chat_id = update.effective_chat.id
        _bot = context.bot

        async def _notify_media(content_id: str) -> None:
            link = f"{WEB_URL}/analise/{content_id}"
            await _bot.send_message(
                chat_id=_chat_id,
                text=f"✅ Análise pronta!\n\nAcesse os resultados:\n{link}",
            )

        asyncio.create_task(
            _analyze_and_persist(fsm.context, mgr, user_id, fsm, notify=_notify_media)
        )

    await _send_messages(messages, fsm.context, update)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle clique em botão inline — seleciona opção do fluxo FSM."""
    query = update.callback_query
    await query.answer()

    user_id = pseudonymize(str(update.effective_user.id))
    option_id = query.data

    mgr = _get_session_mgr()
    fsm = mgr.get_or_create(user_id)
    response = fsm.process_input(option_id)
    messages = _collect_messages(fsm, response)

    if fsm.state == "end":
        mgr.delete(user_id)
    else:
        mgr.save(user_id, fsm)

    await _send_messages(messages, fsm.context, update)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erro no update %s: %s", update, context.error)


# ── App builder ───────────────────────────────────────────────────────────────

def build_application() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN não definido no .env")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.Document.ALL,
        handle_media,
    ))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    return app


def run_polling() -> None:
    app = build_application()
    logger.info("Bot iniciado em modo polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_polling()
