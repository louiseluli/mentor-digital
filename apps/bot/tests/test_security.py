import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set peppers before importing security module
os.environ["PSEUDONYMIZATION_PEPPER"] = "test_pepper_operacional"
os.environ["ANALYTICS_PEPPER"] = "test_pepper_analytics"

from src.security import pseudonymize, pseudonymize_for_analytics
from src.config import load_config


def test_pseudonymize_is_deterministic():
    result1 = pseudonymize("+5511999998888")
    result2 = pseudonymize("+5511999998888")
    assert result1 == result2


def test_pseudonymize_is_irreversible():
    phone = "+5511999998888"
    result = pseudonymize(phone)
    assert phone not in result
    assert "999998888" not in result
    assert len(result) == 64  # SHA-256 hex digest


def test_pseudonymize_different_inputs_different_outputs():
    result1 = pseudonymize("+5511999998888")
    result2 = pseudonymize("+5511999997777")
    assert result1 != result2


def test_pseudonymize_analytics_separate_from_operational():
    phone = "+5511999998888"
    result_ops = pseudonymize(phone)
    result_analytics = pseudonymize_for_analytics(phone)
    assert result_ops != result_analytics


def test_pseudonymize_output_is_hex_string():
    result = pseudonymize("any-user-id")
    assert all(c in "0123456789abcdef" for c in result)


def test_config_loads_from_env():
    os.environ["PSEUDONYMIZATION_PEPPER"] = "test_pepper_operacional"
    os.environ["ANALYTICS_PEPPER"] = "test_pepper_analytics"
    config = load_config()
    assert config.pseudonymization_pepper == "test_pepper_operacional"
    assert config.analytics_pepper == "test_pepper_analytics"


def test_config_fails_without_required_vars():
    saved_ops = os.environ.pop("PSEUDONYMIZATION_PEPPER", None)
    saved_analytics = os.environ.pop("ANALYTICS_PEPPER", None)
    try:
        with pytest.raises(ValueError):
            load_config()
    finally:
        if saved_ops:
            os.environ["PSEUDONYMIZATION_PEPPER"] = saved_ops
        if saved_analytics:
            os.environ["ANALYTICS_PEPPER"] = saved_analytics


def test_security_fails_without_pepper_env():
    saved = os.environ.pop("PSEUDONYMIZATION_PEPPER", None)
    try:
        with pytest.raises(ValueError):
            pseudonymize("+5511999998888")
    finally:
        if saved:
            os.environ["PSEUDONYMIZATION_PEPPER"] = saved
