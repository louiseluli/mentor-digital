"""
whatsapp.py — Handler do WhatsApp Cloud API (Micro-Batch 7.1)

Reutiliza o mesmo FSM pedagógico do canal Telegram.
Sessões persistidas no Redis via SessionManager (chave = pseudônimo do número).

Tipos de mensagem suportados: texto, link, imagem, vídeo, áudio, documento.
Botões interativos: button (≤3 opções) ou list (>3 opções).

Configuração:
  WHATSAPP_ACCESS_TOKEN   → token de acesso da WhatsApp Cloud API (Meta)
  WHATSAPP_APP_SECRET     → segredo para validar HMAC (verificado em main.py)
  WHATSAPP_VERIFY_TOKEN   → token de verificação do webhook (verificado em main.py)
  WEB_PLATFORM_URL        → URL da plataforma web para links de análise
"""

import asyncio
import logging
import os

import httpx

from src.analysis.analysis_service import analyze_content
from src.analytics import AnalyticsEvent, record_event
from src.content_detector import detect_text_type
from src.engine.fsm import QuestioningFSM
from src.models import ConversationContext
from src.security import pseudonymize
from src.session_manager import SessionManager

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v22.0"
WEB_URL = os.getenv("WEB_PLATFORM_URL", "http://localhost:3001")

# Limites da WhatsApp Cloud API
_MAX_BUTTONS = 3       # botão interativo: máximo 3 botões
_BTN_TITLE_MAX = 20    # título de botão: máximo 20 chars
_LIST_TITLE_MAX = 24   # título de linha de lista: máximo 24 chars

_session_mgr: "SessionManager | None" = None


# ── Session manager ────────────────────────────────────────────────────────────

def _get_session_mgr() -> SessionManager:
    global _session_mgr
    if _session_mgr is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _session_mgr = SessionManager.from_url(redis_url)
    return _session_mgr


# ── Envio de mensagens ────────────────────────────────────────────────────────

async def _send_text(phone_number_id: str, to: str, body: str) -> None:
    """Envia mensagem de texto simples via WhatsApp Cloud API."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    if not token:
        logger.debug("WHATSAPP_ACCESS_TOKEN não configurado — envio ignorado.")
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{GRAPH_API_URL}/{phone_number_id}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception as exc:
        logger.error("WhatsApp _send_text falhou: %s", exc)


async def _send_interactive(
    phone_number_id: str, to: str, body: str, options: list
) -> None:
    """Envia botões interativos (≤3 opções) ou lista interativa (>3 opções)."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    if not token:
        logger.debug("WHATSAPP_ACCESS_TOKEN não configurado — envio ignorado.")
        return

    if len(options) <= _MAX_BUTTONS:
        interactive = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": opt["id"],
                            "title": opt["title"][:_BTN_TITLE_MAX],
                        },
                    }
                    for opt in options
                ]
            },
        }
    else:
        interactive = {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": "Ver opções",
                "sections": [
                    {
                        "title": "Opções",
                        "rows": [
                            {
                                "id": opt["id"],
                                "title": opt["title"][:_LIST_TITLE_MAX],
                            }
                            for opt in options
                        ],
                    }
                ],
            },
        }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{GRAPH_API_URL}/{phone_number_id}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception as exc:
        logger.error("WhatsApp _send_interactive falhou: %s", exc)


# ── Helpers FSM ───────────────────────────────────────────────────────────────

def _fill_placeholders(text: str, ctx: ConversationContext) -> str:
    return text.replace("{web_platform_url}", WEB_URL).replace(
        "{content_id}", ctx.content_id
    )


def _collect_messages(fsm: QuestioningFSM, initial_response: dict) -> list[dict]:
    """Coleta mensagens e avança automaticamente por estados sem opções."""
    all_messages = list(initial_response.get("messages", []))
    while True:
        state_data = fsm._flow.get(fsm.state, {})
        has_options = state_data.get("options") or state_data.get(
            "follow_up", {}
        ).get("options", [])
        if not has_options and "next_state" in state_data:
            next_response = fsm._handle_yaml_state("")
            all_messages.extend(next_response.get("messages", []))
        else:
            break
    return all_messages


async def _send_messages(
    messages: list[dict],
    ctx: ConversationContext,
    phone_number_id: str,
    to: str,
) -> None:
    for msg in messages:
        body = _fill_placeholders(msg.get("body", ""), ctx)
        options = msg.get("options", [])
        if not body:
            continue
        if options:
            await _send_interactive(phone_number_id, to, body, options)
        else:
            await _send_text(phone_number_id, to, body)


# ── Background analysis ────────────────────────────────────────────────────────

async def _analyze_and_persist(
    ctx: ConversationContext,
    mgr: SessionManager,
    user_id: str,
    fsm: QuestioningFSM,
    *,
    notify=None,
) -> None:
    """Roda análise em background e persiste resultados.

    notify: coroutine opcional async def _(content_id: str) -> None — chamada após
    a análise terminar para enviar follow-up ao usuário. Exceções silenciadas.
    """
    try:
        results = await analyze_content(ctx)
        mgr.save(user_id, fsm)
        mgr.save_analysis(ctx.content_id, results)
        logger.info("Análise persistida | content_id=%s", ctx.content_id)
        event = AnalyticsEvent.from_analysis(ctx.platform, ctx.content_type, results)
        record_event(event, mgr.redis)
    except Exception as exc:
        logger.error(
            "Falha na análise background | content_id=%s | erro=%s",
            ctx.content_id,
            exc,
        )
        return

    if notify:
        try:
            await notify(ctx.content_id)
        except Exception as exc:
            logger.error(
                "Falha na notificação | content_id=%s | erro=%s", ctx.content_id, exc
            )


# ── Parsing do payload ────────────────────────────────────────────────────────

def _extract_message(
    payload: dict,
) -> "tuple[str, str, str, str, str] | None":
    """Extrai (from_phone, msg_type, content_raw, interaction_id, phone_number_id).

    Retorna None se o payload não contiver mensagem válida.
    """
    try:
        entry = payload.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        from_phone: str = msg.get("from", "")
        msg_type: str = msg.get("type", "")
        phone_number_id: str = value.get("metadata", {}).get("phone_number_id", "")

        content_raw = ""
        interaction_id = ""

        if msg_type == "text":
            content_raw = msg.get("text", {}).get("body", "")
        elif msg_type == "interactive":
            inter = msg.get("interactive", {})
            inter_type = inter.get("type", "")
            if inter_type == "button_reply":
                interaction_id = inter.get("button_reply", {}).get("id", "")
                content_raw = inter.get("button_reply", {}).get("title", "")
            elif inter_type == "list_reply":
                interaction_id = inter.get("list_reply", {}).get("id", "")
                content_raw = inter.get("list_reply", {}).get("title", "")
        elif msg_type == "image":
            content_raw = msg.get("image", {}).get("caption", "") or "[imagem]"
        elif msg_type == "video":
            content_raw = msg.get("video", {}).get("caption", "") or "[vídeo]"
        elif msg_type in ("audio", "voice"):
            content_raw = "[áudio]"
        elif msg_type == "document":
            doc = msg.get("document", {})
            content_raw = doc.get("caption", "") or (
                f"[documento: {doc.get('filename', 'arquivo')}]"
            )

        if not from_phone or not msg_type:
            return None

        return from_phone, msg_type, content_raw, interaction_id, phone_number_id

    except (IndexError, KeyError, TypeError):
        return None


# ── Handler principal ──────────────────────────────────────────────────────────

async def handle_whatsapp_message(payload: dict) -> None:
    """Processa um update recebido da WhatsApp Cloud API."""
    extracted = _extract_message(payload)
    if extracted is None:
        return

    from_phone, msg_type, content_raw, interaction_id, phone_number_id = extracted

    user_id = pseudonymize(from_phone)
    mgr = _get_session_mgr()
    fsm = mgr.get_or_create(user_id)

    # ── Resposta interativa (clique em botão ou lista) ─────────────────────────
    if msg_type == "interactive" and interaction_id:
        response = fsm.process_input(interaction_id)
        messages = _collect_messages(fsm, response)
        if fsm.state == "end":
            mgr.delete(user_id)
        else:
            mgr.save(user_id, fsm)
        await _send_messages(messages, fsm.context, phone_number_id, from_phone)
        return

    if not content_raw:
        return

    # ── Mensagem de conteúdo (texto ou mídia) ─────────────────────────────────
    is_first_content = fsm.state == "awaiting_content"

    if is_first_content:
        content_type = detect_text_type(content_raw) if msg_type == "text" else msg_type
    else:
        content_type = "text"

    response = fsm.process_input(content_raw, content_type)
    messages = _collect_messages(fsm, response)

    if fsm.state == "end":
        mgr.delete(user_id)
    else:
        mgr.save(user_id, fsm)

    if is_first_content:
        _from_phone = from_phone
        _phone_number_id = phone_number_id

        async def _notify(content_id: str) -> None:
            link = f"{WEB_URL}/analise/{content_id}"
            await _send_text(
                _phone_number_id,
                _from_phone,
                f"✅ Análise pronta!\n\nAcesse os resultados:\n{link}",
            )

        asyncio.create_task(
            _analyze_and_persist(fsm.context, mgr, user_id, fsm, notify=_notify)
        )

    await _send_messages(messages, fsm.context, phone_number_id, from_phone)
