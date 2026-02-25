import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import ConversationContext


def test_conversation_context_creation():
    ctx = ConversationContext(user_id="abc123", platform="telegram")
    assert ctx.user_id == "abc123"
    assert ctx.platform == "telegram"
    assert ctx.interaction_count == 0
    assert ctx.reflection_answers == []
    assert ctx.final_decision == ""
    assert ctx.content_id != ""  # UUID gerado automaticamente


def test_conversation_context_defaults():
    ctx = ConversationContext(user_id="xyz", platform="terminal")
    assert ctx.content_type == ""
    assert ctx.content_raw == ""
    assert ctx.motivation == ""
    assert ctx.emotion == ""
    assert ctx.source_trust == ""
    assert ctx.analysis_results == {}
    assert ctx.started_at != ""
    assert ctx.last_interaction_at != ""


def test_conversation_context_serialization():
    ctx = ConversationContext(user_id="abc123", platform="whatsapp")
    ctx.motivation = "inform"
    ctx.interaction_count = 2
    ctx.reflection_answers = ["trust_source", "always_right"]

    json_str = ctx.to_json()
    restored = ConversationContext.from_json(json_str)

    assert restored.motivation == "inform"
    assert restored.user_id == "abc123"
    assert restored.platform == "whatsapp"
    assert restored.interaction_count == 2
    assert restored.reflection_answers == ["trust_source", "always_right"]


def test_content_id_is_unique():
    ctx1 = ConversationContext(user_id="u1", platform="telegram")
    ctx2 = ConversationContext(user_id="u2", platform="telegram")
    assert ctx1.content_id != ctx2.content_id


def test_json_roundtrip_preserves_all_fields():
    ctx = ConversationContext(user_id="test", platform="terminal")
    ctx.content_type = "link"
    ctx.content_raw = "https://example.com"
    ctx.final_decision = "not_share"
    ctx.analysis_results = {"fake_score": 0.87}

    restored = ConversationContext.from_json(ctx.to_json())

    assert restored.content_type == "link"
    assert restored.content_raw == "https://example.com"
    assert restored.final_decision == "not_share"
    assert restored.analysis_results == {"fake_score": 0.87}
