"""
Complete FastAPI + Vue.js Integration Example
==============================================

This example shows how to integrate the message template generator
component into your existing FastAPI application that serves a Vue.js frontend.

Run this file:
    python examples/fastapi_vue_integration.py

Then access:
    - API: http://localhost:8000/api/templates/generate (POST)
    - Health: http://localhost:8000/api/templates/health (GET)
    - Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the message template component
from message_template_component import create_router, ComponentConfig

# Create FastAPI app
app = FastAPI(
    title="WhatsApp CRM with Message Templates",
    description="Complete application with AI-powered message template generation",
    version="1.0.0"
)

# Enable CORS for Vue.js development
# Adjust origins based on your Vue dev server port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue CLI default
        "http://localhost:3000",  # Alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the message template component
# Option 1: Use environment variables (recommended)
template_router = create_router()

# Option 2: Explicit configuration
# config = ComponentConfig(
#     api_key="your-openrouter-api-key",
#     model="deepseek/deepseek-r1-0528",
#     base_url="https://openrouter.ai/api/v1",
#     temperature=0.6,
#     enable_fallback_templates=True
# )
# template_router = create_router(config=config)

# Include the router in your app
app.include_router(
    template_router,
    prefix="/api/templates",
    tags=["Message Templates"]
)

# Your other application routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp CRM API",
        "version": "1.0.0",
        "endpoints": {
            "templates": "/api/templates/generate",
            "health": "/api/templates/health",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
async def health():
    """Application health check."""
    return {"status": "healthy"}

# Example: Your existing CRM routes
@app.get("/api/contacts")
async def get_contacts():
    """Example: Get contacts."""
    return {"contacts": []}

@app.get("/api/broadcasts")
async def get_broadcasts():
    """Example: Get broadcast campaigns."""
    return {"broadcasts": []}


if __name__ == "__main__":
    # Run the application
    print("🚀 Starting FastAPI server...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔧 Message Templates: http://localhost:8000/api/templates/health")
    print("\n⚠️  Make sure to set OPENROUTER_API_KEY in your .env file")
    
    uvicorn.run(
        "fastapi_vue_integration:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

