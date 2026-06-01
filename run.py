import os
from agent.critic import run_with_critic
from agent.trace import write_trace

TRACES_DIR = "traces"

QUERIES = [
    (
        "query_1_simple",
        "How old would Alan Turing be today if he were still alive?",
    ),
    (
        "query_2_medium",
        "What is the population density of India in 2024 (people per km squared), and how does it compare as a ratio to Japan's population density?",
    ),
    (
        "query_3_complex",
        "Wikipedia and Google were both founded in roughly the same era. Find each company's exact founding date, calculate the number of days between them (Wikipedia minus Google), and express that gap as a percentage of Wikipedia's total age in days as of today.",
    ),
]


def main() -> None:
    os.makedirs(TRACES_DIR, exist_ok=True)
    summary = []
    for slug, query in QUERIES:
        print(f"\n=== Running {slug} ===")
        print(f"Q: {query}\n")
        result = run_with_critic(user_query=query, max_critic_retries=2, max_iterations=12)
        json_path, md_path = write_trace(TRACES_DIR, slug, query, result)
        rounds = " -> ".join(r["verdict"] for r in result["critic_rounds"])
        print(f"Status: {result['status']}  Critic: {rounds}")
        print(f"Tokens: {result['total_tokens']}  Latency: {result['total_latency_ms']} ms")
        print(f"Wrote: {json_path}, {md_path}")
        summary.append((slug, result["status"], rounds, result["total_tokens"]))

    print("\n=== Summary ===")
    for slug, status, rounds, toks in summary:
        print(f"{slug}: {status} (critic {rounds}, {toks} tokens)")


if __name__ == "__main__":
    main()
