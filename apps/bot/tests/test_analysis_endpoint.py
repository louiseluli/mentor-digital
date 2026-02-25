"""
test_analysis_endpoint.py — Testes do endpoint GET /analysis/{content_id} (Micro-Batch 4.0)

Usa TestClient sem lifespan. O _session_mgr é injetado como SessionManager
respaldado por fakeredis — sem Redis real, sem Telegram.
"""

import sys
import os
import pytest
import fakeredis
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PSEUDONYMIZATION_PEPPER", "test_pepper_operacional")
os.environ.setdefault("ANALYTICS_PEPPER", "test_pepper_analytics")

import src.main as main_module
from src.main import app
from src.session_manager import SessionManager


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_ID = "a1b2c3d4-1234-5678-abcd-ef0123456789"

SAMPLE_ANALYSIS = {
    "analyzed_at": "2024-01-15T12:00:00Z",
    "query": "Vacina causa autismo",
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
        "word_count": 3,
        "caps_ratio": 0.0,
        "error": "",
        "urgency": {"score": 0.1, "evidence": []},
        "claim": {"score": 0.2, "evidence": ["autoridade: organismo"]},
        "manipulation": {"score": 0.0, "evidence": []},
    },
}


@pytest.fixture(autouse=True)
def reset_main_state():
    """Isola _session_mgr e _telegram_app entre testes."""
    saved_mgr = main_module._session_mgr
    saved_tg = main_module._telegram_app
    main_module._session_mgr = None
    main_module._telegram_app = None
    yield
    main_module._session_mgr = saved_mgr
    main_module._telegram_app = saved_tg


@pytest.fixture
def fake_mgr():
    return SessionManager(fakeredis.FakeRedis(), ttl=60)


@pytest.fixture
def client(fake_mgr):
    """TestClient com SessionManager fake injetado."""
    main_module._session_mgr = fake_mgr
    return TestClient(app, raise_server_exceptions=False)


# ── GET /analysis/{content_id} — 404 ─────────────────────────────────────────

def test_get_analysis_404_when_not_found(client):
    response = client.get(f"/analysis/{SAMPLE_ID}")
    assert response.status_code == 404


def test_get_analysis_404_detail_message(client):
    response = client.get(f"/analysis/{SAMPLE_ID}")
    assert "detail" in response.json()


def test_get_analysis_404_for_unknown_id(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    other_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/analysis/{other_id}")
    assert response.status_code == 404


# ── GET /analysis/{content_id} — 200 ─────────────────────────────────────────

def test_get_analysis_200_when_found(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    response = client.get(f"/analysis/{SAMPLE_ID}")
    assert response.status_code == 200


def test_get_analysis_returns_json(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    response = client.get(f"/analysis/{SAMPLE_ID}")
    assert "application/json" in response.headers["content-type"]


def test_get_analysis_returns_query(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    assert data["query"] == "Vacina causa autismo"


def test_get_analysis_returns_analyzed_at(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    assert "analyzed_at" in data


def test_get_analysis_returns_fact_check(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    assert "fact_check" in data
    assert "pt" in data["fact_check"]
    assert "en" in data["fact_check"]


def test_get_analysis_returns_gdelt(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    assert "gdelt" in data
    assert "por" in data["gdelt"]
    assert "en" in data["gdelt"]


def test_get_analysis_returns_nlp(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    assert "nlp" in data
    nlp = data["nlp"]
    assert "language" in nlp
    assert "urgency" in nlp
    assert "claim" in nlp
    assert "manipulation" in nlp


def test_get_analysis_nlp_scores_are_numbers(client, fake_mgr):
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    data = client.get(f"/analysis/{SAMPLE_ID}").json()
    nlp = data["nlp"]
    assert isinstance(nlp["urgency"]["score"], (int, float))
    assert isinstance(nlp["claim"]["score"], (int, float))
    assert isinstance(nlp["manipulation"]["score"], (int, float))


# ── Isolamento entre content_ids ──────────────────────────────────────────────

def test_different_content_ids_are_isolated(client, fake_mgr):
    id_a = "aaaaaaaa-0000-0000-0000-000000000001"
    id_b = "bbbbbbbb-0000-0000-0000-000000000002"
    fake_mgr.save_analysis(id_a, {**SAMPLE_ANALYSIS, "query": "query A"})
    fake_mgr.save_analysis(id_b, {**SAMPLE_ANALYSIS, "query": "query B"})

    assert client.get(f"/analysis/{id_a}").json()["query"] == "query A"
    assert client.get(f"/analysis/{id_b}").json()["query"] == "query B"


# ── /health ainda funciona ────────────────────────────────────────────────────

def test_health_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── CORS headers ──────────────────────────────────────────────────────────────

def test_cors_header_present_on_analysis_response(client, fake_mgr):
    """Plataforma web pode consumir a API (CORS configurado)."""
    fake_mgr.save_analysis(SAMPLE_ID, SAMPLE_ANALYSIS)
    response = client.get(
        f"/analysis/{SAMPLE_ID}",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
