"""
test_whatsapp.py — Testes do webhook WhatsApp Cloud API (Micro-Batch 7.1)

Seções:
  1. _extract_message       — parsing do payload (10 testes)
  2. handle_whatsapp_message — integração FSM + session (6 testes)
  3. Endpoints main.py      — GET/POST /webhook/whatsapp via TestClient (4 testes)
"""

import os
import sys
import asyncio

import fakeredis
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

import src.main as main_module
from src.main import app
from src.security import pseudonymize
from src.session_manager import SessionManager
from src.webhooks.whatsapp import _extract_message, handle_whatsapp_message


# ── Constantes e helpers ───────────────────────────────────────────────────────

PHONE = "5511999990001"
PHONE_ID = "PHONE_NUMBER_ID_123"


def _make_payload(msg: dict, phone_number_id: str = PHONE_ID) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "BUSINESS_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550000000",
                                "phone_number_id": phone_number_id,
                            },
                            "messages": [msg],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def _text_msg(body: str, from_phone: str = PHONE) -> dict:
    return {
        "from": from_phone,
        "id": "wamid.text001",
        "type": "text",
        "text": {"body": body},
    }


def _button_reply(option_id: str, title: str, from_phone: str = PHONE) -> dict:
    return {
        "from": from_phone,
        "id": "wamid.btn001",
        "type": "interactive",
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": option_id, "title": title},
        },
    }


def _list_reply(option_id: str, title: str, from_phone: str = PHONE) -> dict:
    return {
        "from": from_phone,
        "id": "wamid.lst001",
        "type": "interactive",
        "interactive": {
            "type": "list_reply",
            "list_reply": {"id": option_id, "title": title},
        },
    }


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_mgr():
    return SessionManager(fakeredis.FakeRedis(), ttl=60)


@pytest.fixture(autouse=True)
def reset_main_state():
    saved_tg = main_module._telegram_app
    main_module._telegram_app = None
    yield
    main_module._telegram_app = saved_tg


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def patched_wa(fake_mgr):
    """Fixture que isola o handler de dependências externas."""
    with (
        patch("src.webhooks.whatsapp._get_session_mgr", return_value=fake_mgr),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock) as mock_persist,
        patch("src.webhooks.whatsapp.asyncio.create_task") as mock_task,
    ):
        yield {"mgr": fake_mgr, "mock_persist": mock_persist, "mock_task": mock_task}


# ── 1. _extract_message ────────────────────────────────────────────────────────

def test_extract_text_content():
    result = _extract_message(_make_payload(_text_msg("Vacina causa autismo")))
    assert result is not None
    assert result[2] == "Vacina causa autismo"


def test_extract_text_from_phone():
    result = _extract_message(_make_payload(_text_msg("msg", from_phone="5521888880001")))
    assert result is not None
    assert result[0] == "5521888880001"


def test_extract_text_phone_number_id():
    result = _extract_message(_make_payload(_text_msg("msg"), phone_number_id="MY_ID"))
    assert result is not None
    assert result[4] == "MY_ID"


def test_extract_interactive_button_reply():
    result = _extract_message(_make_payload(_button_reply("op_1", "Opção A")))
    assert result is not None
    _, _, content_raw, interaction_id, _ = result
    assert interaction_id == "op_1"
    assert content_raw == "Opção A"


def test_extract_interactive_list_reply():
    result = _extract_message(_make_payload(_list_reply("op_list", "Lista B")))
    assert result is not None
    _, _, content_raw, interaction_id, _ = result
    assert interaction_id == "op_list"
    assert content_raw == "Lista B"


def test_extract_image_with_caption():
    msg = {"from": PHONE, "type": "image", "image": {"caption": "Veja isso!", "id": "imgid"}}
    result = _extract_message(_make_payload(msg))
    assert result is not None
    assert result[2] == "Veja isso!"


def test_extract_image_without_caption():
    msg = {"from": PHONE, "type": "image", "image": {"id": "imgid"}}
    result = _extract_message(_make_payload(msg))
    assert result is not None
    assert result[2] == "[imagem]"


def test_extract_audio():
    msg = {"from": PHONE, "type": "audio", "audio": {"id": "audioid"}}
    result = _extract_message(_make_payload(msg))
    assert result is not None
    assert result[2] == "[áudio]"


def test_extract_returns_none_for_empty_messages():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [], "metadata": {}}}]}],
    }
    assert _extract_message(payload) is None


def test_extract_returns_none_for_malformed_payload():
    assert _extract_message({}) is None
    assert _extract_message({"entry": []}) is None


# ── 2. handle_whatsapp_message ─────────────────────────────────────────────────

async def test_handle_text_message_no_exception(patched_wa):
    """Handler processa mensagem de texto sem levantar exceção."""
    payload = _make_payload(_text_msg("Compartilhar isso?"))
    await handle_whatsapp_message(payload)  # deve retornar sem erro


async def test_handle_text_saves_session(patched_wa):
    """Após processar texto, sessão é persistida no SessionManager."""
    payload = _make_payload(_text_msg("Alerta URGENTE!"))
    await handle_whatsapp_message(payload)
    mgr = patched_wa["mgr"]
    # Sessão deve existir no fakeredis após o handler
    fsm = mgr.get_or_create(pseudonymize(PHONE))
    assert fsm is not None


async def test_handle_first_content_triggers_analysis(patched_wa):
    """Primeiro conteúdo dispara tarefa de análise em background."""
    payload = _make_payload(_text_msg("Nova notícia viral"))
    await handle_whatsapp_message(payload)
    assert patched_wa["mock_task"].called


async def test_handle_interactive_reply_does_not_trigger_analysis(patched_wa):
    """Resposta interativa (botão/lista) NÃO dispara análise."""
    mgr = patched_wa["mgr"]
    # Avança FSM além do estado awaiting_content
    fsm = mgr.get_or_create(pseudonymize(PHONE))
    fsm.process_input("algum conteúdo", "text")
    mgr.save(pseudonymize(PHONE), fsm)

    payload = _make_payload(_button_reply("op_verificar", "Verificar"))
    await handle_whatsapp_message(payload)
    assert not patched_wa["mock_task"].called


async def test_handle_empty_payload_no_exception(patched_wa):
    """Payload vazio é tratado sem exceção."""
    await handle_whatsapp_message({})


async def test_handle_payload_with_no_messages_no_exception(patched_wa):
    """Payload sem mensagens é tratado sem exceção."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [], "metadata": {"phone_number_id": PHONE_ID}}}]}],
    }
    await handle_whatsapp_message(payload)


# ── 3. Endpoints main.py ───────────────────────────────────────────────────────

def test_whatsapp_verify_correct_token(client):
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "meu-token-secreto"
    try:
        resp = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "meu-token-secreto",
                "hub.challenge": "CHALLENGE_STRING_123",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "CHALLENGE_STRING_123"
    finally:
        os.environ.pop("WHATSAPP_VERIFY_TOKEN", None)


def test_whatsapp_verify_wrong_token(client):
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "token-certo"
    try:
        resp = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "token-errado",
                "hub.challenge": "CHALLENGE",
            },
        )
        assert resp.status_code == 403
    finally:
        os.environ.pop("WHATSAPP_VERIFY_TOKEN", None)


def test_whatsapp_post_returns_ok(client):
    with (
        patch("src.webhooks.whatsapp.handle_whatsapp_message", new_callable=AsyncMock),
        patch("src.main.asyncio.create_task"),
    ):
        resp = client.post(
            "/webhook/whatsapp",
            json={"object": "whatsapp_business_account", "entry": []},
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_whatsapp_post_invalid_hmac(client):
    os.environ["WHATSAPP_APP_SECRET"] = "my-app-secret"
    try:
        resp = client.post(
            "/webhook/whatsapp",
            content=b'{"object": "whatsapp_business_account"}',
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalidsignature000",
            },
        )
        assert resp.status_code == 403
    finally:
        os.environ.pop("WHATSAPP_APP_SECRET", None)
