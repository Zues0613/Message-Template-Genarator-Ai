"""Configuration management for the Message Template Generator component."""

import os
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class ComponentConfig:
    """Configuration for the Message Template Generator component.
    
    Attributes:
        api_key: API key for AI service (OpenRouter/DeepSeek)
        base_url: Base URL for the API endpoint
        model: Model name to use for generation
        max_tokens: Maximum tokens for generation
        temperature: Temperature for AI generation (0-1)
        system_prompt: System prompt for the AI
        min_interval_seconds: Minimum interval between API calls (rate limiting)
        timeout_seconds: Request timeout in seconds
        site_url: Optional site URL for attribution (OpenRouter)
        site_name: Optional site name for attribution (OpenRouter)
        enable_fallback_templates: Whether to use fallback templates on error
    """
    
    # API Configuration
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "deepseek/deepseek-r1-0528"
    max_tokens: int = 2500
    temperature: float = 0.6
    
    # System prompt
    system_prompt: str = (
        "You are a concise message generator for business broadcast messages. "
        "Generate ONE short friendly message suitable for a WhatsApp broadcast. "
        "Always include the placeholder {name} exactly once. "
        "Keep it 1–2 sentences (unless asked for longer). Avoid links and questions."
    )
    
    # Rate limiting & timeout
    min_interval_seconds: float = 1.5
    timeout_seconds: float = 45.0
    
    # Optional attribution (for OpenRouter)
    site_url: Optional[str] = None
    site_name: Optional[str] = None
    
    # Fallback behavior
    enable_fallback_templates: bool = False
    
    # Length to token mapping
    length_token_map: Dict[str, int] = field(default_factory=lambda: {
        "short": 120,
        "medium": 600,
        "long": 1200
    })
    
    @classmethod
    def from_env(cls, **overrides) -> "ComponentConfig":
        """Create configuration from environment variables.
        
        Environment variables:
            - DEEPSEEK_API_KEY or OPENROUTER_API_KEY: API key
            - DEEPSEEK_BASE_URL or OPENROUTER_URL: Base URL
            - DEEPSEEK_MODEL or OPENROUTER_MODEL: Model name
            - DEEPSEEK_MAX_TOKENS: Max tokens
            - DEEPSEEK_TEMPERATURE: Temperature
            - OPENROUTER_MIN_INTERVAL: Min interval between calls
            - OPENROUTER_TIMEOUT: Request timeout
            - OPENROUTER_SITE_URL: Site URL for attribution
            - OPENROUTER_SITE_NAME: Site name for attribution
        
        Args:
            **overrides: Override any configuration values
            
        Returns:
            ComponentConfig instance
        """
        # Try to find API key from multiple sources
        api_key = (
            os.getenv("OPENROUTER_API_KEY") or
            os.getenv("DEEPSEEK_API_KEY") or
            os.getenv("OPENAI_API_KEY") or
            os.getenv("DEFAULT_DEEPSEEK_API_KEY")
        )
        
        config = cls(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENROUTER_URL") or cls.base_url,
            model=os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENROUTER_MODEL") or cls.model,
            max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", cls.max_tokens)),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", cls.temperature)),
            min_interval_seconds=float(os.getenv("OPENROUTER_MIN_INTERVAL", cls.min_interval_seconds)),
            timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT", cls.timeout_seconds)),
            site_url=os.getenv("OPENROUTER_SITE_URL"),
            site_name=os.getenv("OPENROUTER_SITE_NAME"),
        )
        
        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key and not self.enable_fallback_templates:
            raise ValueError(
                "API key is required. Either provide an API key or enable fallback templates."
            )
        
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        return True

