import os
import time
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def model_name() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def call_json(messages: list[dict], temperature: float = 0.1) -> dict:
    client = get_client()
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model_name(),
        messages=messages,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "content": resp.choices[0].message.content,
        "tokens": {
            "prompt": resp.usage.prompt_tokens,
            "completion": resp.usage.completion_tokens,
        },
        "latency_ms": elapsed_ms,
    }
