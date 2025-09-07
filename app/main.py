# app/main.py
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import pathlib
import os
from dotenv import load_dotenv
import asyncio
import time
import random
import openai
from typing import Optional

# Load .env
load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent

app = FastAPI(title="WhatsApp CRM - Message Generator")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ---- Config (read from env) ----
# Support both DEEPSEEK_API_KEY and DEFAULT_DEEPSEEK_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEFAULT_DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"))
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2500"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME")

# System prompt for AI generation
SYSTEM_PROMPT = (
    "You are a concise message generator for business broadcast messages. "
    "Generate ONE short friendly message suitable for a WhatsApp broadcast. "
    "Always include the placeholder {name} exactly once. "
    "Keep it 1–2 sentences (unless asked for longer). Avoid links and questions."
)

# Fallback deterministic templates
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

# map length to token budgets (scaled up for richer outputs)
LENGTH_TOKEN_MAP = {
    "short": 120,
    "medium": 600,
    "long": 1200
}

# ---- OpenAI-compatible client setup (based on your working test) ----
_openai_client: Optional[openai.AsyncOpenAI] = None

async def startup_openrouter_client():
    global _openai_client
    if DEEPSEEK_API_KEY:
        # instantiate AsyncOpenAI client with base_url (OpenRouter-compatible)
        _openai_client = openai.AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        print("[openrouter] client initialized (base_url:", DEEPSEEK_BASE_URL, "model:", DEEPSEEK_MODEL, ")")
        # print first 8 chars of key for debug (safe to confirm origin)
        try:
            print("[openrouter] key prefix:", DEEPSEEK_API_KEY[:8])
        except Exception:
            pass
    else:
        _openai_client = None
        print("[openrouter] no DEEPSEEK_API_KEY found; AI disabled, using rule-based fallback")

async def shutdown_openrouter_client():
    global _openai_client
    if _openai_client:
        await _openai_client.aclose()
        _openai_client = None
        print("[openrouter] client closed")

app.add_event_handler("startup", startup_openrouter_client)
app.add_event_handler("shutdown", shutdown_openrouter_client)

# ---- AI call helper using the same client you used in the smoke test ----
from fastapi import status

# Simple in-process rate limiter to avoid triggering upstream 429s too often
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
    """
    Call OpenRouter via openai.AsyncOpenAI client with retry on transient 429s (exponential backoff).
    Returns the generated text. Raises HTTPException on unrecoverable or final errors.
    """
    global _openai_client
    if not _openai_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI client not initialized")

    # Prepare placeholders
    raw_placeholders = [p.strip() for p in (placeholders or "").split(",") if p.strip()]
    if not raw_placeholders:
        raw_placeholders = ["{name}"]
    norm_placeholders = []
    for ph in raw_placeholders:
        ph = ph if (ph.startswith("{") and ph.endswith("}")) else ("{" + ph.strip("{} ") + "}")
        if ph not in norm_placeholders:
            norm_placeholders.append(ph)

    # Length guidance
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

    # optional attribution headers
    extra_headers = {}
    if OPENROUTER_SITE_URL:
        extra_headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_SITE_NAME:
        extra_headers["X-Title"] = OPENROUTER_SITE_NAME
    if extra_headers:
        req["extra_headers"] = extra_headers

    max_retries = 4
    backoff_base = 1.0
    last_exc = None

    timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT", "45"))
    for attempt in range(1, max_retries + 1):
        try:
            # Respect a minimal interval between upstream calls
            await _ensure_min_interval_between_calls()
            resp = await asyncio.wait_for(
                _openai_client.chat.completions.create(**req),
                timeout=timeout_seconds,
            )
            # parse text
            try:
                message = resp.choices[0].message
                text = (message.content or "").strip()
            except Exception:
                text = (getattr(resp, "text", "") or "") or ""
            text = (text or "").strip()
            if not text:
                # Try a simplified request mirroring the working test script
                simple_messages = [
                    {"role": "user", "content": f"Audience: {audience or 'general audience'}. Tone: {tone}. {sentence_rule} Include each of these placeholders exactly once: {', '.join(norm_placeholders)}. No links or questions.\nPrompt: {prompt}"}
                ]
                simple_req = {
                    "model": DEEPSEEK_MODEL,
                    "messages": simple_messages,
                    "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "0.6")),
                }
                if extra_headers:
                    simple_req["extra_headers"] = extra_headers
                # Keep a conservative token budget if available
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
                    # Treat empty text as transient; backoff and retry if attempts remain
                    last_exc = RuntimeError("OpenRouter returned empty text")
                    if attempt < max_retries:
                        base_delay = backoff_base * (2 ** (attempt - 1))
                        jitter = random.uniform(0, 0.4 * base_delay)
                        delay = base_delay + jitter
                        # Progressive scaling to ease upstream
                        try:
                            current_max = req.get("max_tokens") or max_tokens
                            scaled = max(int(current_max * 0.7), 40)
                            req["max_tokens"] = scaled
                            req["temperature"] = max(0.3, float(req.get("temperature", 0.6)) - 0.05)
                            print(f"[openrouter] empty text; scaling max_tokens {current_max}->{scaled}, temp->{req['temperature']}")
                        except Exception:
                            pass
                        print(f"[openrouter] empty text (attempt {attempt}/{max_retries}). Retrying after {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenRouter returned empty text")

            # enforce placeholders exactly once
            for ph in norm_placeholders:
                if ph not in text:
                    text = f"Hello {ph}, " + text
                elif text.count(ph) > 1:
                    parts = text.split(ph)
                    text = parts[0] + ph + " ".join(parts[1:]).replace(ph, "")

            # log preview and usage (optional)
            preview = text if len(text) <= 300 else text[:300] + "..."
            print(f"[openrouter] preview: {preview}")
            try:
                usage = getattr(resp, "usage", {}) or {}
                if usage:
                    total = usage.get("total_tokens") or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
                    print(f"[openrouter] token usage: {total} (raw: {usage})")
            except Exception:
                pass

            return text

        except asyncio.TimeoutError as e:
            last_exc = e
            # scale down and retry
            try:
                current_max = req.get("max_tokens") or max_tokens
                scaled = max(int(current_max * 0.7), 40)
                req["max_tokens"] = scaled
                req["temperature"] = max(0.3, float(req.get("temperature", 0.6)) - 0.05)
                print(f"[openrouter] timeout; scaling max_tokens {current_max}->{scaled}, temp->{req['temperature']}")
            except Exception:
                pass
            if attempt < max_retries:
                base_delay = backoff_base * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.4 * base_delay)
                delay = base_delay + jitter
                print(f"[openrouter] request timed out (attempt {attempt}/{max_retries}). Retrying after {delay:.2f}s...")
                await asyncio.sleep(delay)
                continue
            print(f"[openrouter] final timeout after {attempt} attempts")
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="OpenRouter timeout")
        except Exception as e:
            last_exc = e
            s = str(e)
            # detect transient rate-limit/upstream throttle
            is_rate_limited = ("429" in s) or ("rate-limit" in s.lower()) or ("rate limited" in s.lower()) or ("temporarily rate-limited" in s.lower())

            # unrecoverable auth/permission -> stop immediately
            if "401" in s or "403" in s or "User not found" in s or "invalid" in s.lower():
                print(f"[openrouter] unrecoverable auth error: {s}")
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenRouter auth error: {s}")

            # retry on rate-limit
            if is_rate_limited and attempt < max_retries:
                # respect Retry-After if present on exception.response.headers
                retry_after = None
                try:
                    resp_obj = getattr(e, "response", None)
                    if resp_obj is not None:
                        headers = getattr(resp_obj, "headers", {}) or {}
                        retry_after = headers.get("Retry-After") or headers.get("retry-after")
                except Exception:
                    pass

                if retry_after and str(retry_after).replace('.', '', 1).isdigit():
                    delay = float(retry_after)
                else:
                    base_delay = backoff_base * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.4 * base_delay)
                    delay = base_delay + jitter

                # Progressive scaling: reduce token budget to ease throttling
                try:
                    current_max = req.get("max_tokens") or max_tokens
                    scaled = max(int(current_max * 0.7), 40)
                    req["max_tokens"] = scaled
                    # Slightly lower temperature on retries for determinism
                    req["temperature"] = max(0.3, float(req.get("temperature", 0.6)) - 0.05)
                    print(f"[openrouter] scaling max_tokens from {current_max} -> {scaled}, temp -> {req['temperature']}")
                except Exception:
                    pass

                print(f"[openrouter] rate-limited (attempt {attempt}/{max_retries}). Retrying after {delay:.2f}s...")
                await asyncio.sleep(delay)
                continue

            # non-retryable or retries exhausted -> return error to caller
            print(f"[openrouter] final error after {attempt} attempts: {s}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenRouter error: {s}")

    # if loop finishes unexpectedly
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenRouter error (final): {last_exc}")
# ---- Routes ----
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "WhatsApp CRM - Message Generator"})

@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    prompt: str = Form(...),
    tone: str = Form("informal"),
    length: str = Form("medium"),
    placeholders: str = Form("") ,
    audience: str = Form("")
):
    """
    Always generate via AI. If AI call fails, show an error message in UI (no rule-based fallback).
    """
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    mapped_tokens = LENGTH_TOKEN_MAP.get(length, LENGTH_TOKEN_MAP["medium"])
    # Add a little buffer to help achieve sentence counts
    if length == "medium":
        mapped_tokens = int(mapped_tokens * 1.1)
    elif length == "long":
        mapped_tokens = int(mapped_tokens * 1.15)
    max_tokens = min(mapped_tokens, DEEPSEEK_MAX_TOKENS)

    # Always call AI (even for 'short')
    try:
        message = await generate_with_openrouter_via_client(prompt, tone, max_tokens, placeholders, audience, length)
        source = "openrouter"
        error_msg = None
    except HTTPException as e:
        # show clear error to user (no fallback)
        print("OpenRouter error:", e.detail)
        message = ""  # keep empty so UI shows editable empty box
        source = "ai_error"
        error_msg = str(e.detail or e)
    except Exception as e:
        print("Unexpected AI error:", e)
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
