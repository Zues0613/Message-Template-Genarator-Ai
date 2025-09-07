import os
import sys
from dotenv import load_dotenv, find_dotenv


def mask(value: str) -> str:
    if not value:
        return "<empty>"
    return f"{value[:4]}****"


def main() -> int:
    dotenv_path = find_dotenv(usecwd=True)
    loaded = load_dotenv(dotenv_path or None)
    print("dotenv_path:", dotenv_path or "<not found>")
    print("loaded:", bool(loaded))

    keys_in_priority = [
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "DEFAULT_DEEPSEEK_API_KEY",
    ]

    found = []
    for k in keys_in_priority:
        v = os.getenv(k)
        if v:
            found.append((k, v))

    if not found:
        print("no_api_keys_found=True")
    else:
        print("api_keys_found:")
        for k, v in found:
            print(f"  - {k} = {mask(v)} (startswith sk-or: {str(v.startswith('sk-or-'))})")

    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENROUTER_URL")
    model = os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENROUTER_MODEL")
    print("base_url:", base_url)
    print("model:", model)

    return 0


if __name__ == "__main__":
    sys.exit(main())


