"""
test_session_manager.py — Testes unitários do SessionManager (Micro-Batch 2.3)

Usa fakeredis para simular Redis sem servidor real.
"""

import sys
import os
import pytest
import fakeredis

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["PSEUDONYMIZATION_PEPPER"] = "test_pepper_operacional"
os.environ["ANALYTICS_PEPPER"] = "test_pepper_analytics"

from src.session_manager import SessionManager, KEY_PREFIX, ANALYSIS_KEY_PREFIX
from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mgr() -> SessionManager:
    """SessionManager com Redis falso e TTL curto para testes."""
    fake_r = fakeredis.FakeRedis()
    return SessionManager(fake_r, ttl=60)


def _advance_to_greeting(mgr: SessionManager, user_id: str) -> QuestioningFSM:
    """Helper: avança FSM até o estado greeting e salva sessão."""
    fsm = mgr.get_or_create(user_id)
    fsm.process_input("notícia de teste")   # awaiting_content → greeting
    mgr.save(user_id, fsm)
    return fsm


# ── get_or_create ─────────────────────────────────────────────────────────────

def test_get_or_create_new_user_starts_at_awaiting_content(mgr):
    fsm = mgr.get_or_create("novo_user")
    assert fsm.state == "awaiting_content"


def test_get_or_create_new_user_has_correct_platform(mgr):
    fsm = mgr.get_or_create("user_plat", platform="telegram")
    assert fsm.context.platform == "telegram"


def test_get_or_create_restores_state_after_save(mgr):
    _advance_to_greeting(mgr, "user_restore")
    restored = mgr.get_or_create("user_restore")
    assert restored.state == "greeting"


def test_get_or_create_restores_context_fields(mgr):
    fsm = mgr.get_or_create("user_ctx")
    fsm.process_input("conteúdo específico")
    mgr.save("user_ctx", fsm)

    restored = mgr.get_or_create("user_ctx")
    assert restored.context.content_raw == "conteúdo específico"
    assert restored.context.interaction_count == 1


def test_get_or_create_after_delete_creates_fresh(mgr):
    _advance_to_greeting(mgr, "user_fresh")
    mgr.delete("user_fresh")
    fresh = mgr.get_or_create("user_fresh")
    assert fresh.state == "awaiting_content"


# ── save ──────────────────────────────────────────────────────────────────────

def test_save_marks_session_as_existing(mgr):
    fsm = mgr.get_or_create("user_exists")
    fsm.process_input("algo")
    mgr.save("user_exists", fsm)
    assert mgr.exists("user_exists")


def test_save_preserves_state_across_multiple_transitions(mgr):
    fsm = mgr.get_or_create("user_multi")
    fsm.process_input("texto")          # → greeting
    fsm.process_input("inform")         # → exploring_inform
    mgr.save("user_multi", fsm)

    restored = mgr.get_or_create("user_multi")
    assert restored.state == "exploring_inform"
    assert restored.context.motivation == "inform"


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_removes_session(mgr):
    _advance_to_greeting(mgr, "user_del")
    assert mgr.exists("user_del")
    mgr.delete("user_del")
    assert not mgr.exists("user_del")


def test_delete_nonexistent_user_does_not_raise(mgr):
    mgr.delete("fantasma")  # não deve lançar exceção


# ── exists ────────────────────────────────────────────────────────────────────

def test_exists_returns_false_for_unknown_user(mgr):
    assert not mgr.exists("desconhecido")


def test_exists_returns_true_after_save(mgr):
    fsm = mgr.get_or_create("user_ex")
    fsm.process_input("x")
    mgr.save("user_ex", fsm)
    assert mgr.exists("user_ex")


# ── Isolamento entre usuários ─────────────────────────────────────────────────

def test_sessions_are_isolated_per_user(mgr):
    fsm_a = mgr.get_or_create("alice")
    fsm_a.process_input("conteúdo da Alice")
    mgr.save("alice", fsm_a)

    fsm_b = mgr.get_or_create("bob")
    fsm_b.process_input("conteúdo do Bob")
    mgr.save("bob", fsm_b)

    alice = mgr.get_or_create("alice")
    bob = mgr.get_or_create("bob")
    assert alice.context.content_raw == "conteúdo da Alice"
    assert bob.context.content_raw == "conteúdo do Bob"


# ── Prefixo de chave ──────────────────────────────────────────────────────────

def test_key_prefix_is_used(mgr):
    """Garante que as chaves no Redis usam o prefixo correto."""
    fsm = mgr.get_or_create("chave_user")
    fsm.process_input("x")
    mgr.save("chave_user", fsm)
    # Acessa o cliente interno para verificar a chave
    assert mgr._r.exists(f"{KEY_PREFIX}chave_user")


# ── save_analysis / get_analysis ──────────────────────────────────────────────

def test_save_analysis_stores_data(mgr):
    mgr.save_analysis("uuid-001", {"query": "vacina", "fact_check": {}})
    assert mgr._r.exists(f"{ANALYSIS_KEY_PREFIX}uuid-001")


def test_get_analysis_returns_none_when_not_found(mgr):
    assert mgr.get_analysis("nao-existe") is None


def test_save_and_get_analysis_roundtrip(mgr):
    data = {"query": "terra plana", "nlp": {"score": 0.9}}
    mgr.save_analysis("uuid-rt", data)
    result = mgr.get_analysis("uuid-rt")
    assert result == data


def test_get_analysis_returns_dict(mgr):
    mgr.save_analysis("uuid-dict", {"key": "value"})
    assert isinstance(mgr.get_analysis("uuid-dict"), dict)


def test_analysis_key_does_not_collide_with_session_key(mgr):
    """Chave de análise e chave de sessão são distintas no Redis."""
    fsm = mgr.get_or_create("user_colide")
    fsm.process_input("texto")
    mgr.save("user_colide", fsm)
    mgr.save_analysis("user_colide", {"query": "homônimo"})

    # Sessão continua intacta
    assert mgr.exists("user_colide")
    # Análise retorna dado correto
    assert mgr.get_analysis("user_colide")["query"] == "homônimo"


def test_analysis_prefix_is_correct(mgr):
    mgr.save_analysis("check-prefix", {"x": 1})
    assert mgr._r.exists(f"{ANALYSIS_KEY_PREFIX}check-prefix")
    assert not mgr._r.exists(f"{KEY_PREFIX}check-prefix")
