import pytest
from pydantic import ValidationError
from agent.schemas import AgentStep, CriticVerdict


def test_agent_step_tool_call_parses():
    raw = '{"thought": "I need a date.", "action": "datetime", "action_input": {"op": "today"}}'
    step = AgentStep.model_validate_json(raw)
    assert step.thought == "I need a date."
    assert step.action == "datetime"
    assert step.action_input == {"op": "today"}


def test_agent_step_finish_parses():
    raw = '{"thought": "Done.", "action": "finish", "action_input": {"answer": "42", "sources": ["wikipedia:Foo"]}}'
    step = AgentStep.model_validate_json(raw)
    assert step.action == "finish"
    assert step.action_input["answer"] == "42"


def test_agent_step_missing_thought_fails():
    raw = '{"action": "datetime", "action_input": {}}'
    with pytest.raises(ValidationError):
        AgentStep.model_validate_json(raw)


def test_critic_verdict_approve():
    raw = '{"verdict": "APPROVE", "issues": [], "hint": null}'
    v = CriticVerdict.model_validate_json(raw)
    assert v.verdict == "APPROVE"
    assert v.issues == []
    assert v.hint is None


def test_critic_verdict_reject_with_issue():
    raw = '{"verdict": "REJECT", "issues": [{"axis": "arithmetic", "detail": "off by one"}], "hint": "recompute"}'
    v = CriticVerdict.model_validate_json(raw)
    assert v.verdict == "REJECT"
    assert len(v.issues) == 1
    assert v.issues[0].axis == "arithmetic"
    assert v.hint == "recompute"


def test_critic_verdict_bad_axis_fails():
    raw = '{"verdict": "REJECT", "issues": [{"axis": "vibes", "detail": "x"}], "hint": "y"}'
    with pytest.raises(ValidationError):
        CriticVerdict.model_validate_json(raw)
