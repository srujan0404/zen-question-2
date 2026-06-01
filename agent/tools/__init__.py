from agent.tools import python_exec, wikipedia, datetime_tool

REGISTRY = {
    "python_exec": python_exec.run,
    "wikipedia": wikipedia.run,
    "datetime": datetime_tool.run,
}

TOOL_SPECS = [python_exec.SPEC, wikipedia.SPEC, datetime_tool.SPEC]


def dispatch(action: str, action_input) -> dict:
    fn = REGISTRY.get(action)
    if fn is None:
        return {
            "ok": False,
            "error": f"unknown action '{action}'. Available: {list(REGISTRY.keys())}",
            "error_type": "bad_input",
        }
    if not isinstance(action_input, dict):
        return {
            "ok": False,
            "error": f"action_input must be a JSON object, got {type(action_input).__name__}",
            "error_type": "bad_input",
        }
    try:
        return fn(action_input)
    except Exception as e:
        return {"ok": False, "error": f"unexpected: {type(e).__name__}: {e}", "error_type": "exec_error"}
