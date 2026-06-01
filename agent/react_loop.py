import json
from pydantic import ValidationError
from agent.llm import call_json
from agent.prompts import AGENT_SYSTEM_PROMPT
from agent.schemas import AgentStep
from agent.tools import dispatch


def run_react(
    user_query: str,
    extra_system_notes: list[str] | None = None,
    max_iterations: int = 8,
    initial_messages: list[dict] | None = None,
    starting_iter_num: int = 1,
) -> dict:
    extra_system_notes = extra_system_notes or []

    if initial_messages is None:
        messages: list[dict] = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
        for note in extra_system_notes:
            messages.append({"role": "system", "content": note})
        messages.append({"role": "user", "content": user_query})
    else:
        messages = list(initial_messages)
        for note in extra_system_notes:
            messages.append({"role": "system", "content": note})

    iterations = []
    total_tokens = 0
    total_latency = 0

    for offset in range(max_iterations):
        i = starting_iter_num + offset
        llm_out = call_json(messages=messages)
        total_tokens += llm_out["tokens"]["prompt"] + llm_out["tokens"]["completion"]
        total_latency += llm_out["latency_ms"]
        raw = llm_out["content"]

        try:
            step = AgentStep.model_validate_json(raw)
        except (ValidationError, ValueError):
            observation = {
                "ok": False,
                "error": "Your last output was not valid JSON matching {thought, action, action_input}. Try again.",
                "error_type": "parse_error",
            }
            iterations.append({
                "i": i,
                "thought": None,
                "action": None,
                "action_input": None,
                "raw_output": raw,
                "observation": observation,
                "latency_ms": llm_out["latency_ms"],
                "tokens": llm_out["tokens"],
            })
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {json.dumps(observation)}"})
            continue

        if step.action == "finish":
            iterations.append({
                "i": i,
                "thought": step.thought,
                "action": "finish",
                "action_input": step.action_input,
                "observation": None,
                "latency_ms": llm_out["latency_ms"],
                "tokens": llm_out["tokens"],
            })
            messages.append({"role": "assistant", "content": raw})
            return {
                "iterations": iterations,
                "final_answer": step.action_input.get("answer", ""),
                "sources": step.action_input.get("sources", []),
                "status": "completed",
                "total_tokens": total_tokens,
                "total_latency_ms": total_latency,
                "messages": messages,
            }

        observation = dispatch(step.action, step.action_input)
        iterations.append({
            "i": i,
            "thought": step.thought,
            "action": step.action,
            "action_input": step.action_input,
            "observation": observation,
            "latency_ms": llm_out["latency_ms"],
            "tokens": llm_out["tokens"],
        })
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": f"Observation: {json.dumps(observation, default=str)[:2000]}"})

    last_thought = iterations[-1]["thought"] if iterations else ""
    return {
        "iterations": iterations,
        "final_answer": f"(no final answer — iteration cap reached. Last thought: {last_thought})",
        "sources": [],
        "status": "max_iterations_exceeded",
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency,
        "messages": messages,
    }
