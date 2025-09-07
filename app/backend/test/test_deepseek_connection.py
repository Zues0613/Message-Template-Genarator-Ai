#!/usr/bin/env python3
"""
DeepSeek connection smoke test (standalone)

What this shows at a glance:
- How to choose base_url and model based on your API key (OpenRouter vs direct DeepSeek)
- How to initialize the OpenAI-compatible client
- How to send a simple chat completion request and print the response

Requirements:
- Python packages: openai, python-dotenv (optional but recommended)
- Environment variable containing your key:
  - DEEPSEEK_API_KEY (preferred) or DEFAULT_DEEPSEEK_API_KEY (fallback)
  - For OpenRouter, use a key starting with "sk-or-v1-" and base_url will be set automatically
  - Optional: DEEPSEEK_MODEL, DEEPSEEK_MAX_TOKENS, DEEPSEEK_TEMPERATURE

Usage examples:
  1) Set environment and run:
     set DEEPSEEK_API_KEY=sk-or-v1-xxxxxxxx   (Windows PowerShell: $env:DEEPSEEK_API_KEY = 'sk-or-v1-...')
     python backend/test/test_deepseek_connection.py

  2) Provide a custom prompt:
     python backend/test/test_deepseek_connection.py --prompt "Say hello in one sentence"

  3) Provide an API key explicitly (overrides env):
     python backend/test/test_deepseek_connection.py --api-key sk-or-v1-xxxxxxxx

Notes:
- If your key starts with "sk-or-v1-", this script uses OpenRouter with model "deepseek/deepseek-r1-0528" by default
- Otherwise, it uses DeepSeek direct API with model "deepseek-reasoner" by default
"""

import argparse
import asyncio
import os
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; if unavailable, environment must be set by other means
    pass

import openai


def resolve_connection_details(explicit_api_key: str | None = None) -> Dict[str, Any]:
    """Decide API key, base_url, model, and defaults based on environment or explicit key."""
    api_key = explicit_api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("No API key found. Set DEEPSEEK_API_KEY or pass --api-key.")

    # Heuristic used in the codebase: OpenRouter keys start with "sk-or-v1-"
    is_openrouter = api_key.startswith("sk-or-v1-")

    if is_openrouter:
        base_url = "https://openrouter.ai/api/v1"
        # This model matches backend usage in app/services/deepseek_service.py
        default_model = "deepseek/deepseek-r1-0528"
    else:
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        # This model matches backend usage in app/services/deepseek_r1_service.py
        default_model = "deepseek-reasoner"

    model = os.getenv("DEEPSEEK_MODEL", default_model)
    temperature = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7"))
    max_tokens_env = os.getenv("DEEPSEEK_MAX_TOKENS", "").strip()
    max_tokens: int | None = int(max_tokens_env) if max_tokens_env.isdigit() and int(max_tokens_env) > 0 else None

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "is_openrouter": is_openrouter,
    }


async def run_test(prompt: str, api_key: str | None = None) -> None:
    details = resolve_connection_details(api_key)

    # Initialize OpenAI-compatible async client
    client = openai.AsyncOpenAI(api_key=details["api_key"], base_url=details["base_url"])

    # Build a minimal messages array. Add a system message if you need stronger style control.
    messages = [
        {"role": "user", "content": prompt},
    ]

    request: Dict[str, Any] = {
        "model": details["model"],
        "messages": messages,
        "temperature": details["temperature"],
    }

    if details["max_tokens"] is not None:
        request["max_tokens"] = details["max_tokens"]

    # Extra headers help attribute traffic for OpenRouter; harmless otherwise.
    request["extra_headers"] = {
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:3000"),
        "X-Title": os.getenv("OPENROUTER_X_TITLE", "DeepSeek Connection Test"),
    }

    print("--- DeepSeek Connection Test ---")
    print(f"Base URL    : {details['base_url']}")
    print(f"Model       : {details['model']}")
    print(f"OpenRouter  : {details['is_openrouter']}")
    print(f"Temperature : {details['temperature']}")
    print(f"Max tokens  : {details['max_tokens']}")
    print(f"Prompt      : {prompt}")
    print("-------------------------------\n")

    try:
        # Request with a reasonable timeout; adjust via OPENROUTER_TIMEOUT if desired
        timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT", "45"))
        response = await asyncio.wait_for(
            client.chat.completions.create(**request),
            timeout=timeout_seconds,
        )

        message = response.choices[0].message
        print("Response:")
        print(message.content or "<empty content>")

        # For function/tool-call scenarios, message.tool_calls would be populated
        if getattr(message, "tool_calls", None):
            print("\n(Note) Tool calls detected:")
            print(message.tool_calls)

    except asyncio.TimeoutError:
        print("Error: Request timed out. Increase OPENROUTER_TIMEOUT or try again.")
    except Exception as e:
        # Special-case OpenRouter 402 insufficient credits
        text = str(e)
        if (
            " 402" in text
            or "Error code: 402" in text
            or "requires more credits" in text
            or "more credits" in text
        ):
            print("Insufficient credits or token budget. Reduce max tokens or add credits.")
        else:
            print(f"Unexpected error: {text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepSeek connection smoke test")
    parser.add_argument("--prompt", type=str, default="Say hello in one short sentence.", help="Prompt to send")
    parser.add_argument("--api-key", type=str, default=None, help="API key to use (overrides env)")
    args = parser.parse_args()

    # On Windows, use asyncio.run which configures an event loop appropriately
    asyncio.run(run_test(args.prompt, args.api_key))


if __name__ == "__main__":
    main()