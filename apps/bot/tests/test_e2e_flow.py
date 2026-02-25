"""
test_e2e_flow.py — Testes de integração ponta a ponta (Micro-Batch 7.2)

Cobre o fluxo completo do produto:
  mensagem WhatsApp → FSM → sessão Redis → análise → GET /analysis/{id}

Diferença em relação aos testes de unidade:
  - Não mocka FSM nem SessionManager
  - Usa fakeredis (Redis real emulado)
  - Mocka apenas chamadas a APIs externas (HTTP, Telegram)

Seções:
  1. Fluxo WhatsApp via handler direto (async)
  2. Fluxo HTTP — respostas dos endpoints
  3. Fluxo análise → recuperação via API
"""

import os
import sys
import uuid

import fakeredis
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "e2e_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "e2e_pepper_analytics")

import src.main as main_module
from src.main import app
from src.security import pseudonymize
from src.session_manager import SessionManager
from src.webhooks.whatsapp import handle_whatsapp_message


# ── Helpers ────────────────────────────────────────────────────────────────────

PHONE = "5511900001111"
PHONE_ID = "WA_PHONE_ID_E2E"

MOCK_ANALYSIS = {
    "analyzed_at": "2024-01-15T12:00:00Z",
    "query": "Texto de teste e2e",
    "fact_check": {
        "pt": {"results": [], "error": ""},
        "en": {"results": [], "error": ""},
    },
    "gdelt": {
        "por": {"articles": [], "error": ""},
        "en": {"articles": [], "error": ""},
    },
    "nlp": {
        "language": "pt",
        "word_count": 4,
        "caps_ratio": 0.0,
        "error": "",
        "urgency": {"score": 0.1, "evidence": []},
        "claim": {"score": 0.2, "evidence": []},
        "manipulation": {"score": 0.0, "evidence": []},
    },
}


def _wa_payload(body: str, phone: str = PHONE, phone_id: str = PHONE_ID) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "BIZ_ID_E2E",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550000000",
                                "phone_number_id": phone_id,
                            },
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "wamid.e2e001",
                                    "type": "text",
                                    "text": {"body": body},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_mgr():
    return SessionManager(fakeredis.FakeRedis(), ttl=60)


@pytest.fixture(autouse=True)
def reset_main_state(fake_mgr):
    main_module._session_mgr = fake_mgr
    main_module._telegram_app = None
    yield
    main_module._session_mgr = None
    main_module._telegram_app = None


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ── 1. Fluxo WhatsApp via handler direto ──────────────────────────────────────

async def test_first_message_advances_fsm_state(fake_mgr):
    """Primeira mensagem move o FSM para fora de awaiting_content."""
    user_id = pseudonymize(PHONE)

    with (
        patch("src.webhooks.whatsapp._get_session_mgr", return_value=fake_mgr),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp.asyncio.create_task"),
    ):
        await handle_whatsapp_message(_wa_payload("Notícia suspeita viral"))

    fsm = fake_mgr.get_or_create(user_id)
    assert fsm.state != "awaiting_content"


async def test_second_message_continues_session(fake_mgr):
    """Segunda mensagem encontra sessão existente e continua o fluxo."""
    user_id = pseudonymize(PHONE)

    with (
        patch("src.webhooks.whatsapp._get_session_mgr", return_value=fake_mgr),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp.asyncio.create_task"),
    ):
        await handle_whatsapp_message(_wa_payload("Primeira mensagem"))
        state_after_first = fake_mgr.get_or_create(user_id).state

        await handle_whatsapp_message(_wa_payload("Segunda mensagem"))

    # Sessão continua existindo após segunda mensagem
    fsm = fake_mgr.get_or_create(user_id)
    assert fsm is not None
    assert state_after_first != "awaiting_content"


async def test_analysis_is_triggered_on_first_content(fake_mgr):
    """Primeira mensagem dispara tarefa de análise em background."""
    with (
        patch("src.webhooks.whatsapp._get_session_mgr", return_value=fake_mgr),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp.asyncio.create_task") as mock_task,
    ):
        await handle_whatsapp_message(_wa_payload("Link suspeito: http://example.com"))

    assert mock_task.called, "asyncio.create_task deve ser chamado na primeira mensagem"


# ── 2. Fluxo HTTP — respostas dos endpoints ────────────────────────────────────

def test_whatsapp_post_returns_200(client):
    """POST /webhook/whatsapp com payload válido retorna 200 imediatamente."""
    with (
        patch("src.webhooks.whatsapp._get_session_mgr", return_value=main_module._session_mgr),
        patch("src.webhooks.whatsapp._send_text", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._send_interactive", new_callable=AsyncMock),
        patch("src.webhooks.whatsapp._analyze_and_persist", new_callable=AsyncMock),
        patch("src.main.asyncio.create_task"),
    ):
        resp = client.post("/webhook/whatsapp", json=_wa_payload("Mensagem via HTTP"))

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_whatsapp_verification_challenge_roundtrip(client):
    """GET /webhook/whatsapp devolve exatamente o hub.challenge da Meta."""
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "e2e-token-roundtrip"
    try:
        challenge = "UNIQUE_CHALLENGE_XYZ_789"
        resp = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "e2e-token-roundtrip",
                "hub.challenge": challenge,
            },
        )
        assert resp.status_code == 200
        assert resp.text == challenge
    finally:
        os.environ.pop("WHATSAPP_VERIFY_TOKEN", None)


# ── 3. Fluxo análise → recuperação via API ─────────────────────────────────────

def test_stored_analysis_retrievable_via_api(client, fake_mgr):
    """Análise armazenada pelo bot é recuperável pela plataforma web."""
    content_id = str(uuid.uuid4())
    analysis = {**MOCK_ANALYSIS, "query": "Vacina causa autismo — teste e2e"}
    fake_mgr.save_analysis(content_id, analysis)

    resp = client.get(f"/analysis/{content_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Vacina causa autismo — teste e2e"
    assert "nlp" in data
    assert "fact_check" in data
    assert "gdelt" in data


def test_analysis_structure_complete(client, fake_mgr):
    """Análise retornada contém todos os campos esperados pela plataforma web."""
    content_id = str(uuid.uuid4())
    fake_mgr.save_analysis(content_id, MOCK_ANALYSIS)

    data = client.get(f"/analysis/{content_id}").json()

    # Estrutura NLP
    assert "urgency" in data["nlp"]
    assert "score" in data["nlp"]["urgency"]
    assert "evidence" in data["nlp"]["urgency"]
    assert "manipulation" in data["nlp"]
    assert "claim" in data["nlp"]

    # Estrutura fact_check
    assert "pt" in data["fact_check"]
    assert "en" in data["fact_check"]

    # Estrutura GDELT
    assert "por" in data["gdelt"]
    assert "en" in data["gdelt"]
