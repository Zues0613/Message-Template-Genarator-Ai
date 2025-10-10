# Vue.js Example App - Message Template Generator

This is a complete Vue.js application example showing how to integrate the Message Template Generator component.

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Start the Backend

In the project root directory, start the FastAPI backend:

```bash
# Make sure you have the .env file with OPENROUTER_API_KEY
cd ../..
python examples/fastapi_vue_integration.py
```

The backend will run on `http://localhost:8000`

### 3. Start the Vue Dev Server

```bash
npm run dev
```

The Vue app will run on `http://localhost:5173`

## Features Demonstrated

1. **Full Component Usage**: Shows how to use the complete `MessageTemplateGenerator` component
2. **Composable Usage**: Shows how to use the `useMessageTemplate` composable for custom UIs
3. **Event Handling**: Demonstrates how to handle generated messages and errors
4. **Message History**: Shows how to maintain a list of generated messages

## File Structure

```
src/
├── main.js                          # App entry point
├── App.vue                          # Main app component
├── style.css                        # Global styles
├── components/
│   └── MessageTemplateGenerator.vue # Message generator component
└── composables/
    └── useMessageTemplate.js        # Composable for programmatic usage
```

## Integration into Your App

### Copy Files

Copy these files to your Vue.js project:

1. `src/components/MessageTemplateGenerator.vue` → Your components directory
2. `src/composables/useMessageTemplate.js` → Your composables directory

### Configure API Endpoint

In your Vue component:

```vue
<template>
  <MessageTemplateGenerator
    api-endpoint="http://your-backend.com/api/templates/generate"
    @message-generated="handleGenerated"
  />
</template>

<script setup>
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const handleGenerated = (result) => {
  // Do something with the generated message
  console.log(result.message)
}
</script>
```

Or use the proxy in `vite.config.js`:

```js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://your-backend.com',
        changeOrigin: true
      }
    }
  }
})
```

Then use relative URLs:

```vue
<MessageTemplateGenerator api-endpoint="/api/templates/generate" />
```

## Customization

### Custom Styling

The component uses scoped styles. Override them in your parent component:

```vue
<style>
.message-template-generator {
  /* Your custom styles */
}

.message-template-generator .btn-primary {
  background: #your-brand-color;
}
</style>
```

### Custom Events

Handle component events:

```vue
<MessageTemplateGenerator
  @message-generated="onGenerated"
  @message-used="onUsed"
  @error="onError"
/>
```

### Props

- `api-endpoint`: API endpoint URL (default: `/api/templates/generate`)
- `default-tone`: Default tone selection (default: `informal`)
- `default-length`: Default length selection (default: `medium`)

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Troubleshooting

### CORS Errors

Make sure your FastAPI backend has CORS enabled:

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

### API Connection Errors

Check that:
1. FastAPI backend is running on port 8000
2. The API endpoint URL is correct
3. OPENROUTER_API_KEY is set in your backend .env file

