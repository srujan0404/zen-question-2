import os
import re
import time
from functools import lru_cache
from openai import OpenAI, RateLimitError
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


def _wait_seconds_from_error(err: RateLimitError) -> float:
    msg = str(err)
    m = re.search(r"try again in (\d+\.?\d*)s", msg, re.IGNORECASE)
    if m:
        return float(m.group(1)) + 0.5
    return 20.0


def call_json(messages: list[dict], temperature: float = 0.1, model: str | None = None) -> dict:
    client = get_client()
    chosen_model = model or model_name()
    attempts_remaining = 4

    while True:
        try:
            t0 = time.perf_counter()
            resp = client.chat.completions.create(
                model=chosen_model,
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
        except RateLimitError as e:
            attempts_remaining -= 1
            if attempts_remaining <= 0:
                raise
            wait = _wait_seconds_from_error(e)
            time.sleep(min(wait, 30.0))
