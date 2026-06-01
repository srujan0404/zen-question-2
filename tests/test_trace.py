import json
import os
import tempfile
from agent.trace import write_trace


SAMPLE_RESULT = {
    "iterations": [
        {
            "i": 1,
            "thought": "I need today's date",
            "action": "datetime",
            "action_input": {"op": "today"},
            "observation": {"ok": True, "result": "2026-06-02"},
            "latency_ms": 100,
            "tokens": {"prompt": 50, "completion": 20},
        },
        {
            "i": 2,
            "thought": "Done",
            "action": "finish",
            "action_input": {"answer": "Today is 2026-06-02", "sources": []},
            "observation": None,
            "latency_ms": 80,
            "tokens": {"prompt": 60, "completion": 15},
        },
    ],
    "critic_rounds": [{"round": 1, "verdict": "APPROVE", "issues": [], "hint": None}],
    "final_answer": "Today is 2026-06-02",
    "sources": [],
    "status": "completed",
    "total_tokens": 145,
    "total_latency_ms": 180,
}


def test_writes_both_json_and_md():
    with tempfile.TemporaryDirectory() as tmp:
        write_trace(tmp, "query_1_simple", "What is today?", SAMPLE_RESULT)
        assert os.path.exists(os.path.join(tmp, "query_1_simple.json"))
        assert os.path.exists(os.path.join(tmp, "query_1_simple.md"))


def test_json_is_valid_and_contains_query():
    with tempfile.TemporaryDirectory() as tmp:
        write_trace(tmp, "query_1_simple", "What is today?", SAMPLE_RESULT)
        with open(os.path.join(tmp, "query_1_simple.json")) as f:
            data = json.load(f)
        assert data["query"] == "What is today?"
        assert data["status"] == "completed"
        assert len(data["iterations"]) == 2


def test_md_contains_iteration_headers():
    with tempfile.TemporaryDirectory() as tmp:
        write_trace(tmp, "query_1_simple", "What?", SAMPLE_RESULT)
        with open(os.path.join(tmp, "query_1_simple.md")) as f:
            md = f.read()
        assert "### Iteration 1" in md
        assert "### Iteration 2" in md
        assert "APPROVED" in md


def test_md_marks_critic_reject_visibly():
    result = {**SAMPLE_RESULT,
              "critic_rounds": [
                  {"round": 1, "verdict": "REJECT", "issues": [{"axis": "arithmetic", "detail": "off"}], "hint": "redo"},
                  {"round": 2, "verdict": "APPROVE", "issues": [], "hint": None},
              ]}
    with tempfile.TemporaryDirectory() as tmp:
        write_trace(tmp, "query_3_complex", "?", result)
        with open(os.path.join(tmp, "query_3_complex.md")) as f:
            md = f.read()
        assert "REJECTED" in md.upper()
        assert "redo" in md
