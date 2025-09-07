from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pathlib
import os
import asyncio
import time
import random
import openai
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# Resolve directories
BACKEND_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Load .env
_dotenv_path = find_dotenv(usecwd=True)
load_dotenv(_dotenv_path or None)

app = FastAPI(title="WhatsApp CRM - Message Generator")

templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# Config
DEEPSEEK_API_KEY = (
    os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"))
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2500"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME")

SYSTEM_PROMPT = (
    "You are a concise message generator for business broadcast messages. "
    "Generate ONE short friendly message suitable for a WhatsApp broadcast. "
    "Always include the placeholder {name} exactly once. "
    "Keep it 1–2 sentences (unless asked for longer). Avoid links and questions."
)

TEMPLATES = {
    "diwali": "Hello {name}, Diwali greetings! We wish you the best holiday. Namaste!",
    "birthday": "Hello {name}, happy birthday! Wishing you a wonderful year ahead.",
    "promo": "Hello {name}, enjoy an exclusive {discount} off on your next order. Use code: {code}.",
    "generic": "Hello {name}, hope you are doing well. We have an update for you."
}

def detect_keyword(p: str) -> str:
    p = (p or "").lower()
    if "diwali" in p or "deepavali" in p:
        return "diwali"
    if "birthday" in p:
        return "birthday"
    if "promo" in p or "discount" in p or "offer" in p:
        return "promo"
    return "generic"

LENGTH_TOKEN_MAP = {"short": 120, "medium": 600, "long": 1200}

_openai_client: Optional[openai.AsyncOpenAI] = None

async def startup_openrouter_client():
    global _openai_client
    if DEEPSEEK_API_KEY:
        _openai_client = openai.AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        print("[openrouter] client initialized (base_url:", DEEPSEEK_BASE_URL, "model:", DEEPSEEK_MODEL, ")")
    else:
        _openai_client = None
        print("[openrouter] no API key found; AI disabled")

async def shutdown_openrouter_client():
    global _openai_client
    if _openai_client:
        try:
            aclose = getattr(_openai_client, "aclose", None)
            if callable(aclose):
                await aclose()
            else:
                close = getattr(_openai_client, "close", None)
                if callable(close):
                    close()
        except Exception as _e:
            print("[openrouter] client close warning:", _e)
        _openai_client = None
        print("[openrouter] client closed")

app.add_event_handler("startup", startup_openrouter_client)
app.add_event_handler("shutdown", shutdown_openrouter_client)

_rate_limit_lock = asyncio.Lock()
_last_call_ts: float = 0.0
_min_interval_seconds = float(os.getenv("OPENROUTER_MIN_INTERVAL", "1.5"))

async def _ensure_min_interval_between_calls() -> None:
    global _last_call_ts
    async with _rate_limit_lock:
        now = time.monotonic()
        wait_for = (_last_call_ts + _min_interval_seconds) - now
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _last_call_ts = time.monotonic()

async def generate_with_openrouter_via_client(prompt: str, tone: str, max_tokens: int, placeholders: str, audience: str, length: str) -> str:
    global _openai_client
    if not _openai_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI client not initialized")

    raw_placeholders = [p.strip() for p in (placeholders or "").split(",") if p.strip()]
    if not raw_placeholders:
        raw_placeholders = ["{name}"]
    norm_placeholders = []
    for ph in raw_placeholders:
        ph = ph if (ph.startswith("{") and ph.endswith("}")) else ("{" + ph.strip("{} ") + "}")
        if ph not in norm_placeholders:
            norm_placeholders.append(ph)

    if length == "medium":
        sentence_rule = "Write 4 to 5 complete sentences."
    elif length == "long":
        sentence_rule = "Write 7 to 9 complete sentences."
    else:
        sentence_rule = "Write 1 to 2 concise sentences."

    placeholders_rule = " ".join([f"Include the exact placeholder {ph} exactly once." for ph in norm_placeholders])

    user_instruction = (
        f"Audience: {audience or 'general audience'}\n"
        f"Tone: {tone}\n"
        f"Desired tokens (approx): {max_tokens}\n"
        f"User prompt: {prompt}\n\n"
        "Task: Produce one broadcast-ready WhatsApp message based on the user prompt.\n"
        f"Output rules:\n - {sentence_rule}\n - {placeholders_rule}\n"
        " - Keep it friendly and brand-safe.\n"
        " - Do not include links or phone numbers.\n"
        " - Do not ask questions.\n"
        "Return only the final message text."
    )

    req = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_instruction}
        ],
        "max_tokens": min(max_tokens, DEEPSEEK_MAX_TOKENS),
        "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "0.6")),
        "n": 1,
    }

    extra_headers = {}
    if OPENROUTER_SITE_URL:
        extra_headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_SITE_NAME:
        extra_headers["X-Title"] = OPENROUTER_SITE_NAME
    if extra_headers:
        req["extra_headers"] = extra_headers

    timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT", "45"))

    for attempt in range(1, 5):
        try:
            await _ensure_min_interval_between_calls()
            resp = await asyncio.wait_for(
                _openai_client.chat.completions.create(**req),
                timeout=timeout_seconds,
            )
            try:
                message = resp.choices[0].message
                text = (message.content or "").strip()
            except Exception:
                text = (getattr(resp, "text", "") or "").strip()
            text = (text or "").strip()
            if not text:
                simple_req = {
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "user", "content": f"Audience: {audience or 'general audience'}. Tone: {tone}. {sentence_rule} Include each of these placeholders exactly once: {', '.join(norm_placeholders)}. No links or questions.\nPrompt: {prompt}"}
                    ],
                    "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "0.6")),
                }
                if extra_headers:
                    simple_req["extra_headers"] = extra_headers
                try:
                    simple_req["max_tokens"] = max(80, min(200, int(req.get("max_tokens") or 180)))
                except Exception:
                    pass
                await _ensure_min_interval_between_calls()
                resp2 = await asyncio.wait_for(
                    _openai_client.chat.completions.create(**simple_req),
                    timeout=timeout_seconds,
                )
                try:
                    msg2 = resp2.choices[0].message
                    text = (msg2.content or "").strip()
                except Exception:
                    text = (getattr(resp2, "text", "") or "").strip()
                text = (text or "").strip()
                if not text:
                    if attempt < 4:
                        base_delay = 1.0 * (2 ** (attempt - 1))
                        jitter = random.uniform(0, 0.4 * base_delay)
                        delay = base_delay + jitter
                        current_max = req.get("max_tokens") or max_tokens
                        req["max_tokens"] = max(int(current_max * 0.7), 40)
                        req["temperature"] = max(0.3, float(req.get("temperature", 0.6)) - 0.05)
                        print(f"[openrouter] empty text; scaling and retrying after {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenRouter returned empty text")

            for ph in norm_placeholders:
                if ph not in text:
                    text = f"Hello {ph}, " + text
                elif text.count(ph) > 1:
                    parts = text.split(ph)
                    text = parts[0] + ph + " ".join(parts[1:]).replace(ph, "")

            return text

        except Exception as e:
            s = str(e)
            is_rate_limited = ("429" in s) or ("rate-limit" in s.lower()) or ("rate limited" in s.lower()) or ("temporarily rate-limited" in s.lower())
            if ("401" in s) or ("403" in s) or ("User not found" in s) or ("invalid" in s.lower()):
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenRouter auth error: {s}")
            if is_rate_limited and attempt < 4:
                base_delay = 1.0 * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.4 * base_delay)
                delay = base_delay + jitter
                current_max = req.get("max_tokens") or max_tokens
                req["max_tokens"] = max(int(current_max * 0.7), 40)
                req["temperature"] = max(0.3, float(req.get("temperature", 0.6)) - 0.05)
                print(f"[openrouter] rate-limited; retrying after {delay:.2f}s...")
                await asyncio.sleep(delay)
                continue
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenRouter error: {s}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "WhatsApp CRM - Message Generator"})

@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    prompt: str = Form(...),
    tone: str = Form("informal"),
    length: str = Form("medium"),
    placeholders: str = Form(""),
    audience: str = Form("")
):
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    mapped_tokens = LENGTH_TOKEN_MAP.get(length, LENGTH_TOKEN_MAP["medium"])
    if length == "medium":
        mapped_tokens = int(mapped_tokens * 1.1)
    elif length == "long":
        mapped_tokens = int(mapped_tokens * 1.15)
    max_tokens = min(mapped_tokens, DEEPSEEK_MAX_TOKENS)

    try:
        message = await generate_with_openrouter_via_client(prompt, tone, max_tokens, placeholders, audience, length)
        source = "openrouter"
        error_msg = None
    except HTTPException as e:
        message = ""
        source = "ai_error"
        error_msg = str(e.detail or e)
    except Exception as e:
        message = ""
        source = "ai_error"
        error_msg = str(e)

    return templates.TemplateResponse(
        "_result.html",
        {
            "request": request,
            "message": message,
            "source": source,
            "length": length,
            "error_msg": error_msg,
            "prompt": prompt,
            "placeholders": placeholders,
            "audience": audience,
        }
    )


