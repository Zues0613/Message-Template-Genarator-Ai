"""FastAPI router for integrating the message template generator."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from .core import MessageTemplateGenerator
from .config import ComponentConfig


class MessageRequest(BaseModel):
    """Request model for API endpoint."""
    prompt: str
    tone: str = "informal"
    length: str = "medium"
    placeholders: str = ""
    audience: str = ""


class MessageResponse(BaseModel):
    """Response model for API endpoint."""
    success: bool
    message: str
    source: str
    error: Optional[str] = None
    prompt: str
    length: str
    placeholders: str
    audience: str
    metadata: dict = {}


def create_router(
    config: Optional[ComponentConfig] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    prefix: str = "",
    tags: list = None,
    enable_cors: bool = True
) -> APIRouter:
    """Create a FastAPI router for the message template generator.
    
    This function creates a ready-to-use FastAPI router that can be included
    in your main FastAPI application. The router provides JSON API endpoints
    that work seamlessly with Vue.js, React, or any modern frontend framework.
    
    Args:
        config: ComponentConfig instance (if None, will be created from other params)
        api_key: API key for AI service (overrides config)
        base_url: Base URL for API (overrides config)
        model: Model name (overrides config)
        prefix: URL prefix for the router
        tags: Tags for API documentation
        enable_cors: Whether to add CORS middleware (useful for Vue.js development)
        
    Returns:
        FastAPI APIRouter instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> from message_template_component import create_router
        >>> 
        >>> app = FastAPI()
        >>> router = create_router(api_key="your-key")
        >>> app.include_router(router, prefix="/api/templates")
    """
    if config is None:
        config = ComponentConfig.from_env()
    
    # Override with explicit parameters
    if api_key:
        config.api_key = api_key
    if base_url:
        config.base_url = base_url
    if model:
        config.model = model
    
    # Validate config
    config.validate()
    
    # Create router
    router = APIRouter(
        prefix=prefix,
        tags=tags or ["Message Templates"]
    )
    
    # Create generator instance (will be initialized on startup)
    generator = MessageTemplateGenerator(config)
    
    # Startup and shutdown handlers
    @router.on_event("startup")
    async def startup():
        """Initialize the generator on startup."""
        await generator.initialize()
    
    @router.on_event("shutdown")
    async def shutdown():
        """Cleanup the generator on shutdown."""
        await generator.cleanup()
    
    # API endpoint (JSON) - primary endpoint for Vue.js integration
    @router.post("/generate", response_model=MessageResponse)
    async def generate_api(request_data: MessageRequest):
        """Generate message template via JSON API.
        
        This endpoint accepts JSON requests and returns JSON responses.
        Perfect for Vue.js, React, or any modern frontend framework.
        Also works with automation tools like n8n, Zapier, etc.
        
        Example request:
        ```json
        {
            "prompt": "Birthday wishes for VIP customer",
            "tone": "formal",
            "length": "medium",
            "placeholders": "name,discount",
            "audience": "VIP customers"
        }
        ```
        
        Example response:
        ```json
        {
            "success": true,
            "message": "Dear {name}, happy birthday! As a valued VIP customer...",
            "source": "ai",
            "error": null,
            "prompt": "Birthday wishes for VIP customer",
            "length": "medium",
            "placeholders": "name,discount",
            "audience": "VIP customers",
            "metadata": {...}
        }
        ```
        """
        result = await generator.generate(
            prompt=request_data.prompt,
            tone=request_data.tone,
            length=request_data.length,
            placeholders=request_data.placeholders,
            audience=request_data.audience
        )
        
        return MessageResponse(
            success=result["source"] != "error",
            message=result["message"],
            source=result["source"],
            error=result["error"],
            prompt=request_data.prompt,
            length=request_data.length,
            placeholders=request_data.placeholders,
            audience=request_data.audience,
            metadata=result["metadata"]
        )
    
    # Health check endpoint
    @router.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "model": config.model,
            "ai_enabled": generator._client is not None
        }
    
    return router


def create_standalone_router(
    api_key: Optional[str] = None,
    **kwargs
) -> APIRouter:
    """Create a standalone router with default settings.
    
    This is a convenience function for quickly creating a router
    without manually managing configuration.
    
    Args:
        api_key: API key for AI service
        **kwargs: Additional arguments passed to create_router
        
    Returns:
        FastAPI APIRouter instance
    """
    config = ComponentConfig.from_env(api_key=api_key)
    return create_router(config=config, **kwargs)

