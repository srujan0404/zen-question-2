# Multi-Step Agentic Workflow with Self-Correction — Zen Technologies OA Q2

A ReAct-style agent that answers multi-step analytical questions using three tools (Python executor, Wikipedia, date/time). A separate critic LLM call verifies arithmetic, logical consistency, and source grounding after every `finish`, and bounded-retries (max 2) with the hint injected back into the same transcript so the agent surgically fixes the broken step rather than starting over.

## TL;DR — what works

- **44/44 unit tests pass** — schemas, all 3 tools, dispatcher, LLM client, ReAct loop, critic, trace writer (`pytest -v`).
- **9/9 error-injection cases handled gracefully** (`scripts/error_injection.py`) — ZeroDivision, timeout, blocked imports, Wikipedia 404, disambiguation, bad input, unknown tool, non-dict input. None crash the agent.
- **Live before/after self-correction** captured end-to-end in `traces/demo_self_correction.md` — REJECT (no sources, ungrounded math) → APPROVE (Wikipedia + python_exec verified). Both LLM calls real; controlled only in that the query asks the agent to attempt the first draft from memory so the critic has something to catch.
- **Three live test queries** (simple / medium / complex) traced in `traces/query_{1,2,3}_*.md`.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # paste your OPENAI_API_KEY into .env

python run.py                              # 3 queries, writes traces/
python scripts/demo_self_correction.py     # before/after artifact
python scripts/error_injection.py          # tool-error validation
pytest -v                                  # 44 unit tests
```

## Architecture

```
            user query
                 |
                 v
  +-------------------+   action: tool   +----------+   {ok | error envelope}
  |   ReAct loop      | ---------------> | dispatch | -------+
  | (max 12 iters)    | <------------------------------------+
  +---------+---------+
            | action: finish
            v
  +-------------------+   APPROVE  ->  done
  |  Critic           |
  |  (separate LLM,   |   REJECT + hint  ->  inject as system note,
  |   3-axis check)   |                       continue same transcript (≤2 retries)
  +-------------------+
```

The LLM emits `{thought, action, action_input}` as a single JSON object every turn (enforced via OpenAI's JSON mode). We parse with pydantic, dispatch to one of three tools, append the `Observation`, and feed the running transcript back in. No agent framework — plain `openai` SDK + pydantic + requests.

## Outputs

- `traces/demo_self_correction.{md,json}` — the live REJECT → APPROVE before/after trace.
- `traces/query_{1,2,3}_*.{md,json}` — three test queries (simple / medium / complex).
- `traces/error_injection.md` — pass/fail table for 9 deliberately failing tool inputs.

## On-prem / defence-friendly architecture

The OpenAI client reads `OPENAI_BASE_URL` and `OPENAI_MODEL` from env. Swapping to a local Ollama instance (Ollama exposes an OpenAI-compatible API at `:11434/v1`) is a config-only change — no code changes:

```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL=qwen3
```

## Models used and validation

- **OpenAI `gpt-4o-mini`** — default agent + critic for `run.py` and unit tests. Cheap, fast, follows JSON-mode reliably.
- **OpenAI `gpt-4o`** — used as the critic in `demo_self_correction.py` (the "verifier outranks producer" pattern — a weaker agent + stronger critic). Demonstrably catches mistakes the agent makes.

**Validation methodology:**
1. Unit tests with mocked LLM and mocked external APIs cover every layer in isolation (`tests/` — 44 tests).
2. Live error-injection script exercises 9 distinct failure paths against the real tool dispatch layer and confirms every case returns an error envelope rather than crashing.
3. Live demo trace shows the critic genuinely rejecting an ungrounded draft and approving the retry — verifiable by inspecting `traces/demo_self_correction.md` (both rounds, all hint text, all observations).

## Known limit & next step

On the harder live queries (`query_2_medium`, `query_3_complex`) running on `gpt-4o-mini` for both agent and critic, the system hits `critic_unsatisfied` — the critic correctly catches that the agent put numbers in its final answer without computing them via `python_exec`, but `gpt-4o-mini` as the agent is too weak to act on the hint and repeats the same mistake. The fix is the architecture used in `demo_self_correction.py`: stronger critic than agent. Documented in the traces themselves rather than papered over.
