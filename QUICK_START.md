# Quick Start Guide

## What Was Created

Your standalone Message Template Generator app has been converted into a **reusable component** that's easy to integrate into your larger Vue.js application!

## 📦 Package Structure

```
message_template_component/          ← Your reusable component package
├── __init__.py                      # Package exports
├── config.py                        # Configuration management
├── core.py                          # Core AI generation logic
├── router.py                        # FastAPI router
├── README.md                        # Full documentation
├── vue_components/                  # Vue.js frontend
│   ├── MessageTemplateGenerator.vue # Full UI component
│   ├── useMessageTemplate.js        # Composable for custom UIs
│   └── index.js                     # Exports
└── templates/                       # Optional HTML templates

examples/                            ← Integration examples
├── fastapi_vue_integration.py       # Complete FastAPI + Vue setup
├── standalone_usage.py              # Python-only usage
└── vue_app_example/                 # Full Vue.js example app

INTEGRATION_GUIDE.md                 ← Detailed integration guide
QUICK_START.md                       ← This file
```

## 🚀 Quick Integration (3 Steps)

### Step 1: Backend Integration

Add one line to your FastAPI app:

```python
# Your main FastAPI file
from message_template_component import create_router

app = FastAPI()

# Add this line:
app.include_router(create_router(), prefix="/api/templates")
```

### Step 2: Copy Vue Files

Copy 2 files to your Vue.js project:

```bash
cp message_template_component/vue_components/MessageTemplateGenerator.vue your-app/src/components/
cp message_template_component/vue_components/useMessageTemplate.js your-app/src/composables/
```

### Step 3: Use in Vue Component

```vue
<template>
  <MessageTemplateGenerator
    api-endpoint="/api/templates/generate"
    @message-used="handleMessage"
  />
</template>

<script setup>
import MessageTemplateGenerator from '@/components/MessageTemplateGenerator.vue'

const handleMessage = (message) => {
  // Use the generated message in your app
  console.log('Generated:', message)
}
</script>
```

Done! ✅

## 🎯 Usage Options

### Option 1: Full Component (Pre-built UI)

Perfect if you want a ready-to-use interface:

```vue
<MessageTemplateGenerator api-endpoint="/api/templates/generate" />
```

### Option 2: Composable (Custom UI)

Perfect if you want to build your own UI:

```vue
<script setup>
import { useMessageTemplate } from '@/composables/useMessageTemplate'

const { generateMessage, loading, message } = useMessageTemplate()

const generate = () => {
  generateMessage({ prompt: 'Birthday wishes', tone: 'informal' })
}
</script>
```

### Option 3: Programmatic (Python)

Use directly in Python code:

```python
from message_template_component import MessageTemplateGenerator, ComponentConfig

async with MessageTemplateGenerator(ComponentConfig.from_env()) as gen:
    result = await gen.generate(prompt="Birthday wishes")
    print(result["message"])
```

## ⚙️ Configuration

Create a `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528
```

That's all you need!

## 📚 Documentation

- **Full Documentation**: See `message_template_component/README.md`
- **Integration Guide**: See `INTEGRATION_GUIDE.md`
- **Examples**: Check the `examples/` directory

## 🔧 Run Examples

### Run the Full Example App

Terminal 1 - Backend:
```bash
python examples/fastapi_vue_integration.py
```

Terminal 2 - Frontend:
```bash
cd examples/vue_app_example
npm install
npm run dev
```

Open http://localhost:5173

### Run Python Examples

```bash
python examples/standalone_usage.py
```

## 🎨 Key Features

✅ **Drop-in Integration**: Add to your existing app with minimal changes  
✅ **Vue 3 Ready**: Modern Vue components and composables  
✅ **FastAPI Router**: Clean API integration  
✅ **Type Safe**: Full Pydantic models  
✅ **Configurable**: Extensive configuration options  
✅ **Production Ready**: Error handling, retries, rate limiting  
✅ **Documented**: Comprehensive docs and examples  

## 💡 Integration Ideas

1. **Broadcast Composer**: Add a "Generate with AI" button
2. **Quick Actions**: Generate common message types with one click
3. **Template Library**: Build and save generated templates
4. **Bulk Generation**: Generate multiple messages at once
5. **Preview System**: Show AI suggestions before sending

## 📖 Next Steps

1. ✅ Copy component files to your Vue project
2. ✅ Add router to your FastAPI backend
3. ✅ Configure your API key in `.env`
4. ✅ Test with the example app
5. ✅ Integrate into your application
6. ✅ Customize styling to match your brand

## 🆘 Need Help?

- Check `INTEGRATION_GUIDE.md` for detailed instructions
- Look at `examples/` for working code
- Review `message_template_component/README.md` for API reference

## 🎉 What Changed

**Before**: Standalone app with everything mixed together  
**After**: Clean, reusable component you can drop into any Vue.js app!

Your original app code is still in `app/` and `backend/` directories if you need to reference it.

