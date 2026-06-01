import json
import os
from datetime import datetime, timezone
from agent.llm import model_name


def write_trace(out_dir: str, slug: str, query: str, result: dict) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    record = {
        "query": query,
        "model": model_name(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "iterations": result["iterations"],
        "critic_rounds": result["critic_rounds"],
        "final_answer": result["final_answer"],
        "sources": result["sources"],
        "status": result["status"],
        "total_tokens": result["total_tokens"],
        "total_latency_ms": result["total_latency_ms"],
    }
    json_path = os.path.join(out_dir, f"{slug}.json")
    with open(json_path, "w") as f:
        json.dump(record, f, indent=2, default=str)

    md_path = os.path.join(out_dir, f"{slug}.md")
    with open(md_path, "w") as f:
        f.write(_render_md(record))

    return json_path, md_path


def _render_md(record: dict) -> str:
    lines = []
    lines.append(f"# Trace — {record['query']}")
    lines.append("")
    lines.append(f"**Model:** `{record['model']}`  ")
    lines.append(f"**Status:** `{record['status']}`  ")
    lines.append(f"**Total tokens:** {record['total_tokens']}  ")
    lines.append(f"**Total latency:** {record['total_latency_ms']} ms  ")
    lines.append("")

    verdicts = [r["verdict"] for r in record["critic_rounds"]]
    if "REJECT" in verdicts:
        ribbon = " -> ".join(verdicts)
        lines.append(f"> **Self-correction occurred:** `{ribbon}`")
        lines.append("")

    lines.append("## ReAct trace")
    lines.append("")
    for it in record["iterations"]:
        lines.append(f"### Iteration {it['i']}")
        lines.append(f"**Thought:** {it.get('thought') or '(parse error)'}")
        lines.append("")
        lines.append("**Action:**")
        lines.append("```json")
        lines.append(json.dumps({"action": it.get("action"), "action_input": it.get("action_input")}, indent=2, default=str))
        lines.append("```")
        if it.get("observation") is not None:
            lines.append("**Observation:**")
            lines.append("```json")
            obs_str = json.dumps(it["observation"], indent=2, default=str)
            if len(obs_str) > 1500:
                obs_str = obs_str[:1500] + "\n... (truncated)"
            lines.append(obs_str)
            lines.append("```")
        lines.append(f"_latency: {it['latency_ms']} ms · tokens: {it['tokens']['prompt']}+{it['tokens']['completion']}_")
        lines.append("")

    lines.append("## Critic rounds")
    lines.append("")
    for r in record["critic_rounds"]:
        marker = "APPROVED" if r["verdict"] == "APPROVE" else "REJECTED"
        lines.append(f"### Round {r['round']} — {marker}")
        if r["issues"]:
            for issue in r["issues"]:
                lines.append(f"- **{issue['axis']}**: {issue['detail']}")
        if r["hint"]:
            lines.append(f"- **Hint:** {r['hint']}")
        lines.append("")

    lines.append("## Final answer")
    lines.append("")
    lines.append(record["final_answer"])
    lines.append("")
    lines.append("**Sources:** " + (", ".join(record["sources"]) if record["sources"] else "(none)"))
    return "\n".join(lines)
