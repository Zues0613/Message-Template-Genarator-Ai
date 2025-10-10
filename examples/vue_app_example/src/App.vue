<template>
  <div id="app">
    <header class="app-header">
      <h1>WhatsApp CRM - Message Templates</h1>
      <p>AI-powered message generation for your broadcast campaigns</p>
    </header>

    <main class="app-main">
      <div class="container">
        <!-- Example 1: Using the full component -->
        <section class="example-section">
          <h2>Example 1: Full Component</h2>
          <MessageTemplateGenerator
            :api-endpoint="apiEndpoint"
            @message-generated="handleMessageGenerated"
            @message-used="handleMessageUsed"
            @error="handleError"
          />
        </section>

        <!-- Example 2: Using the composable -->
        <section class="example-section">
          <h2>Example 2: Using Composable</h2>
          <div class="composable-example">
            <div class="input-group">
              <input
                v-model="customPrompt"
                type="text"
                placeholder="Enter your prompt..."
                @keyup.enter="generateWithComposable"
              />
              <button
                @click="generateWithComposable"
                :disabled="composableLoading || !customPrompt"
              >
                {{ composableLoading ? 'Generating...' : 'Generate' }}
              </button>
            </div>

            <div v-if="composableResult" class="result-box">
              <div v-if="composableError" class="error">
                {{ composableError }}
              </div>
              <div v-else>
                <p class="message-text">{{ composableMessage }}</p>
                <button @click="copyComposableMessage">
                  {{ composableCopied ? 'Copied!' : 'Copy' }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Recent Messages -->
        <section class="example-section">
          <h2>Recent Messages</h2>
          <div v-if="recentMessages.length === 0" class="empty-state">
            No messages generated yet. Try generating one above!
          </div>
          <div v-else class="messages-list">
            <div
              v-for="(msg, index) in recentMessages"
              :key="index"
              class="message-item"
            >
              <div class="message-header">
                <span class="message-prompt">{{ msg.prompt }}</span>
                <span class="message-meta">
                  {{ msg.tone }} · {{ msg.length }}
                </span>
              </div>
              <p class="message-content">{{ msg.message }}</p>
              <button
                @click="reuseMessage(msg.message)"
                class="btn-reuse"
              >
                Reuse
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import MessageTemplateGenerator from './components/MessageTemplateGenerator.vue'
import { useMessageTemplate } from './composables/useMessageTemplate'

// Configuration
const apiEndpoint = import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000/api/templates/generate'

// State for recent messages
const recentMessages = ref([])

// Example 1: Full component event handlers
const handleMessageGenerated = (result) => {
  console.log('Message generated:', result)
  
  // Add to recent messages
  recentMessages.value.unshift({
    prompt: result.prompt,
    message: result.message,
    tone: result.metadata?.tone || 'informal',
    length: result.length,
    timestamp: new Date()
  })
  
  // Keep only last 5
  if (recentMessages.value.length > 5) {
    recentMessages.value.pop()
  }
}

const handleMessageUsed = (message) => {
  console.log('Using message:', message)
  
  // Here you would integrate with your app
  // For example: insert into broadcast composer, save to draft, etc.
  alert(`Message will be used:\n\n${message}`)
}

const handleError = (error) => {
  console.error('Error:', error)
  alert(`Error: ${error}`)
}

// Example 2: Using composable
const customPrompt = ref('')
const composableCopied = ref(false)

const {
  loading: composableLoading,
  result: composableResult,
  error: composableError,
  message: composableMessage,
  generateMessage,
  copyToClipboard
} = useMessageTemplate({
  apiEndpoint,
  onSuccess: (result) => {
    console.log('Composable success:', result)
  },
  onError: (error) => {
    console.error('Composable error:', error)
  }
})

const generateWithComposable = async () => {
  if (!customPrompt.value.trim()) return
  
  await generateMessage({
    prompt: customPrompt.value,
    tone: 'informal',
    length: 'medium'
  })
}

const copyComposableMessage = async () => {
  const success = await copyToClipboard()
  if (success) {
    composableCopied.value = true
    setTimeout(() => {
      composableCopied.value = false
    }, 2000)
  }
}

const reuseMessage = (message) => {
  alert(`Reusing message:\n\n${message}`)
  // Integrate with your app
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #1f2937;
}

.app-header p {
  margin: 0.5rem 0 0;
  color: #6b7280;
}

.app-main {
  padding: 2rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.example-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.example-section h2 {
  margin: 0 0 1.5rem;
  font-size: 1.5rem;
  color: #1f2937;
}

.composable-example {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.input-group input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.input-group button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.input-group button:hover:not(:disabled) {
  background: #5568d3;
}

.input-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-box {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.message-text {
  margin: 0 0 1rem;
  line-height: 1.6;
  color: #1f2937;
}

.error {
  color: #dc2626;
  padding: 0.75rem;
  background: #fef2f2;
  border-radius: 0.375rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
  font-style: italic;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-item {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.message-prompt {
  font-weight: 600;
  color: #1f2937;
}

.message-meta {
  font-size: 0.875rem;
  color: #6b7280;
}

.message-content {
  margin: 0.5rem 0 1rem;
  color: #374151;
  line-height: 1.6;
}

.btn-reuse {
  padding: 0.5rem 1rem;
  background: white;
  color: #667eea;
  border: 1px solid #667eea;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reuse:hover {
  background: #667eea;
  color: white;
}
</style>

