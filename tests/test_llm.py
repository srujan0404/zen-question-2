from unittest.mock import patch, MagicMock
from agent.llm import call_json


def _fake_completion(content: str, prompt_tokens=10, completion_tokens=20):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def test_call_json_returns_content_and_usage():
    fake = _fake_completion('{"hello": "world"}')
    with patch("agent.llm.get_client") as gc:
        gc.return_value.chat.completions.create.return_value = fake
        out = call_json(messages=[{"role": "user", "content": "hi"}])
    assert out["content"] == '{"hello": "world"}'
    assert out["tokens"]["prompt"] == 10
    assert out["tokens"]["completion"] == 20
    assert out["latency_ms"] >= 0


def test_call_json_uses_json_mode():
    fake = _fake_completion('{}')
    with patch("agent.llm.get_client") as gc:
        gc.return_value.chat.completions.create.return_value = fake
        call_json(messages=[{"role": "user", "content": "x"}])
        kwargs = gc.return_value.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["temperature"] == 0.1
