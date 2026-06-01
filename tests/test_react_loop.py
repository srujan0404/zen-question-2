from unittest.mock import patch
from agent.react_loop import run_react


def _llm_returns(*payloads):
    iterator = iter(payloads)

    def fake_call(messages, temperature=0.1):
        return {"content": next(iterator), "tokens": {"prompt": 10, "completion": 5}, "latency_ms": 1}

    return fake_call


def test_loop_terminates_on_finish():
    payloads = [
        '{"thought": "easy", "action": "finish", "action_input": {"answer": "42", "sources": []}}',
    ]
    with patch("agent.react_loop.call_json", side_effect=_llm_returns(*payloads)):
        result = run_react(user_query="What?", extra_system_notes=[])
    assert result["final_answer"] == "42"
    assert result["status"] == "completed"
    assert len(result["iterations"]) == 1


def test_loop_dispatches_then_finishes():
    payloads = [
        '{"thought": "need date", "action": "datetime", "action_input": {"op": "today"}}',
        '{"thought": "have it", "action": "finish", "action_input": {"answer": "done", "sources": []}}',
    ]
    with patch("agent.react_loop.call_json", side_effect=_llm_returns(*payloads)):
        result = run_react(user_query="Today?", extra_system_notes=[])
    assert result["status"] == "completed"
    assert len(result["iterations"]) == 2
    assert result["iterations"][0]["action"] == "datetime"
    assert result["iterations"][0]["observation"]["ok"] is True


def test_loop_handles_invalid_json_then_recovers():
    payloads = [
        'not json at all',
        '{"thought": "ok now", "action": "finish", "action_input": {"answer": "ok", "sources": []}}',
    ]
    with patch("agent.react_loop.call_json", side_effect=_llm_returns(*payloads)):
        result = run_react(user_query="?", extra_system_notes=[])
    assert result["status"] == "completed"
    assert result["iterations"][0]["observation"]["error_type"] == "parse_error"


def test_loop_hits_iteration_cap():
    payloads = ['{"thought": "x", "action": "datetime", "action_input": {"op": "today"}}'] * 10
    with patch("agent.react_loop.call_json", side_effect=_llm_returns(*payloads)):
        result = run_react(user_query="?", extra_system_notes=[], max_iterations=3)
    assert result["status"] == "max_iterations_exceeded"
    assert len(result["iterations"]) == 3
