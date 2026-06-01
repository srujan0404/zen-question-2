from agent.tools import dispatch, REGISTRY, TOOL_SPECS


def test_registry_has_three_tools():
    assert "python_exec" in REGISTRY
    assert "wikipedia" in REGISTRY
    assert "datetime" in REGISTRY


def test_tool_specs_lists_three():
    assert len(TOOL_SPECS) == 3


def test_dispatch_datetime():
    result = dispatch("datetime", {"op": "today"})
    assert result["ok"] is True


def test_dispatch_unknown_tool_returns_error():
    result = dispatch("ghost_tool", {})
    assert result["ok"] is False
    assert result["error_type"] == "bad_input"


def test_dispatch_propagates_tool_error_envelope():
    result = dispatch("python_exec", {"code": "1/0"})
    assert result["ok"] is False
    assert result["error_type"] == "exec_error"


def test_dispatch_catches_non_dict_input():
    result = dispatch("datetime", None)
    assert result["ok"] is False
    assert result["error_type"] == "bad_input"
