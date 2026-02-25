import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM


def make_fsm():
    ctx = ConversationContext(user_id="test", platform="terminal")
    return QuestioningFSM(ctx), ctx


def test_fsm_starts_in_awaiting_content():
    fsm, _ = make_fsm()
    assert fsm.state == "awaiting_content"


def test_fsm_transitions_to_greeting_on_content():
    fsm, _ = make_fsm()
    response = fsm.process_input("Olha essa notícia sobre saúde")
    assert fsm.state == "greeting"
    assert len(response["messages"]) >= 1
    assert "options" in response["messages"][-1]


def test_fsm_transitions_based_on_option_selection():
    fsm, ctx = make_fsm()
    fsm.process_input("Uma notícia qualquer")  # → greeting
    fsm.process_input("inform")                # → exploring_inform
    assert fsm.state == "exploring_inform"
    assert ctx.motivation == "inform"


def test_fsm_reaches_closing():
    fsm, _ = make_fsm()
    fsm.process_input("notícia")         # → greeting
    fsm.process_input("inform")          # → exploring_inform
    fsm.process_input("trust_source")   # → deepening_trust
    fsm.process_input("always_right")   # → closing
    assert fsm.state == "closing"


def test_fsm_records_final_decision():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    fsm.process_input("always_right")
    fsm.process_input("no_changed_mind")  # → feedback_not_share
    assert ctx.final_decision == "not_share"


def test_fsm_records_final_decision_investigate():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    fsm.process_input("always_right")
    fsm.process_input("want_deeper")
    assert ctx.final_decision == "investigate"


def test_fsm_handles_invalid_input():
    fsm, _ = make_fsm()
    fsm.process_input("notícia")  # → greeting
    response = fsm.process_input("xyzzy_nonsense")
    assert fsm.state == "greeting"  # Should NOT advance
    assert "escolher" in response["messages"][0]["body"].lower()


def test_fsm_interaction_count_increments():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")
    assert ctx.interaction_count == 1
    fsm.process_input("inform")
    assert ctx.interaction_count == 2


def test_fsm_records_motivation_and_emotion():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")  # → greeting
    fsm.process_input("alert")    # → exploring_alert
    assert ctx.motivation == "alert"
    fsm.process_input("fear")     # → deepening_fear
    assert ctx.emotion == "fear"


def test_fsm_numeric_input_works():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")  # → greeting
    fsm.process_input("1")        # → exploring_inform (option 1 = inform)
    assert fsm.state == "exploring_inform"
    assert ctx.motivation == "inform"


def test_fsm_reflection_answers_recorded():
    fsm, ctx = make_fsm()
    fsm.process_input("notícia")
    fsm.process_input("inform")
    fsm.process_input("trust_source")
    assert "inform" in ctx.reflection_answers
    assert "trust_source" in ctx.reflection_answers


def test_fsm_auto_advance_no_options_state():
    """States without options (deepening_unknown_source) auto-advance on next input."""
    fsm, _ = make_fsm()
    fsm.process_input("notícia")         # → greeting
    fsm.process_input("inform")          # → exploring_inform
    fsm.process_input("unknown_source")  # → deepening_unknown_source (no options)
    assert fsm.state == "deepening_unknown_source"
    fsm.process_input("qualquer coisa")  # auto-advance → closing
    assert fsm.state == "closing"


def test_fsm_greeting_response_has_three_messages():
    """Greeting sends: ack (text) + transition (text) + motivation list."""
    fsm, _ = make_fsm()
    response = fsm.process_input("uma notícia")
    assert len(response["messages"]) == 3
    assert response["messages"][0]["type"] == "text"   # ack dinâmico
    assert response["messages"][1]["type"] == "text"   # mensagem de transição
    assert response["messages"][2]["type"] == "list"   # opções de motivação


def test_fsm_link_content_type_shows_link_ack():
    """Input com URL gera ack de link."""
    fsm, ctx = make_fsm()
    response = fsm.process_input("https://exemplo.com/noticia", content_type="link")
    assert ctx.content_type == "link"
    ack_body = response["messages"][0]["body"]
    assert "🔗" in ack_body or "link" in ack_body.lower()


def test_fsm_image_content_type_stored():
    """Tipo de mídia é armazenado no contexto."""
    fsm, ctx = make_fsm()
    fsm.process_input("[imagem]", content_type="image")
    assert ctx.content_type == "image"
