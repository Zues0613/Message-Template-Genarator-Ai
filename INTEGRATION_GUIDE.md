# Integration Guide: Message Template Generator for Vue.js Apps

This guide shows you how to integrate the Message Template Generator component into your existing Vue.js application with a FastAPI backend.

## Overview

The component provides:
- **Backend**: FastAPI router with AI-powered message generation
- **Frontend**: Vue 3 component and composable for easy integration
- **API**: RESTful JSON API for maximum flexibility

## Quick Start (5 minutes)

### Step 1: Add to Backend (FastAPI)

In your main FastAPI file:

```python
# backend/main.py (or wherever your FastAPI app is)
from fastapi import FastAPI
from message_template_component import create_router

app = FastAPI()

# Add the message template router
template_router = create_router()
app.include_router(template_router, prefix="/api/templates")
```

That's it for the backend! The component will read configuration from your `.env` file.

### Step 2: Add to Frontend (Vue.js)

Copy the component files to your Vue project:

```bash
# From the message_template_component directory
cp vue_components/MessageTemplateGenerator.vue your-vue-app/src/components/
cp vue_components/useMessageTemplate.js your-vue-app/src/composables/
```

### Step 3: Use in Your Vue Component

```vue
<template>
  <div>
    <MessageTemplateGenerator
      api-endpoint="/api/templates/generate"
      @message-used="handleMessageUsed"
    />
  </div>
</template>

<script setup>
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const handleMessageUsed = (message) => {
  // Insert the message into your broadcast composer
  // or wherever you need it
  console.log('Generated message:', message)
}
</script>
```

Done! You now have AI-powered message generation in your app.

## Detailed Integration

### Backend Setup

#### 1. Environment Configuration

Create or update your `.env` file:

```env
# Required: Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Optional: Customize the model
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528

# Optional: Other settings
DEEPSEEK_TEMPERATURE=0.6
DEEPSEEK_MAX_TOKENS=2500
```

#### 2. CORS Configuration

If your Vue.js dev server runs on a different port, enable CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue CLI
        # Add your production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3. Advanced Configuration

For more control:

```python
from message_template_component import create_router, ComponentConfig

config = ComponentConfig(
    api_key="your-key",
    model="deepseek/deepseek-r1-0528",
    temperature=0.7,
    system_prompt="Custom system prompt...",
    enable_fallback_templates=True
)

router = create_router(config=config)
app.include_router(router, prefix="/api/templates")
```

### Frontend Setup

#### 1. Configure Vite Proxy (Recommended)

In `vite.config.js`:

```js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Your FastAPI server
        changeOrigin: true
      }
    }
  }
})
```

This allows you to use relative URLs like `/api/templates/generate` instead of full URLs.

#### 2. Component Integration Methods

**Method A: Full Component (Easiest)**

Use the pre-built component with all UI:

```vue
<template>
  <MessageTemplateGenerator
    api-endpoint="/api/templates/generate"
    default-tone="formal"
    default-length="medium"
    @message-generated="onGenerated"
    @message-used="onUsed"
    @error="onError"
  />
</template>

<script setup>
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const onGenerated = (result) => {
  console.log('Generated:', result.message)
  // Track analytics, save to history, etc.
}

const onUsed = (message) => {
  // Insert message into your broadcast composer
  insertIntoBroadcast(message)
}

const onError = (error) => {
  // Show error notification
  showNotification('Error generating message', error)
}
</script>
```

**Method B: Composable (Custom UI)**

Build your own UI using the composable:

```vue
<template>
  <div class="custom-generator">
    <input v-model="prompt" placeholder="Enter prompt" />
    <button @click="generate" :disabled="loading">
      Generate
    </button>
    
    <div v-if="hasResult" class="result">
      <textarea v-model="message" />
      <button @click="copyToClipboard">Copy</button>
      <button @click="use">Use Message</button>
    </div>
    
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMessageTemplate } from '@/composables/useMessageTemplate'

const prompt = ref('')

const {
  loading,
  hasResult,
  message,
  error,
  generateMessage,
  copyToClipboard
} = useMessageTemplate({
  apiEndpoint: '/api/templates/generate'
})

const generate = async () => {
  await generateMessage({
    prompt: prompt.value,
    tone: 'informal',
    length: 'medium'
  })
}

const use = () => {
  // Use the message in your app
  insertIntoBroadcast(message.value)
}
</script>
```

**Method C: Service (Shared State)**

Create a shared service for use across multiple components:

```js
// services/messageTemplate.js
import { createMessageTemplateService } from '@/composables/useMessageTemplate'

export const messageTemplateService = createMessageTemplateService({
  apiEndpoint: '/api/templates/generate',
  onSuccess: (result) => {
    console.log('Message generated:', result.message)
  }
})
```

Use in any component:

```vue
<script setup>
import { messageTemplateService } from '@/services/messageTemplate'

const { generateMessage, loading, message } = messageTemplateService

// Now you can generate messages from anywhere
</script>
```

## Integration with Your Existing App

### Scenario 1: Broadcast Composer

Add message generation to your broadcast message composer:

```vue
<template>
  <div class="broadcast-composer">
    <!-- Your existing broadcast UI -->
    <textarea v-model="broadcastMessage" placeholder="Message content" />
    
    <!-- Add a button to open the generator -->
    <button @click="showGenerator = true">✨ Generate with AI</button>
    
    <!-- Generator modal/drawer -->
    <Modal v-model:show="showGenerator">
      <MessageTemplateGenerator
        api-endpoint="/api/templates/generate"
        @message-used="insertGenerated"
      />
    </Modal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const broadcastMessage = ref('')
const showGenerator = ref(false)

const insertGenerated = (message) => {
  broadcastMessage.value = message
  showGenerator.value = false
}
</script>
```

### Scenario 2: Quick Actions Menu

Add to a quick actions menu:

```vue
<template>
  <div class="quick-actions">
    <DropdownMenu>
      <DropdownItem @click="generateBirthday">Birthday Message</DropdownItem>
      <DropdownItem @click="generatePromo">Promo Message</DropdownItem>
      <DropdownItem @click="generateCustom">Custom Message</DropdownItem>
    </DropdownMenu>
  </div>
</template>

<script setup>
import { useMessageTemplate } from '@/composables/useMessageTemplate'

const { generateMessage } = useMessageTemplate()

const generateBirthday = async () => {
  const result = await generateMessage({
    prompt: 'Birthday wishes for customer',
    tone: 'informal',
    length: 'short'
  })
  if (result) {
    insertIntoBroadcast(result.message)
  }
}

const generatePromo = async () => {
  const result = await generateMessage({
    prompt: 'Promotional message with discount',
    tone: 'formal',
    length: 'medium',
    placeholders: 'name,discount,code'
  })
  if (result) {
    insertIntoBroadcast(result.message)
  }
}
</script>
```

### Scenario 3: Template Library

Build a template library with AI generation:

```vue
<template>
  <div class="template-library">
    <!-- Saved templates -->
    <div v-for="template in templates" :key="template.id">
      {{ template.message }}
    </div>
    
    <!-- Generate new button -->
    <button @click="showGenerator = true">+ Generate New Template</button>
    
    <MessageTemplateGenerator
      v-if="showGenerator"
      @message-generated="saveAsTemplate"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const templates = ref([])

const saveAsTemplate = (result) => {
  templates.value.push({
    id: Date.now(),
    message: result.message,
    prompt: result.prompt,
    createdAt: new Date()
  })
  
  // Save to backend
  api.post('/templates', { message: result.message })
}
</script>
```

## API Reference

### REST API

**Endpoint**: `POST /api/templates/generate`

**Request**:
```json
{
  "prompt": "Birthday wishes for VIP customer",
  "tone": "formal",
  "length": "medium",
  "placeholders": "name,discount",
  "audience": "VIP customers"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Dear {name}, happy birthday!...",
  "source": "ai",
  "error": null,
  "prompt": "Birthday wishes for VIP customer",
  "length": "medium",
  "placeholders": "name,discount",
  "audience": "VIP customers",
  "metadata": {}
}
```

### Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `api-endpoint` | String | `/api/templates/generate` | API endpoint URL |
| `default-tone` | String | `informal` | Default tone selection |
| `default-length` | String | `medium` | Default length selection |

### Component Events

| Event | Payload | Description |
|-------|---------|-------------|
| `message-generated` | `MessageResponse` | Fired when message is generated |
| `message-used` | `string` | Fired when "Use Message" is clicked |
| `error` | `string` | Fired on error |

### Composable API

```typescript
const {
  loading: Ref<boolean>,
  result: Ref<MessageResponse | null>,
  error: Ref<string | null>,
  hasResult: ComputedRef<boolean>,
  isSuccess: ComputedRef<boolean>,
  message: ComputedRef<string>,
  generateMessage: (params) => Promise<MessageResponse>,
  reset: () => void,
  copyToClipboard: () => Promise<boolean>
} = useMessageTemplate(options)
```

## Production Deployment

### Backend

1. Set environment variables in your production environment
2. Use a production-grade ASGI server (Uvicorn with Gunicorn)
3. Configure proper CORS for your domain

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend

1. Build your Vue app: `npm run build`
2. Set the production API endpoint in your environment variables
3. Ensure your API endpoint is accessible from your frontend domain

## Troubleshooting

### Issue: CORS errors in browser console

**Solution**: Enable CORS in FastAPI (see above)

### Issue: 503 Service Unavailable

**Solution**: Check that `OPENROUTER_API_KEY` is set in your backend `.env` file

### Issue: Empty responses from API

**Solution**: 
1. Verify API key is valid and has credits
2. Check model name is correct
3. Review backend logs for errors

### Issue: Component not rendering

**Solution**: 
1. Ensure Vue 3 is installed
2. Check that component is properly imported
3. Verify file paths are correct

## Support

For issues, questions, or contributions, please refer to the main README.md or open an issue on the repository.

