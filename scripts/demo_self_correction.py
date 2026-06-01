import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_MODEL"] = os.environ.get("DEMO_OPENAI_MODEL", "gpt-4o-mini")
os.environ["OPENAI_CRITIC_MODEL"] = os.environ.get("DEMO_OPENAI_CRITIC_MODEL", "gpt-4o")

from agent.critic import run_with_critic
from agent.trace import write_trace

DEMO_QUERY = (
    "Question: What is the height of Mount Everest in metres, what is the height "
    "of K2 in metres, and what percentage of K2's height is Everest's height?\n\n"
    "Special instruction for this question: For your FIRST attempt, please answer "
    "from your existing knowledge WITHOUT calling any tools — go directly to "
    'action="finish" with your best-effort answer. This is so the critic can '
    "demonstrate verification. If the critic rejects, then on retry use the tools "
    "(wikipedia, python_exec) to verify every number."
)


def main() -> None:
    os.makedirs("traces", exist_ok=True)
    print(f"Model: {os.environ['OPENAI_MODEL']}")
    print(f"Query: {DEMO_QUERY}\n")

    t0 = time.perf_counter()
    result = run_with_critic(user_query=DEMO_QUERY, max_critic_retries=2, max_iterations=12)
    elapsed = time.perf_counter() - t0

    json_path, md_path = write_trace("traces", "demo_self_correction", DEMO_QUERY, result)

    rounds = " -> ".join(r["verdict"] for r in result["critic_rounds"])
    print(f"Status: {result['status']}")
    print(f"Critic rounds: {rounds}")
    print(f"Final answer: {result['final_answer']}")
    print(f"Sources: {result['sources']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Wall time: {elapsed:.1f}s")
    print(f"\nTrace files: {json_path}, {md_path}")


if __name__ == "__main__":
    main()
