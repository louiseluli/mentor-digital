"""
terminal_runner.py — Simula o fluxo completo do bot no terminal.

Uso: python -m src.terminal_runner
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM

BOT = "🤖"
USER_PROMPT = "\nVocê: "
DIVIDER = "─" * 42
WEB_URL = os.getenv("WEB_PLATFORM_URL", "http://localhost:3000")


def _fill_placeholders(text: str, ctx: ConversationContext) -> str:
    return text.replace("{web_platform_url}", WEB_URL).replace(
        "{content_id}", ctx.content_id
    )


def print_bot(text: str) -> None:
    print(f"\n{BOT} {text}")


def print_options(options: list) -> None:
    print()
    for i, opt in enumerate(options, 1):
        print(f"   [{i}] {opt['title']}")


def _get_current_options(fsm: QuestioningFSM) -> list:
    state_data = fsm._flow.get(fsm.state, {})
    return (
        state_data.get("options")
        or state_data.get("follow_up", {}).get("options", [])
        or []
    )


def render_response(response: dict, ctx: ConversationContext) -> None:
    for msg in response.get("messages", []):
        body = _fill_placeholders(msg.get("body", ""), ctx)
        options = msg.get("options", [])
        if body:
            time.sleep(0.3)
            print_bot(body)
        if options:
            print_options(options)


def auto_advance(fsm: QuestioningFSM, ctx: ConversationContext) -> None:
    """Advance through states that need no user input (e.g. feedback_* → end)."""
    state_data = fsm._flow.get(fsm.state, {})
    has_options = (
        state_data.get("options")
        or state_data.get("follow_up", {}).get("options", [])
    )
    if not has_options and "next_state" in state_data:
        time.sleep(0.6)
        response = fsm._handle_yaml_state("")  # internal advance, no count bump
        render_response(response, ctx)
        auto_advance(fsm, ctx)  # recurse if next state also has no options


def print_fallback_with_options(fsm: QuestioningFSM, fallback_msg: str) -> None:
    print_bot(fallback_msg)
    options = _get_current_options(fsm)
    if options:
        print("\n   Suas opções são:")
        print_options(options)


def print_summary(ctx: ConversationContext) -> None:
    decision_labels = {
        "share": "Vai compartilhar",
        "not_share": "Decidiu não compartilhar",
        "investigate": "Quer investigar mais",
        "": "Não concluído",
    }
    print(f"\n{DIVIDER}")
    print("  📊 RESUMO DA CONVERSA")
    print(DIVIDER)
    print(f"  Motivação:     {ctx.motivation or '—'}")
    print(f"  Emoção:        {ctx.emotion or '—'}")
    print(f"  Fonte:         {ctx.source_trust or '—'}")
    print(f"  Decisão:       {decision_labels.get(ctx.final_decision, ctx.final_decision)}")
    print(f"  Interações:    {ctx.interaction_count}")
    print(DIVIDER)


def make_fresh_fsm() -> tuple[QuestioningFSM, ConversationContext]:
    ctx = ConversationContext(user_id="terminal-user", platform="terminal")
    return QuestioningFSM(ctx), ctx


def run() -> None:
    print(f"\n{DIVIDER}")
    print("  🤖 Mentor Digital — Modo Terminal")
    print(DIVIDER)
    print("  Envie qualquer conteúdo para começar.")
    print("  Digite 'sair' para encerrar.")
    print(DIVIDER)

    fsm, ctx = make_fresh_fsm()

    while True:
        try:
            user_input = input(USER_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEncerrando...")
            break

        if not user_input:
            continue

        if user_input.lower() == "sair":
            print_bot("Até a próxima! Continue questionando antes de compartilhar. 🤗")
            break

        response = fsm.process_input(user_input)

        # Detect fallback (no state change, single fallback message)
        msgs = response.get("messages", [])
        if len(msgs) == 1 and "escolher" in msgs[0].get("body", "").lower():
            print_fallback_with_options(fsm, msgs[0]["body"])
        else:
            render_response(response, ctx)
            # Auto-advance through no-option states (feedback → end)
            auto_advance(fsm, ctx)

        if fsm.state == "end":
            print_summary(ctx)
            print_bot("Conversa encerrada. Envie um novo conteúdo para começar de novo.")
            fsm, ctx = make_fresh_fsm()


if __name__ == "__main__":
    run()
