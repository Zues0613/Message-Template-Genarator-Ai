"""
Message Template Generator Component
=====================================

A reusable component for generating AI-powered message templates for WhatsApp CRM.

Usage:
    from message_template_component import MessageTemplateGenerator, create_router
    
    # Option 1: Use as a Python API
    generator = MessageTemplateGenerator(api_key="your-api-key")
    message = await generator.generate(prompt="Diwali greetings", tone="informal")
    
    # Option 2: Integrate into FastAPI
    app = FastAPI()
    app.include_router(create_router(api_key="your-api-key"), prefix="/templates")
"""

from .core import MessageTemplateGenerator
from .router import create_router
from .config import ComponentConfig

__version__ = "1.0.0"
__all__ = ["MessageTemplateGenerator", "create_router", "ComponentConfig"]

