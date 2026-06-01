from unittest.mock import patch
from agent.critic import critique, run_with_critic


def _llm_returns(*payloads):
    iterator = iter(payloads)

    def fake_call(messages, temperature=0.1):
        return {"content": next(iterator), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    return fake_call


def test_critique_approve():
    payload = '{"verdict": "APPROVE", "issues": [], "hint": null}'
    with patch("agent.critic.call_json", side_effect=_llm_returns(payload)):
        v = critique(user_query="q", draft_answer="a", sources=[], trace=[])
    assert v.verdict == "APPROVE"


def test_critique_reject():
    payload = '{"verdict": "REJECT", "issues": [{"axis": "arithmetic", "detail": "wrong"}], "hint": "redo math"}'
    with patch("agent.critic.call_json", side_effect=_llm_returns(payload)):
        v = critique(user_query="q", draft_answer="a", sources=[], trace=[])
    assert v.verdict == "REJECT"
    assert v.hint == "redo math"


def test_run_with_critic_approves_first_pass():
    react_payload = '{"thought": "easy", "action": "finish", "action_input": {"answer": "42", "sources": []}}'
    critic_payload = '{"verdict": "APPROVE", "issues": [], "hint": null}'

    react_iter = iter([react_payload])
    critic_iter = iter([critic_payload])

    def react_fake(messages, temperature=0.1):
        return {"content": next(react_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    def critic_fake(messages, temperature=0.1):
        return {"content": next(critic_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    with patch("agent.react_loop.call_json", side_effect=react_fake):
        with patch("agent.critic.call_json", side_effect=critic_fake):
            result = run_with_critic("what?", max_critic_retries=2)

    assert len(result["critic_rounds"]) == 1
    assert result["critic_rounds"][0]["verdict"] == "APPROVE"
    assert result["final_answer"] == "42"


def test_run_with_critic_rejects_then_approves():
    react_round1 = '{"thought": "draft", "action": "finish", "action_input": {"answer": "wrong", "sources": []}}'
    critic_round1 = '{"verdict": "REJECT", "issues": [{"axis": "arithmetic", "detail": "x"}], "hint": "retry"}'
    react_round2 = '{"thought": "fixed", "action": "finish", "action_input": {"answer": "right", "sources": []}}'
    critic_round2 = '{"verdict": "APPROVE", "issues": [], "hint": null}'

    react_iter = iter([react_round1, react_round2])
    critic_iter = iter([critic_round1, critic_round2])

    def react_fake(messages, temperature=0.1):
        return {"content": next(react_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    def critic_fake(messages, temperature=0.1):
        return {"content": next(critic_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    with patch("agent.react_loop.call_json", side_effect=react_fake):
        with patch("agent.critic.call_json", side_effect=critic_fake):
            result = run_with_critic("what?", max_critic_retries=2)

    assert len(result["critic_rounds"]) == 2
    assert result["critic_rounds"][0]["verdict"] == "REJECT"
    assert result["critic_rounds"][1]["verdict"] == "APPROVE"
    assert result["final_answer"] == "right"
    assert result["status"] == "completed"


def test_run_with_critic_exhausts_retries():
    react_payload = '{"thought": "draft", "action": "finish", "action_input": {"answer": "x", "sources": []}}'
    critic_payload = '{"verdict": "REJECT", "issues": [{"axis": "logical", "detail": "y"}], "hint": "fix it"}'

    react_iter = iter([react_payload] * 10)
    critic_iter = iter([critic_payload] * 10)

    def react_fake(messages, temperature=0.1):
        return {"content": next(react_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    def critic_fake(messages, temperature=0.1):
        return {"content": next(critic_iter), "tokens": {"prompt": 5, "completion": 3}, "latency_ms": 1}

    with patch("agent.react_loop.call_json", side_effect=react_fake):
        with patch("agent.critic.call_json", side_effect=critic_fake):
            result = run_with_critic("what?", max_critic_retries=2)

    assert result["status"] == "critic_unsatisfied"
    assert len(result["critic_rounds"]) == 3
