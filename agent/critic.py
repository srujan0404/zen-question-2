import json
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
    out = call_json(messages=messages, temperature=0.0)
    try:
        return CriticVerdict.model_validate_json(out["content"])
    except (ValidationError, ValueError):
        return CriticVerdict(verdict="APPROVE", issues=[], hint=None)


def run_with_critic(user_query: str, max_critic_retries: int = 2, max_iterations: int = 8) -> dict:
    extra_notes: list[str] = []
    critic_rounds = []
    react_result = None

    for round_idx in range(max_critic_retries + 1):
        react_result = run_react(
            user_query=user_query,
            extra_system_notes=extra_notes,
            max_iterations=max_iterations,
        )

        trace_for_critic = [
            {
                "i": it["i"],
                "thought": it["thought"],
                "action": it["action"],
                "action_input": it["action_input"],
                "observation": it["observation"],
            }
            for it in react_result["iterations"]
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
                **react_result,
                "critic_rounds": critic_rounds,
                "status": "completed",
            }

        if round_idx == max_critic_retries:
            break

        if verdict.hint:
            extra_notes.append(
                f"NOTE FROM CRITIC (round {round_idx + 1}): {verdict.hint}\n"
                f"Reconsider the step(s) that caused this and try again."
            )

    return {
        **react_result,
        "critic_rounds": critic_rounds,
        "status": "critic_unsatisfied",
    }
