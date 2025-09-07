import asyncio
import os
import sys
from dotenv import load_dotenv, find_dotenv

try:
    import openai
except ImportError:
    print("Please 'pip install openai python-dotenv' in your virtualenv.")
    sys.exit(1)


def load_env():
    path = find_dotenv(usecwd=True)
    load_dotenv(path or None)
    return path


def resolve_api_key():
    for k in ["OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "DEFAULT_DEEPSEEK_API_KEY"]:
        v = os.getenv(k)
        if v:
            return k, v
    return None, None


async def run_probe():
    dotenv_path = load_env()
    print("[probe] dotenv:", dotenv_path or "<none>")

    key_name, key_value = resolve_api_key()
    if not key_value:
        print("[probe] No API key found in env. Checked OPENROUTER_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY, DEFAULT_DEEPSEEK_API_KEY")
        return 2

    base_url = os.getenv("DEEPSEEK_BASE_URL", os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"))
    model = os.getenv("DEEPSEEK_MODEL", os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"))
    print(f"[probe] using key: {key_name} ({key_value[:4]}****), base_url: {base_url}, model: {model}")

    client = openai.AsyncOpenAI(api_key=key_value, base_url=base_url)
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with: ok"}],
            max_tokens=2,
            temperature=0,
        )
        try:
            msg = resp.choices[0].message.content.strip()
        except Exception:
            msg = (getattr(resp, "text", "") or "").strip()
        print("[probe] response:", repr(msg))
        if not msg:
            print("[probe] ERROR: empty response body")
            return 3
        return 0
    except Exception as e:
        print("[probe] ERROR:", e)
        return 4
    finally:
        try:
            aclose = getattr(client, "aclose", None)
            if callable(aclose):
                await aclose()
            else:
                close = getattr(client, "close", None)
                if callable(close):
                    close()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(run_probe())
    sys.exit(exit_code)


