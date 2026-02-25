"""
test_webhook.py — Testes do FastAPI Gateway (Micro-Batch 2.5)

Usa TestClient sem lifespan para evitar conexão real com o Telegram.
O _telegram_app é injetado diretamente como AsyncMock.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

import src.main as main_module
from src.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_state():
    """Garante que _telegram_app e WEBHOOK_SECRET são limpos entre testes."""
    saved_secret = os.environ.pop("WEBHOOK_SECRET", None)
    main_module._telegram_app = None
    yield
    main_module._telegram_app = None
    if saved_secret:
        os.environ["WEBHOOK_SECRET"] = saved_secret
    else:
        os.environ.pop("WEBHOOK_SECRET", None)


@pytest.fixture
def mock_tg_app():
    mock = AsyncMock()
    mock.bot = MagicMock()
    return mock


@pytest.fixture
def client():
    """TestClient sem lifespan — _telegram_app precisa ser injetado manualmente."""
    return TestClient(app, raise_server_exceptions=False)


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "mentor-digital-bot"


# ── /webhook/telegram — sem app inicializada ──────────────────────────────────

def test_webhook_returns_503_when_app_not_initialized(client):
    response = client.post("/webhook/telegram", json={"update_id": 1})
    assert response.status_code == 503


# ── /webhook/telegram — validação de secret ──────────────────────────────────

def test_webhook_returns_403_with_wrong_secret(client, mock_tg_app):
    main_module._telegram_app = mock_tg_app
    os.environ["WEBHOOK_SECRET"] = "correct-secret"

    response = client.post(
        "/webhook/telegram",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )
    assert response.status_code == 403


def test_webhook_returns_403_when_secret_missing_from_header(client, mock_tg_app):
    main_module._telegram_app = mock_tg_app
    os.environ["WEBHOOK_SECRET"] = "required-secret"

    response = client.post("/webhook/telegram", json={"update_id": 1})
    assert response.status_code == 403


def test_webhook_accepts_correct_secret(client, mock_tg_app):
    main_module._telegram_app = mock_tg_app
    os.environ["WEBHOOK_SECRET"] = "my-secret"

    with patch("src.main.Update.de_json", return_value=MagicMock()):
        response = client.post(
            "/webhook/telegram",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "my-secret"},
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}


# ── /webhook/telegram — sem secret configurado ───────────────────────────────

def test_webhook_works_without_webhook_secret(client, mock_tg_app):
    """Se WEBHOOK_SECRET não está configurado, qualquer request é aceito."""
    main_module._telegram_app = mock_tg_app

    with patch("src.main.Update.de_json", return_value=MagicMock()):
        response = client.post("/webhook/telegram", json={"update_id": 1})

    assert response.status_code == 200


# ── /webhook/telegram — dispatch do update ───────────────────────────────────

def test_webhook_calls_process_update(client, mock_tg_app):
    """Verifica que process_update é chamado com o update correto."""
    main_module._telegram_app = mock_tg_app
    fake_update = MagicMock()

    with patch("src.main.Update.de_json", return_value=fake_update):
        client.post("/webhook/telegram", json={"update_id": 42})

    mock_tg_app.process_update.assert_called_once_with(fake_update)


def test_webhook_passes_json_body_to_de_json(client, mock_tg_app):
    """Verifica que o corpo JSON é passado para Update.de_json."""
    main_module._telegram_app = mock_tg_app
    payload = {"update_id": 99, "message": {"text": "oi"}}

    with patch("src.main.Update.de_json", return_value=MagicMock()) as mock_de_json:
        client.post("/webhook/telegram", json=payload)

    args = mock_de_json.call_args
    assert args[0][0] == payload           # primeiro arg = dados do body
    assert args[0][1] == mock_tg_app.bot   # segundo arg = bot instance
