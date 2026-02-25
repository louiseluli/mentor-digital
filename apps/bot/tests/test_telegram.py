"""
test_telegram.py — Testes unitários para o handler Telegram (Micro-Batch 2.2/2.3)

Testa helpers puros e handlers com mocks do Telegram + fakeredis.
"""

import sys
import os
import pytest
import fakeredis
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["PSEUDONYMIZATION_PEPPER"] = "test_pepper_operacional"
os.environ["ANALYTICS_PEPPER"] = "test_pepper_analytics"
os.environ["WEB_PLATFORM_URL"] = "http://localhost:3000"

from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM
from src.session_manager import SessionManager
from src.webhooks.telegram import (
    _fill_placeholders,
    _collect_messages,
    _build_keyboard,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def no_background_tasks():
    """Substitui _analyze_and_persist por AsyncMock nos testes unitários.

    A análise de conteúdo (fire-and-forget) é testada separadamente em
    test_analysis_service.py. Aqui queremos apenas testar o fluxo do handler.
    O AsyncMock resolve imediatamente → sem tasks pendentes ao fechar o loop.
    """
    with patch(
        "src.webhooks.telegram._analyze_and_persist",
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture
def fake_mgr() -> SessionManager:
    """SessionManager com Redis falso — injetado nos handlers via patch."""
    return SessionManager(fakeredis.FakeRedis(), ttl=60)


@pytest.fixture
def patch_mgr(fake_mgr):
    """Substitui o singleton _get_session_mgr pelo fake durante o teste."""
    with patch("src.webhooks.telegram._get_session_mgr", return_value=fake_mgr):
        yield fake_mgr


def _make_fsm(user_id: str = "test_user") -> QuestioningFSM:
    ctx = ConversationContext(user_id=user_id, platform="telegram")
    return QuestioningFSM(ctx)


# ── _fill_placeholders ────────────────────────────────────────────────────────

def test_fill_placeholders_replaces_web_url():
    ctx = ConversationContext(user_id="u1", platform="telegram")
    result = _fill_placeholders("Acesse {web_platform_url}", ctx)
    assert result == "Acesse http://localhost:3000"


def test_fill_placeholders_replaces_content_id():
    ctx = ConversationContext(user_id="u1", platform="telegram")
    result = _fill_placeholders("ID: {content_id}", ctx)
    assert result == f"ID: {ctx.content_id}"


def test_fill_placeholders_replaces_both():
    ctx = ConversationContext(user_id="u1", platform="telegram")
    text = "{web_platform_url}/analise/{content_id}"
    result = _fill_placeholders(text, ctx)
    assert result == f"http://localhost:3000/analise/{ctx.content_id}"


def test_fill_placeholders_no_placeholders():
    ctx = ConversationContext(user_id="u1", platform="telegram")
    text = "Texto sem substituições."
    assert _fill_placeholders(text, ctx) == text


# ── _collect_messages ─────────────────────────────────────────────────────────

def test_collect_messages_returns_initial_when_state_has_options():
    fsm = _make_fsm()
    response = fsm.process_input("notícia qualquer")    # estado: greeting (tem opções)
    messages = _collect_messages(fsm, response)
    assert len(messages) >= 1
    has_options = any(msg.get("options") for msg in messages)
    assert has_options


def test_collect_messages_auto_advances_deepening_unknown_source():
    """deepening_unknown_source não tem opções → deve avançar para closing."""
    fsm = _make_fsm()
    fsm.process_input("conteúdo de teste")
    fsm.process_input("inform")

    response = fsm.process_input("unknown_source")
    messages = _collect_messages(fsm, response)

    assert len(messages) >= 2
    assert fsm.state == "closing"


def test_collect_messages_auto_advances_feedback_to_end():
    """feedback_* não tem opções → deve avançar para end."""
    fsm = _make_fsm()
    fsm.process_input("texto")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    fsm.process_input("always_right")

    response = fsm.process_input("no_changed_mind")
    messages = _collect_messages(fsm, response)

    assert len(messages) >= 2
    assert fsm.state == "end"


# ── _build_keyboard ───────────────────────────────────────────────────────────

def test_build_keyboard_creates_one_row_per_option():
    from telegram import InlineKeyboardMarkup
    options = [
        {"id": "a", "title": "Opção A"},
        {"id": "b", "title": "Opção B"},
        {"id": "c", "title": "Opção C"},
    ]
    keyboard = _build_keyboard(options)
    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3


def test_build_keyboard_callback_data_matches_option_id():
    options = [
        {"id": "inform", "title": "Para informar"},
        {"id": "alert",  "title": "Para alertar"},
    ]
    keyboard = _build_keyboard(options)
    ids = [row[0].callback_data for row in keyboard.inline_keyboard]
    assert ids == ["inform", "alert"]


# ── Async handlers ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_handler_deletes_existing_session(patch_mgr):
    from src.webhooks.telegram import start

    # Pré-carrega sessão para garantir que será removida
    fsm = _make_fsm("hashed_user")
    fsm.process_input("old content")
    patch_mgr.save("hashed_user", fsm)
    assert patch_mgr.exists("hashed_user")

    mock_update = MagicMock()
    mock_update.effective_user.id = "12345"
    mock_update.message.reply_text = AsyncMock()

    with patch("src.webhooks.telegram.pseudonymize", return_value="hashed_user"):
        await start(mock_update, MagicMock())

    assert not patch_mgr.exists("hashed_user")
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_sends_greeting_on_first_message(patch_mgr):
    from src.webhooks.telegram import handle_message

    mock_update = MagicMock()
    mock_update.effective_user.id = "99999"
    mock_update.message.text = "Vi essa notícia hoje"
    mock_update.message.reply_text = AsyncMock()
    mock_update.callback_query = None

    with patch("src.webhooks.telegram.pseudonymize", return_value="user_99999"):
        await handle_message(mock_update, MagicMock())

    assert mock_update.message.reply_text.call_count >= 1
    # Sessão deve ter sido salva no Redis
    assert patch_mgr.exists("user_99999")
    assert patch_mgr.get_or_create("user_99999").state == "greeting"


@pytest.mark.asyncio
async def test_handle_callback_transitions_state(patch_mgr):
    from src.webhooks.telegram import handle_callback

    # Configura sessão no estado greeting
    fsm = _make_fsm("cb_user")
    fsm.process_input("conteúdo")
    patch_mgr.save("cb_user", fsm)

    mock_query = MagicMock()
    mock_query.answer = AsyncMock()
    mock_query.data = "inform"
    mock_query.message.reply_text = AsyncMock()

    mock_update = MagicMock()
    mock_update.effective_user.id = "77777"
    mock_update.callback_query = mock_query

    with patch("src.webhooks.telegram.pseudonymize", return_value="cb_user"):
        await handle_callback(mock_update, MagicMock())

    assert patch_mgr.get_or_create("cb_user").state == "exploring_inform"
    mock_query.answer.assert_called_once()
    mock_query.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_handle_message_clears_session_at_end(patch_mgr):
    """Quando o fluxo termina, a sessão deve ser removida do Redis."""
    from src.webhooks.telegram import handle_message

    fsm = _make_fsm("end_user")
    fsm.process_input("texto")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    fsm.process_input("always_right")    # → closing
    patch_mgr.save("end_user", fsm)

    mock_update = MagicMock()
    mock_update.effective_user.id = "00001"
    mock_update.message.text = "no_changed_mind"
    mock_update.message.reply_text = AsyncMock()
    mock_update.callback_query = None

    with patch("src.webhooks.telegram.pseudonymize", return_value="end_user"):
        await handle_message(mock_update, MagicMock())

    assert not patch_mgr.exists("end_user")
