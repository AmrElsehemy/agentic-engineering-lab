import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from agent import get_training_plan


def test_tool_returns_bounded_sessions():
    result = get_training_plan("athlete", "HYROX preparation", 2)
    assert result["days_available"] == 2
    assert len(result["sessions"]) == 2
    assert result["limitations"]


def test_tool_rejects_invalid_days():
    try:
        get_training_plan("athlete", "goal", 0)
    except ValueError as exc:
        assert "days_available" in str(exc)
    else:
        raise AssertionError("Expected validation error")
