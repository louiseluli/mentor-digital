import os
import yaml
from datetime import datetime, UTC

from src.models import ConversationContext
from src.content_detector import get_acknowledgment

FLOW_PATH = os.path.join(os.path.dirname(__file__), "flows", "questioning.yaml")

TERMINAL_STATES = frozenset({
    "closing", "feedback_share", "feedback_not_share", "feedback_investigate", "end"
})
FALLBACK_MESSAGE = "Desculpe, não entendi. Pode escolher uma das opções acima? 😊"
MAX_INTERACTIONS = 8


class QuestioningFSM:
    """Motor de estados para o fluxo de questionamento do Mentor Digital."""

    def __init__(self, context: ConversationContext, nlp_data: dict | None = None):
        self.context = context
        self.nlp_data = nlp_data
        self.state = "awaiting_content"
        with open(FLOW_PATH, encoding="utf-8") as f:
            self._flow = yaml.safe_load(f)["flow"]

    @staticmethod
    def _nlp_intro(nlp_data: dict) -> str:
        """Gera mensagem educativa com os sinais NLP detectados no texto."""
        signals = []
        urgency = nlp_data.get("urgency", {})
        manipulation = nlp_data.get("manipulation", {})
        claim = nlp_data.get("claim", {})

        if urgency.get("score", 0) >= 0.5:
            evidence = urgency.get("evidence", [])
            hint = f" — \"{evidence[0]}\"" if evidence else ""
            signals.append(f"🚨 Linguagem de urgência{hint}: cria pressão para agir sem pensar")

        if manipulation.get("score", 0) >= 0.5:
            evidence = manipulation.get("evidence", [])
            hint = f" — \"{evidence[0]}\"" if evidence else ""
            signals.append(f"⚠️ Apelo emocional forte{hint}: pode estar tentando influenciar sua reação")

        if claim.get("score", 0) >= 0.5:
            signals.append("📊 Afirmações verificáveis: números, estatísticas ou autoridades citadas")

        if not signals:
            return "✅ Linguagem relativamente neutra — mas sempre vale checar a fonte antes de compartilhar."

        intro = "Analisando este texto, percebi:\n" + "\n".join(f"• {s}" for s in signals)
        return intro

    def process_input(self, user_input: str, content_type: str = "text") -> dict:
        self.context.interaction_count += 1
        self.context.last_interaction_at = datetime.now(UTC).isoformat()

        # Safety net: force closing if over interaction limit
        if (self.context.interaction_count > MAX_INTERACTIONS
                and self.state not in TERMINAL_STATES):
            self.state = "closing"
            return self._build_response("closing")

        if self.state == "awaiting_content":
            return self._handle_awaiting_content(user_input, content_type)

        return self._handle_yaml_state(user_input)

    # ── Private handlers ────────────────────────────────────────────────────

    def _handle_awaiting_content(self, content: str, content_type: str = "text") -> dict:
        self.context.content_raw = content
        self.context.content_type = content_type
        self.state = "greeting"
        response = self._build_response("greeting")
        # Insere reconhecimento específico ao tipo antes da pergunta de motivação
        ack = {"type": "text", "body": get_acknowledgment(content_type)}
        response["messages"].insert(0, ack)
        # Insere sinais NLP detectados no início (antes do ack) se disponíveis
        if self.nlp_data:
            nlp_msg = {"type": "text", "body": self._nlp_intro(self.nlp_data)}
            response["messages"].insert(0, nlp_msg)
        return response

    def _handle_yaml_state(self, user_input: str) -> dict:
        state_data = self._flow.get(self.state, {})

        # Options can live at top-level or inside follow_up (e.g., greeting)
        options = (
            state_data.get("options")
            or state_data.get("follow_up", {}).get("options", [])
        )

        # No options → auto-advance to next_state (e.g., deepening_unknown_source)
        if not options:
            next_state = state_data.get("next_state")
            if next_state:
                self.state = next_state
                return self._build_response(next_state)
            return {"messages": [], "state": self.state}

        matched = self._match_option(user_input, options)
        if not matched:
            return {
                "messages": [{"type": "text", "body": FALLBACK_MESSAGE}],
                "state": self.state,
            }

        self._update_context(matched)
        next_state = matched.get("next_state", "end")
        self.state = next_state
        return self._build_response(next_state)

    def _match_option(self, user_input: str, options: list) -> dict | None:
        normalized = user_input.strip().lower()
        for opt in options:
            if opt["id"] == normalized or opt["title"].lower() == normalized:
                return opt
        # Numeric selection for terminal runner ("1", "2", "3"...)
        try:
            idx = int(user_input.strip()) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, TypeError):
            pass
        return None

    def _update_context(self, option: dict) -> None:
        option_id = option["id"]
        if self.state == "greeting":
            self.context.motivation = option_id
        elif self.state == "exploring_inform":
            self.context.source_trust = option_id
        elif self.state == "exploring_alert":
            self.context.emotion = option_id
        elif self.state == "closing":
            self.context.final_decision = {
                "yes_share": "share",
                "no_changed_mind": "not_share",
                "want_deeper": "investigate",
            }.get(option_id, "")
        self.context.reflection_answers.append(option_id)

    def _build_response(self, state_name: str) -> dict:
        if state_name not in self._flow:
            return {"messages": [], "state": state_name}

        state_data = self._flow[state_name]
        messages = []

        if "message" in state_data:
            msg = {"type": "text", "body": state_data["message"]}
            if "options" in state_data:
                msg["type"] = state_data.get("type", "buttons")
                msg["options"] = state_data["options"]
            messages.append(msg)

        if "follow_up" in state_data:
            fu = state_data["follow_up"]
            fu_msg = {"type": fu.get("type", "text"), "body": fu.get("message", "")}
            if "options" in fu:
                fu_msg["options"] = fu["options"]
            messages.append(fu_msg)

        return {"messages": messages, "state": state_name}
