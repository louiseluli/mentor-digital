import sys
import os
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "engine", "flows", "questioning.yaml"
)


def load_flow():
    with open(FLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["flow"]


def test_yaml_loads_correctly():
    flow = load_flow()
    assert "greeting" in flow
    assert "closing" in flow
    assert "end" in flow


def test_all_next_states_exist():
    flow = load_flow()
    all_states = set(flow.keys())

    for state_name, state_data in flow.items():
        # Check top-level next_state (for states without options)
        if "next_state" in state_data:
            assert state_data["next_state"] in all_states, (
                f"State '{state_data['next_state']}' referenced by '{state_name}' doesn't exist"
            )
        # Check options[].next_state
        if "options" in state_data:
            for opt in state_data["options"]:
                if "next_state" in opt:
                    assert opt["next_state"] in all_states, (
                        f"State '{opt['next_state']}' referenced by option "
                        f"'{opt['id']}' in '{state_name}' doesn't exist"
                    )
        # Check follow_up.options[].next_state (e.g., greeting)
        if "follow_up" in state_data and "options" in state_data["follow_up"]:
            for opt in state_data["follow_up"]["options"]:
                if "next_state" in opt:
                    assert opt["next_state"] in all_states, (
                        f"State '{opt['next_state']}' referenced by follow_up option "
                        f"'{opt['id']}' in '{state_name}' doesn't exist"
                    )


def test_no_message_exceeds_300_chars():
    flow = load_flow()
    for state_name, state_data in flow.items():
        if "message" in state_data:
            length = len(state_data["message"])
            assert length <= 300, (
                f"Message in '{state_name}' has {length} chars (max 300)"
            )


def test_closing_exists_and_has_three_options():
    flow = load_flow()
    assert "closing" in flow
    assert "options" in flow["closing"]
    assert len(flow["closing"]["options"]) == 3


def test_no_judgmental_language():
    forbidden = ["falso", "fake", "mentira", "errado", "burro", "ignorante", "ingênuo"]
    flow = load_flow()
    for state_name, state_data in flow.items():
        if "message" in state_data:
            msg_lower = state_data["message"].lower()
            for word in forbidden:
                assert word not in msg_lower, (
                    f"Forbidden word '{word}' found in state '{state_name}'"
                )


def test_greeting_has_six_motivation_options():
    flow = load_flow()
    options = flow["greeting"]["follow_up"]["options"]
    assert len(options) == 6
    ids = [o["id"] for o in options]
    assert set(ids) == {"inform", "alert", "opinion", "identify", "seen_many", "other"}


def test_all_deepening_states_lead_to_closing():
    flow = load_flow()
    deepening_states = [k for k in flow if k.startswith("deepening_")]
    for state_name in deepening_states:
        state = flow[state_name]
        if "options" in state:
            for opt in state["options"]:
                assert opt["next_state"] == "closing", (
                    f"Option '{opt['id']}' in '{state_name}' doesn't lead to closing"
                )
        elif "next_state" in state:
            assert state["next_state"] == "closing", (
                f"'{state_name}' next_state is not 'closing'"
            )
