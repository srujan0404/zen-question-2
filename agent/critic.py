import json
import os
from pydantic import ValidationError
from agent.llm import call_json
from agent.prompts import CRITIC_SYSTEM_PROMPT
from agent.schemas import CriticVerdict
from agent.react_loop import run_react


def critique(user_query: str, draft_answer: str, sources: list, trace: list) -> CriticVerdict:
    summary = {
        "user_query": user_query,
        "draft_answer": draft_answer,
        "sources": sources,
        "trace": trace,
    }
    user_content = "Verify this:\n\n" + json.dumps(summary, default=str)[:8000]
    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    critic_model = os.environ.get("OPENAI_CRITIC_MODEL")  # optional override
    out = call_json(messages=messages, temperature=0.0, model=critic_model)
    try:
        return CriticVerdict.model_validate_json(out["content"])
    except (ValidationError, ValueError):
        return CriticVerdict(verdict="APPROVE", issues=[], hint=None)


def run_with_critic(user_query: str, max_critic_retries: int = 2, max_iterations: int = 12) -> dict:
    
    critic_rounds = []
    all_iterations: list = []
    total_tokens = 0
    total_latency = 0
    last_messages: list[dict] | None = None
    last_react: dict | None = None

    for round_idx in range(max_critic_retries + 1):
        if last_messages is None:
            react_result = run_react(
                user_query=user_query,
                extra_system_notes=[],
                max_iterations=max_iterations,
            )
        else:
            critic_note = (
                f"NOTE FROM CRITIC (round {round_idx}): "
                f"{critic_rounds[-1]['hint'] or 'your prior answer was rejected — revise it'}. "
                "You have already done work above; do NOT restart from scratch. Use the prior "
                "observations, fix the specific issue the critic flagged, and emit a corrected "
                "finish action when ready."
            )
            react_result = run_react(
                user_query=user_query,
                extra_system_notes=[critic_note],
                max_iterations=max_iterations,
                initial_messages=last_messages,
                starting_iter_num=len(all_iterations) + 1,
            )

        all_iterations.extend(react_result["iterations"])
        total_tokens += react_result["total_tokens"]
        total_latency += react_result["total_latency_ms"]
        last_messages = react_result["messages"]
        last_react = react_result

        trace_for_critic = [
            {
                "i": it["i"],
                "thought": it["thought"],
                "action": it["action"],
                "action_input": it["action_input"],
                "observation": it["observation"],
            }
            for it in all_iterations
        ]

        verdict = critique(
            user_query=user_query,
            draft_answer=react_result["final_answer"],
            sources=react_result["sources"],
            trace=trace_for_critic,
        )
        critic_rounds.append({
            "round": round_idx + 1,
            "verdict": verdict.verdict,
            "issues": [i.model_dump() for i in verdict.issues],
            "hint": verdict.hint,
        })

        if verdict.verdict == "APPROVE":
            return {
                "iterations": all_iterations,
                "final_answer": react_result["final_answer"],
                "sources": react_result["sources"],
                "status": "completed",
                "total_tokens": total_tokens,
                "total_latency_ms": total_latency,
                "messages": last_messages,
                "critic_rounds": critic_rounds,
            }

    # All retries exhausted without APPROVE.
    return {
        "iterations": all_iterations,
        "final_answer": last_react["final_answer"] if last_react else "",
        "sources": last_react["sources"] if last_react else [],
        "status": "critic_unsatisfied",
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency,
        "messages": last_messages,
        "critic_rounds": critic_rounds,
    }
