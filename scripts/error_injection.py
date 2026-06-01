import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import dispatch

os.makedirs("traces", exist_ok=True)

CASES = [
    ("python_exec ZeroDivisionError", "python_exec", {"code": "print(1/0)"}),
    ("python_exec timeout", "python_exec", {"code": "while True: pass"}),
    ("python_exec blocked import", "python_exec", {"code": "import os; print(os.listdir('/'))"}),
    ("python_exec syntax error", "python_exec", {"code": "print(1 +"}),
    ("wikipedia page not found", "wikipedia", {"op": "search", "query": "xyzzy_definitely_not_a_real_page_12345"}),
    ("wikipedia disambiguation", "wikipedia", {"op": "search", "query": "Mercury"}),
    ("datetime bad input", "datetime", {"op": "days_between", "start": "not-a-date", "end": "2020-01-01"}),
    ("unknown tool", "ghost_tool", {}),
    ("non-dict action_input", "datetime", "string-instead-of-dict"),
]


def main() -> None:
    lines = [
        "# Error injection validation",
        "",
        "Each row exercises a failure path. Every case must return an error envelope (no uncaught exceptions).",
        "",
        "| Case | Result | error_type | Error message (first 80 chars) |",
        "|---|---|---|---|",
    ]
    for name, action, action_input in CASES:
        result = dispatch(action, action_input)
        ok = "PASS" if result.get("ok") is False else "FAIL"
        err_type = result.get("error_type", "-")
        err_msg = (result.get("error") or "")[:80].replace("|", "\\|")
        lines.append(f"| {name} | {ok} | `{err_type}` | {err_msg} |")

    output = "\n".join(lines)
    with open("traces/error_injection.md", "w") as f:
        f.write(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
