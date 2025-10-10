# Message Template Generator Component

A reusable, production-ready component for generating AI-powered message templates for WhatsApp CRM and other messaging platforms. Designed to integrate seamlessly into Vue.js applications with FastAPI backends.

## Features

- 🤖 **AI-Powered Generation**: Uses OpenRouter/DeepSeek for intelligent message generation
- 🎨 **Vue.js Ready**: Pre-built Vue 3 components and composables
- ⚡ **FastAPI Integration**: Drop-in router for your FastAPI backend
- 🔧 **Highly Configurable**: Extensive configuration options
- 📦 **Standalone or Embedded**: Use as API, component, or programmatically
- 🎯 **Type Safe**: Full Pydantic models for type safety
- 🔄 **Retry Logic**: Built-in exponential backoff and error handling
- 📝 **Customizable**: Placeholders, tone, length, and audience targeting

## Installation

### Backend (Python)

```bash
pip install fastapi uvicorn openai python-dotenv
```

### Frontend (Vue.js)

The Vue components are self-contained and don't require additional dependencies beyond Vue 3.

## Quick Start

### 1. Backend Setup (FastAPI)

Add the component to your FastAPI application:

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from message_template_component import create_router

app = FastAPI()

# Enable CORS for Vue.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the message template router
router = create_router(api_key="your-openrouter-api-key")
app.include_router(router, prefix="/api/templates")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Or use environment variables:

```python
# .env file
OPENROUTER_API_KEY=sk-or-v1-...
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1

# main.py
from message_template_component import create_router

router = create_router()  # Reads from environment
app.include_router(router, prefix="/api/templates")
```

### 2. Vue.js Integration

#### Option A: Use the Complete Component

```vue
<template>
  <div>
    <MessageTemplateGenerator
      api-endpoint="http://localhost:8000/api/templates/generate"
      @message-generated="handleGenerated"
      @message-used="handleUsed"
    />
  </div>
</template>

<script setup>
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const handleGenerated = (result) => {
  console.log('Message generated:', result.message)
}

const handleUsed = (message) => {
  console.log('Using message:', message)
  // Integrate with your app (e.g., insert into broadcast composer)
}
</script>
```

#### Option B: Use the Composable

```vue
<template>
  <div>
    <input v-model="prompt" placeholder="Enter prompt" />
    <button @click="generate" :disabled="loading">
      {{ loading ? 'Generating...' : 'Generate' }}
    </button>
    
    <div v-if="result">
      <p>{{ message }}</p>
      <button @click="copyToClipboard">Copy</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMessageTemplate } from '@/composables/useMessageTemplate'

const prompt = ref('')

const { generateMessage, loading, result, message, copyToClipboard } = useMessageTemplate({
  apiEndpoint: 'http://localhost:8000/api/templates/generate'
})

const generate = async () => {
  await generateMessage({
    prompt: prompt.value,
    tone: 'informal',
    length: 'medium'
  })
}
</script>
```

#### Option C: Programmatic Usage (Python)

Use the core generator directly in your Python code:

```python
from message_template_component import MessageTemplateGenerator, ComponentConfig

async def generate_template():
    config = ComponentConfig(api_key="your-api-key")
    
    async with MessageTemplateGenerator(config) as generator:
        result = await generator.generate(
            prompt="Birthday wishes for VIP customers",
            tone="formal",
            length="medium",
            placeholders="name,discount",
            audience="VIP customers"
        )
        
        print(result["message"])
        # Output: "Dear {name}, happy birthday! As a valued VIP customer..."

# Or without context manager
async def generate_template_manual():
    config = ComponentConfig.from_env()  # Read from environment
    generator = MessageTemplateGenerator(config)
    
    await generator.initialize()
    
    result = await generator.generate(
        prompt="Diwali greetings",
        tone="informal"
    )
    
    await generator.cleanup()
    
    return result["message"]
```

## Configuration

### Backend Configuration

```python
from message_template_component import ComponentConfig, create_router

# Method 1: Explicit configuration
config = ComponentConfig(
    api_key="your-api-key",
    base_url="https://openrouter.ai/api/v1",
    model="deepseek/deepseek-r1-0528",
    max_tokens=2500,
    temperature=0.6,
    system_prompt="Your custom system prompt...",
    min_interval_seconds=1.5,
    timeout_seconds=45.0,
    enable_fallback_templates=True
)

router = create_router(config=config)

# Method 2: From environment variables
config = ComponentConfig.from_env(
    # Override specific values
    temperature=0.8,
    enable_fallback_templates=True
)

router = create_router(config=config)

# Method 3: Direct parameters
router = create_router(
    api_key="your-key",
    model="deepseek/deepseek-r1-0528"
)
```

### Environment Variables

```bash
# API Configuration
OPENROUTER_API_KEY=sk-or-v1-...
DEEPSEEK_API_KEY=sk-...  # Alternative
OPENAI_API_KEY=sk-...    # Alternative

# Model Configuration
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MAX_TOKENS=2500
DEEPSEEK_TEMPERATURE=0.6

# Rate Limiting & Timeout
OPENROUTER_MIN_INTERVAL=1.5
OPENROUTER_TIMEOUT=45

# Optional Attribution (for OpenRouter)
OPENROUTER_SITE_URL=https://yoursite.com
OPENROUTER_SITE_NAME=Your App Name
```

## API Reference

### Backend API Endpoints

#### `POST /api/templates/generate`

Generate a message template.

**Request Body:**
```json
{
  "prompt": "Birthday wishes for VIP customer",
  "tone": "formal",
  "length": "medium",
  "placeholders": "name,discount",
  "audience": "VIP customers"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dear {name}, happy birthday! As a valued VIP customer, enjoy {discount} off your next purchase.",
  "source": "ai",
  "error": null,
  "prompt": "Birthday wishes for VIP customer",
  "length": "medium",
  "placeholders": "name,discount",
  "audience": "VIP customers",
  "metadata": {
    "tone": "formal",
    "length": "medium",
    "placeholders": ["{name}", "{discount}"],
    "audience": "VIP customers"
  }
}
```

#### `GET /api/templates/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "deepseek/deepseek-r1-0528",
  "ai_enabled": true
}
```

### Vue Composable API

```typescript
const {
  // State
  loading: Ref<boolean>,
  result: Ref<MessageResponse | null>,
  error: Ref<string | null>,
  
  // Computed
  hasResult: ComputedRef<boolean>,
  isSuccess: ComputedRef<boolean>,
  message: ComputedRef<string>,
  
  // Methods
  generateMessage: (params: GenerateParams) => Promise<MessageResponse | null>,
  reset: () => void,
  copyToClipboard: () => Promise<boolean>
} = useMessageTemplate(options)
```

### Python Generator API

```python
class MessageTemplateGenerator:
    async def initialize() -> None
    async def cleanup() -> None
    async def generate(
        prompt: str,
        tone: str = "informal",
        length: str = "medium",
        placeholders: Optional[str] = None,
        audience: Optional[str] = None,
        max_retries: int = 4
    ) -> Dict[str, any]
```

## Advanced Usage

### Custom Styling (Vue Component)

The Vue component uses scoped styles. Override them in your parent component:

```vue
<style>
.message-template-generator {
  /* Your custom styles */
}

.message-template-generator .btn-primary {
  background: your-brand-color;
}
</style>
```

### Error Handling

```vue
<script setup>
import { useMessageTemplate } from '@/composables/useMessageTemplate'

const { generateMessage } = useMessageTemplate({
  apiEndpoint: '/api/templates/generate',
  onSuccess: (result) => {
    console.log('Success:', result)
    // Show success notification
  },
  onError: (error) => {
    console.error('Error:', error)
    // Show error notification
  }
})
</script>
```

### Custom Fallback Templates

```python
from message_template_component import MessageTemplateGenerator, ComponentConfig

config = ComponentConfig(
    api_key="your-key",
    enable_fallback_templates=True
)

generator = MessageTemplateGenerator(config)

# Override default fallback templates
generator._fallback_templates = {
    "custom": "Hello {name}, this is a custom fallback template!",
    "promo": "Hi {name}, special offer: {discount}% off!",
}
```

## File Structure

```
message_template_component/
├── __init__.py              # Package entry point
├── config.py                # Configuration management
├── core.py                  # Core generator logic
├── router.py                # FastAPI router
├── README.md                # This file
├── vue_components/          # Vue.js components
│   ├── index.js
│   ├── MessageTemplateGenerator.vue
│   └── useMessageTemplate.js
└── templates/               # Optional HTML templates (for non-Vue apps)
    ├── base.html
    ├── index.html
    └── _result.html
```

## Integration Examples

See the `examples/` directory for complete integration examples:

- `examples/fastapi_vue_integration.py` - Complete FastAPI + Vue.js setup
- `examples/standalone_usage.py` - Using the generator programmatically
- `examples/vue_app_example/` - Full Vue.js application example

## Troubleshooting

### CORS Issues

Make sure to enable CORS in your FastAPI app:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Key Issues

Check that your API key is properly set:

```python
import os
print(os.getenv("OPENROUTER_API_KEY"))  # Should print your key
```

### Empty Responses

If you're getting empty responses, check:
1. Your API key is valid
2. You have sufficient credits
3. The model name is correct
4. Network connectivity is working

## License

MIT

## Support

For issues and questions, please open an issue on the repository.

