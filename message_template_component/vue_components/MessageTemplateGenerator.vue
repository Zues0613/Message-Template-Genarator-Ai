<template>
  <div class="message-template-generator">
    <!-- Generator Form -->
    <div class="generator-card">
      <h2 class="card-title">Generate Message Template</h2>
      
      <form @submit.prevent="generateMessage" class="generator-form">
        <!-- Prompt Input -->
        <div class="form-group">
          <label for="prompt" class="form-label">Prompt *</label>
          <input
            id="prompt"
            v-model="formData.prompt"
            type="text"
            required
            placeholder="e.g. Diwali greetings for customers"
            class="form-input"
            :disabled="loading"
          />
        </div>

        <!-- Placeholders and Audience -->
        <div class="form-row">
          <div class="form-group">
            <label for="placeholders" class="form-label">Placeholders</label>
            <input
              id="placeholders"
              v-model="formData.placeholders"
              type="text"
              placeholder="e.g. name, discount, code"
              class="form-input"
              :disabled="loading"
            />
            <p class="form-hint">Comma-separated. Default: {name}</p>
          </div>

          <div class="form-group">
            <label for="audience" class="form-label">Audience</label>
            <input
              id="audience"
              v-model="formData.audience"
              type="text"
              placeholder="e.g. premium customers, VIP members"
              class="form-input"
              :disabled="loading"
            />
          </div>
        </div>

        <!-- Tone and Length -->
        <div class="form-row">
          <div class="form-group">
            <label for="tone" class="form-label">Tone</label>
            <select
              id="tone"
              v-model="formData.tone"
              class="form-select"
              :disabled="loading"
            >
              <option value="informal">Informal</option>
              <option value="formal">Formal</option>
            </select>
          </div>

          <div class="form-group">
            <label for="length" class="form-label">Length</label>
            <select
              id="length"
              v-model="formData.length"
              class="form-select"
              :disabled="loading"
            >
              <option value="short">Short (1-2 sentences)</option>
              <option value="medium">Medium (4-5 sentences)</option>
              <option value="long">Long (7-9 sentences)</option>
            </select>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="form-actions">
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading || !formData.prompt"
          >
            <span v-if="loading" class="btn-spinner"></span>
            {{ loading ? 'Generating...' : 'Generate' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Result Display -->
    <div v-if="result" class="result-card">
      <div class="result-header">
        <h3 class="result-title">Generated Message</h3>
        <div class="result-meta">
          <span class="meta-item">Length: {{ result.length }}</span>
          <span class="meta-item">Source: {{ result.source }}</span>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="result.error" class="error-message">
        <strong>Error:</strong> {{ result.error }}
      </div>

      <!-- Generated Text -->
      <div class="form-group">
        <label for="generatedText" class="form-label">
          Generated message (editable)
        </label>
        <textarea
          id="generatedText"
          v-model="result.message"
          rows="6"
          class="form-textarea"
          placeholder="Generated message will appear here..."
        ></textarea>
        <p class="form-hint">
          You can edit the message before using it. Keep the placeholders like {name}.
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="result-actions">
        <button
          @click="copyToClipboard"
          class="btn btn-secondary"
          :disabled="!result.message"
        >
          {{ copied ? 'Copied!' : 'Copy to Clipboard' }}
        </button>

        <button
          @click="useMessage"
          class="btn btn-primary"
          :disabled="!result.message"
        >
          Use Message
        </button>

        <button
          @click="retryGeneration"
          class="btn btn-warning"
        >
          Retry
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

// Props
const props = defineProps({
  apiEndpoint: {
    type: String,
    default: '/api/templates/generate'
  },
  defaultTone: {
    type: String,
    default: 'informal'
  },
  defaultLength: {
    type: String,
    default: 'medium'
  }
})

// Emits
const emit = defineEmits(['message-generated', 'message-used', 'error'])

// State
const loading = ref(false)
const result = ref(null)
const copied = ref(false)

const formData = reactive({
  prompt: '',
  tone: props.defaultTone,
  length: props.defaultLength,
  placeholders: '',
  audience: ''
})

// Methods
const generateMessage = async () => {
  if (!formData.prompt.trim()) {
    return
  }

  loading.value = true
  result.value = null

  try {
    const response = await fetch(props.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    result.value = data

    emit('message-generated', data)

    if (!data.success) {
      emit('error', data.error)
    }
  } catch (error) {
    console.error('Error generating message:', error)
    result.value = {
      success: false,
      message: '',
      source: 'error',
      error: error.message,
      prompt: formData.prompt,
      length: formData.length,
      placeholders: formData.placeholders,
      audience: formData.audience,
      metadata: {}
    }
    emit('error', error.message)
  } finally {
    loading.value = false
  }
}

const copyToClipboard = async () => {
  if (!result.value?.message) return

  try {
    await navigator.clipboard.writeText(result.value.message)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
    alert('Failed to copy to clipboard')
  }
}

const useMessage = () => {
  if (!result.value?.message) return
  emit('message-used', result.value.message)
}

const retryGeneration = () => {
  generateMessage()
}
</script>

<style scoped>
.message-template-generator {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.generator-card,
.result-card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #1f2937;
}

.generator-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-input:disabled,
.form-select:disabled,
.form-textarea:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #1f2937;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #111827;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-warning {
  background: white;
  color: #d97706;
  border: 1px solid #fbbf24;
}

.btn-warning:hover:not(:disabled) {
  background: #fffbeb;
}

.btn-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.result-card {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.result-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.result-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.meta-item {
  font-weight: 500;
}

.error-message {
  padding: 0.875rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.375rem;
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.result-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}
</style>

