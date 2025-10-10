"""Core message template generator component."""

import asyncio
import time
import random
from typing import Optional, Dict, List
import openai

from .config import ComponentConfig


class MessageTemplateGenerator:
    """Core component for generating AI-powered message templates.
    
    This class encapsulates all the logic for generating message templates
    using AI models. It can be used standalone or integrated into a larger
    application.
    
    Example:
        >>> config = ComponentConfig(api_key="your-key")
        >>> generator = MessageTemplateGenerator(config)
        >>> await generator.initialize()
        >>> message = await generator.generate(
        ...     prompt="Birthday wishes",
        ...     tone="informal",
        ...     length="medium"
        ... )
        >>> await generator.cleanup()
    """
    
    def __init__(self, config: ComponentConfig):
        """Initialize the message template generator.
        
        Args:
            config: Configuration for the generator
        """
        self.config = config
        self.config.validate()
        
        self._client: Optional[openai.AsyncOpenAI] = None
        self._rate_limit_lock = asyncio.Lock()
        self._last_call_ts: float = 0.0
        self._initialized = False
        
        # Fallback templates
        self._fallback_templates = {
            "diwali": "Hello {name}, Diwali greetings! We wish you the best holiday. Namaste!",
            "birthday": "Hello {name}, happy birthday! Wishing you a wonderful year ahead.",
            "promo": "Hello {name}, enjoy an exclusive {discount} off on your next order. Use code: {code}.",
            "generic": "Hello {name}, hope you are doing well. We have an update for you."
        }
    
    async def initialize(self) -> None:
        """Initialize the AI client.
        
        Should be called before using the generator.
        Can also be used as an async context manager.
        """
        if self._initialized:
            return
        
        if self.config.api_key:
            self._client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            print(f"[MessageTemplateGenerator] Client initialized (model: {self.config.model})")
        else:
            self._client = None
            print("[MessageTemplateGenerator] No API key provided; AI disabled")
        
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources.
        
        Should be called when done using the generator.
        """
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                print(f"[MessageTemplateGenerator] Cleanup warning: {e}")
            self._client = None
        
        self._initialized = False
        print("[MessageTemplateGenerator] Client closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def _ensure_min_interval(self) -> None:
        """Ensure minimum interval between API calls (rate limiting)."""
        async with self._rate_limit_lock:
            now = time.monotonic()
            wait_for = (self._last_call_ts + self.config.min_interval_seconds) - now
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_call_ts = time.monotonic()
    
    def _normalize_placeholders(self, placeholders: Optional[str]) -> List[str]:
        """Normalize placeholder strings.
        
        Args:
            placeholders: Comma-separated placeholder string
            
        Returns:
            List of normalized placeholders in {name} format
        """
        if not placeholders:
            return ["{name}"]
        
        raw = [p.strip() for p in placeholders.split(",") if p.strip()]
        if not raw:
            return ["{name}"]
        
        normalized = []
        for ph in raw:
            if not (ph.startswith("{") and ph.endswith("}")):
                ph = "{" + ph.strip("{} ") + "}"
            if ph not in normalized:
                normalized.append(ph)
        
        return normalized
    
    def _get_sentence_rule(self, length: str) -> str:
        """Get sentence count rule based on length.
        
        Args:
            length: Length setting (short, medium, long)
            
        Returns:
            Sentence rule description
        """
        if length == "medium":
            return "Write 4 to 5 complete sentences."
        elif length == "long":
            return "Write 7 to 9 complete sentences."
        else:
            return "Write 1 to 2 concise sentences."
    
    def _enforce_placeholders(self, text: str, placeholders: List[str]) -> str:
        """Ensure each placeholder appears exactly once in the text.
        
        Args:
            text: Generated text
            placeholders: List of required placeholders
            
        Returns:
            Text with enforced placeholders
        """
        for ph in placeholders:
            if ph not in text:
                # Add missing placeholder at the beginning
                text = f"Hello {ph}, " + text
            elif text.count(ph) > 1:
                # Remove duplicate placeholders
                parts = text.split(ph)
                text = parts[0] + ph + " ".join(parts[1:]).replace(ph, "")
        
        return text
    
    def _detect_keyword(self, prompt: str) -> str:
        """Detect keyword from prompt for fallback templates.
        
        Args:
            prompt: User prompt
            
        Returns:
            Detected keyword
        """
        p = (prompt or "").lower()
        if "diwali" in p or "deepavali" in p:
            return "diwali"
        if "birthday" in p:
            return "birthday"
        if "promo" in p or "discount" in p or "offer" in p:
            return "promo"
        return "generic"
    
    async def generate(
        self,
        prompt: str,
        tone: str = "informal",
        length: str = "medium",
        placeholders: Optional[str] = None,
        audience: Optional[str] = None,
        max_retries: int = 4
    ) -> Dict[str, any]:
        """Generate a message template.
        
        Args:
            prompt: Description of what message to generate
            tone: Message tone (informal, formal)
            length: Message length (short, medium, long)
            placeholders: Comma-separated placeholders (e.g., "name,discount,code")
            audience: Target audience description
            max_retries: Maximum number of retries on failure
            
        Returns:
            Dictionary with:
                - message: Generated message text
                - source: Generation source (ai, fallback, error)
                - error: Error message if any
                - metadata: Additional metadata
                
        Raises:
            RuntimeError: If generator is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Generator not initialized. Call initialize() first.")
        
        prompt = prompt.strip()
        if not prompt:
            return {
                "message": "",
                "source": "error",
                "error": "Prompt is required",
                "metadata": {}
            }
        
        # Normalize inputs
        norm_placeholders = self._normalize_placeholders(placeholders)
        
        # Calculate token budget
        mapped_tokens = self.config.length_token_map.get(length, 600)
        if length == "medium":
            mapped_tokens = int(mapped_tokens * 1.1)
        elif length == "long":
            mapped_tokens = int(mapped_tokens * 1.15)
        max_tokens = min(mapped_tokens, self.config.max_tokens)
        
        # Try AI generation if client is available
        if self._client:
            try:
                message = await self._generate_with_ai(
                    prompt=prompt,
                    tone=tone,
                    length=length,
                    max_tokens=max_tokens,
                    placeholders=norm_placeholders,
                    audience=audience,
                    max_retries=max_retries
                )
                return {
                    "message": message,
                    "source": "ai",
                    "error": None,
                    "metadata": {
                        "tone": tone,
                        "length": length,
                        "placeholders": norm_placeholders,
                        "audience": audience
                    }
                }
            except Exception as e:
                error_msg = str(e)
                print(f"[MessageTemplateGenerator] AI generation failed: {error_msg}")
                
                # Try fallback if enabled
                if self.config.enable_fallback_templates:
                    keyword = self._detect_keyword(prompt)
                    fallback_msg = self._fallback_templates.get(keyword, self._fallback_templates["generic"])
                    return {
                        "message": fallback_msg,
                        "source": "fallback",
                        "error": f"AI failed, using fallback: {error_msg}",
                        "metadata": {"keyword": keyword}
                    }
                
                # Return error
                return {
                    "message": "",
                    "source": "error",
                    "error": error_msg,
                    "metadata": {}
                }
        
        # No AI client and fallback enabled
        if self.config.enable_fallback_templates:
            keyword = self._detect_keyword(prompt)
            fallback_msg = self._fallback_templates.get(keyword, self._fallback_templates["generic"])
            return {
                "message": fallback_msg,
                "source": "fallback",
                "error": None,
                "metadata": {"keyword": keyword}
            }
        
        # No AI and no fallback
        return {
            "message": "",
            "source": "error",
            "error": "AI client not available and fallback templates disabled",
            "metadata": {}
        }
    
    async def _generate_with_ai(
        self,
        prompt: str,
        tone: str,
        length: str,
        max_tokens: int,
        placeholders: List[str],
        audience: Optional[str],
        max_retries: int
    ) -> str:
        """Generate message using AI API.
        
        Args:
            prompt: User prompt
            tone: Message tone
            length: Message length
            max_tokens: Token budget
            placeholders: List of placeholders
            audience: Target audience
            max_retries: Maximum retries
            
        Returns:
            Generated message text
            
        Raises:
            Exception: If generation fails after all retries
        """
        sentence_rule = self._get_sentence_rule(length)
        placeholders_rule = " ".join([
            f"Include the exact placeholder {ph} exactly once."
            for ph in placeholders
        ])
        
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
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_instruction}
            ],
            "max_tokens": max_tokens,
            "temperature": self.config.temperature,
            "n": 1,
        }
        
        # Add optional headers
        extra_headers = {}
        if self.config.site_url:
            extra_headers["HTTP-Referer"] = self.config.site_url
        if self.config.site_name:
            extra_headers["X-Title"] = self.config.site_name
        if extra_headers:
            req["extra_headers"] = extra_headers
        
        last_exc = None
        
        for attempt in range(1, max_retries + 1):
            try:
                # Respect rate limiting
                await self._ensure_min_interval()
                
                # Make API call
                resp = await asyncio.wait_for(
                    self._client.chat.completions.create(**req),
                    timeout=self.config.timeout_seconds,
                )
                
                # Extract text
                try:
                    message = resp.choices[0].message
                    text = (message.content or "").strip()
                except Exception:
                    text = (getattr(resp, "text", "") or "").strip()
                
                text = (text or "").strip()
                
                # If empty, try simplified request
                if not text:
                    simple_req = {
                        "model": self.config.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Audience: {audience or 'general audience'}. Tone: {tone}. {sentence_rule} Include each of these placeholders exactly once: {', '.join(placeholders)}. No links or questions.\nPrompt: {prompt}"
                            }
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": max(80, min(200, max_tokens)),
                    }
                    if extra_headers:
                        simple_req["extra_headers"] = extra_headers
                    
                    await self._ensure_min_interval()
                    resp2 = await asyncio.wait_for(
                        self._client.chat.completions.create(**simple_req),
                        timeout=self.config.timeout_seconds,
                    )
                    
                    try:
                        msg2 = resp2.choices[0].message
                        text = (msg2.content or "").strip()
                    except Exception:
                        text = (getattr(resp2, "text", "") or "").strip()
                    
                    text = (text or "").strip()
                
                # Still empty after retry?
                if not text:
                    if attempt < max_retries:
                        # Scale down and retry
                        delay = self._calculate_backoff(attempt)
                        req["max_tokens"] = max(int(req["max_tokens"] * 0.7), 40)
                        req["temperature"] = max(0.3, req["temperature"] - 0.05)
                        print(f"[MessageTemplateGenerator] Empty response, retrying after {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RuntimeError("API returned empty text after all retries")
                
                # Enforce placeholders
                text = self._enforce_placeholders(text, placeholders)
                
                return text
                
            except asyncio.TimeoutError as e:
                last_exc = e
                if attempt < max_retries:
                    delay = self._calculate_backoff(attempt)
                    req["max_tokens"] = max(int(req["max_tokens"] * 0.7), 40)
                    req["temperature"] = max(0.3, req["temperature"] - 0.05)
                    print(f"[MessageTemplateGenerator] Timeout, retrying after {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise RuntimeError(f"Request timeout after {max_retries} attempts")
                    
            except Exception as e:
                last_exc = e
                s = str(e)
                
                # Check for auth errors (don't retry)
                if "401" in s or "403" in s or "invalid" in s.lower():
                    raise RuntimeError(f"Authentication error: {s}")
                
                # Check for rate limiting (retry)
                is_rate_limited = "429" in s or "rate" in s.lower()
                if is_rate_limited and attempt < max_retries:
                    delay = self._calculate_backoff(attempt)
                    req["max_tokens"] = max(int(req["max_tokens"] * 0.7), 40)
                    req["temperature"] = max(0.3, req["temperature"] - 0.05)
                    print(f"[MessageTemplateGenerator] Rate limited, retrying after {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                # Other errors
                if attempt < max_retries:
                    delay = self._calculate_backoff(attempt)
                    print(f"[MessageTemplateGenerator] Error: {s}, retrying after {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise RuntimeError(f"Generation failed: {s}")
        
        # Should not reach here
        raise RuntimeError(f"Generation failed after {max_retries} attempts: {last_exc}")
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter.
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        base_delay = 1.0 * (2 ** (attempt - 1))
        jitter = random.uniform(0, 0.4 * base_delay)
        return base_delay + jitter

