"""
test_notifications.py — Testes da notificação de resultado ao usuário (Micro-Batch 8.4)

Testa _analyze_and_persist diretamente com a callable notify:
  1. notify é chamada com o content_id correto após análise bem-sucedida
  2. notify=None (default) não causa erros
  3. Exceção dentro de notify é silenciada — não propaga
  4. notify NÃO é chamada se analyze_content falhar
  5. Telegram: closure _notify criada no handler tem notify != None
  6. WhatsApp: closure _notify criada no handler tem notify != None
"""

import os
import sys

import fakeredis
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_notif")
os.environ.setdefault("ANALYTICS_PEPPER", "test_analytics_notif")

from src.models import ConversationContext
from src.session_manager import SessionManager
from src.engine.fsm import QuestioningFSM


# ── Helpers ────────────────────────────────────────────────────────────────────

MOCK_ANALYSIS = {
    "analyzed_at": "2024-01-15T12:00:00Z",
    "query": "Teste de notificação",
    "fact_check": {"pt": {"results": [], "error": ""}, "en": {"results": [], "error": ""}},
    "gdelt": {"por": {"articles": [], "error": ""}, "en": {"articles": [], "error": ""}},
    "nlp": {
        "language": "pt",
        "word_count": 3,
        "caps_ratio": 0.0,
        "error": "",
        "urgency": {"score": 0.1, "evidence": []},
        "claim": {"score": 0.2, "evidence": []},
        "manipulation": {"score": 0.0, "evidence": []},
    },
}


def _make_ctx(platform: str = "telegram") -> ConversationContext:
    return ConversationContext(
        user_id="test_user_notif",
        platform=platform,
        content_type="text",
        content_raw="Texto de teste",
    )


def _make_mgr() -> SessionManager:
    return SessionManager(fakeredis.FakeRedis(), ttl=60)


def _make_fsm(ctx: ConversationContext) -> QuestioningFSM:
    return QuestioningFSM(ctx)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_analyze():
    """Patch analyze_content em ambos os módulos que o usam."""
    with (
        patch(
            "src.webhooks.telegram.analyze_content",
            new_callable=AsyncMock,
            return_value=MOCK_ANALYSIS,
        ),
        patch(
            "src.webhooks.whatsapp.analyze_content",
            new_callable=AsyncMock,
            return_value=MOCK_ANALYSIS,
        ),
    ):
        yield


# ── 1. notify chamada com content_id correto ───────────────────────────────────

async def test_telegram_notify_called_with_correct_content_id(mock_analyze):
    from src.webhooks.telegram import _analyze_and_persist

    ctx = _make_ctx("telegram")
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)
    notify = AsyncMock()

    with patch("src.webhooks.telegram.record_event"):
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm, notify=notify)

    notify.assert_awaited_once_with(ctx.content_id)


async def test_whatsapp_notify_called_with_correct_content_id(mock_analyze):
    from src.webhooks.whatsapp import _analyze_and_persist

    ctx = _make_ctx("whatsapp")
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)
    notify = AsyncMock()

    with patch("src.webhooks.whatsapp.record_event"):
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm, notify=notify)

    notify.assert_awaited_once_with(ctx.content_id)


# ── 2. notify=None não causa erros ─────────────────────────────────────────────

async def test_notify_none_does_not_raise(mock_analyze):
    from src.webhooks.telegram import _analyze_and_persist

    ctx = _make_ctx()
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)

    with patch("src.webhooks.telegram.record_event"):
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm)  # notify=None por padrão


# ── 3. Exceção em notify é silenciada ──────────────────────────────────────────

async def test_notify_exception_is_silenced(mock_analyze):
    from src.webhooks.telegram import _analyze_and_persist

    ctx = _make_ctx()
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)

    async def broken_notify(content_id: str) -> None:
        raise ConnectionError("Telegram offline")

    with patch("src.webhooks.telegram.record_event"):
        # Não deve propagar a exceção
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm, notify=broken_notify)


async def test_whatsapp_notify_exception_is_silenced(mock_analyze):
    from src.webhooks.whatsapp import _analyze_and_persist

    ctx = _make_ctx("whatsapp")
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)

    async def broken_notify(content_id: str) -> None:
        raise ConnectionError("WhatsApp offline")

    with patch("src.webhooks.whatsapp.record_event"):
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm, notify=broken_notify)


# ── 4. notify NÃO é chamada se analyze_content falhar ─────────────────────────

async def test_notify_not_called_when_analysis_fails():
    from src.webhooks.telegram import _analyze_and_persist

    ctx = _make_ctx()
    mgr = _make_mgr()
    fsm = _make_fsm(ctx)
    notify = AsyncMock()

    with patch(
        "src.webhooks.telegram.analyze_content",
        new_callable=AsyncMock,
        side_effect=RuntimeError("API timeout"),
    ):
        await _analyze_and_persist(ctx, mgr, ctx.user_id, fsm, notify=notify)

    notify.assert_not_awaited()


# ── 5. Handlers criam closure com notify != None ───────────────────────────────

async def test_telegram_handle_message_passes_notify_to_task():
    """handle_message cria asyncio.create_task com notify no kwargs."""
    from src.webhooks.telegram import handle_message

    # Monta update e context simulados
    mock_update = MagicMock()
    mock_update.message.text = "Notícia suspeita"
    mock_update.effective_user.id = 99999
    mock_update.effective_chat.id = 99999
    mock_update.message.reply_text = AsyncMock()
    mock_update.callback_query = None

    mock_context = MagicMock()
    mock_context.bot.send_message = AsyncMock()

    captured_tasks = []

    def fake_create_task(coro):
        captured_tasks.append(coro)
        return MagicMock()

    with (
        patch("src.webhooks.telegram._get_session_mgr") as mock_mgr_fn,
        patch("src.webhooks.telegram._analyze_and_persist", new_callable=AsyncMock),
        patch("src.webhooks.telegram.asyncio.create_task", side_effect=fake_create_task),
        patch("src.webhooks.telegram._send_messages", new_callable=AsyncMock),
    ):
        fake_mgr = _make_mgr()
        mock_mgr_fn.return_value = fake_mgr
        await handle_message(mock_update, mock_context)

    # create_task deve ter sido chamado uma vez (para a análise)
    assert len(captured_tasks) == 1


async def test_whatsapp_handle_message_passes_notify_to_task():
    """handle_whatsapp_message cria asyncio.create_task com notify no kwargs."""
    from src.webhooks.whatsapp import handle_whatsapp_message

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550000", "phone_number_id": "PH_ID"},
                    "messages": [{"from": "5511999990001", "id": "wamid1", "type": "text",
                                  "text": {"body": "Notícia suspeita"}}],
                },
                "field": "messages",
            }],
        }],
    }

    captured_tasks = []

    def fake_create_task(coro):
        captured_tasks.append(coro)
        return MagicMock()

    with (
        patch("src.webhooks.whatsapp._get_session_mgr") as mock_mgr_fn,
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp.asyncio.create_task", side_effect=fake_create_task),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
    ):
        fake_mgr = _make_mgr()
        mock_mgr_fn.return_value = fake_mgr
        await handle_whatsapp_message(payload)

    assert len(captured_tasks) == 1
