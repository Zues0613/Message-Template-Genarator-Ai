/**
 * Vue 3 Composable for Message Template Generator
 * 
 * This composable provides a simple API to integrate the message template
 * generator into your Vue.js application without using the full component.
 * 
 * @example
 * ```js
 * import { useMessageTemplate } from './useMessageTemplate'
 * 
 * export default {
 *   setup() {
 *     const { generateMessage, loading, result, error } = useMessageTemplate()
 *     
 *     const handleGenerate = async () => {
 *       await generateMessage({
 *         prompt: 'Birthday wishes',
 *         tone: 'formal',
 *         length: 'medium'
 *       })
 *     }
 *     
 *     return { generateMessage, loading, result, error, handleGenerate }
 *   }
 * }
 * ```
 */

import { ref, computed } from 'vue'

export function useMessageTemplate(options = {}) {
  const {
    apiEndpoint = '/api/templates/generate',
    onSuccess = null,
    onError = null
  } = options

  // State
  const loading = ref(false)
  const result = ref(null)
  const error = ref(null)

  // Computed
  const hasResult = computed(() => result.value !== null)
  const isSuccess = computed(() => result.value?.success === true)
  const message = computed(() => result.value?.message || '')

  /**
   * Generate a message template
   * 
   * @param {Object} params - Generation parameters
   * @param {string} params.prompt - Description of the message to generate
   * @param {string} [params.tone='informal'] - Message tone (informal, formal)
   * @param {string} [params.length='medium'] - Message length (short, medium, long)
   * @param {string} [params.placeholders=''] - Comma-separated placeholders
   * @param {string} [params.audience=''] - Target audience description
   * @returns {Promise<Object>} The generation result
   */
  const generateMessage = async (params) => {
    if (!params.prompt) {
      error.value = 'Prompt is required'
      return null
    }

    loading.value = true
    error.value = null
    result.value = null

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: params.prompt,
          tone: params.tone || 'informal',
          length: params.length || 'medium',
          placeholders: params.placeholders || '',
          audience: params.audience || ''
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      result.value = data

      if (data.success) {
        if (onSuccess) {
          onSuccess(data)
        }
      } else {
        error.value = data.error
        if (onError) {
          onError(data.error)
        }
      }

      return data
    } catch (err) {
      console.error('Error generating message:', err)
      error.value = err.message
      
      result.value = {
        success: false,
        message: '',
        source: 'error',
        error: err.message,
        prompt: params.prompt,
        length: params.length || 'medium',
        placeholders: params.placeholders || '',
        audience: params.audience || '',
        metadata: {}
      }

      if (onError) {
        onError(err.message)
      }

      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset the state
   */
  const reset = () => {
    loading.value = false
    result.value = null
    error.value = null
  }

  /**
   * Copy message to clipboard
   * 
   * @returns {Promise<boolean>} True if successful
   */
  const copyToClipboard = async () => {
    if (!message.value) return false

    try {
      await navigator.clipboard.writeText(message.value)
      return true
    } catch (err) {
      console.error('Failed to copy:', err)
      return false
    }
  }

  return {
    // State
    loading,
    result,
    error,
    
    // Computed
    hasResult,
    isSuccess,
    message,
    
    // Methods
    generateMessage,
    reset,
    copyToClipboard
  }
}

/**
 * Create a message template generator service
 * 
 * This creates a singleton-like service that can be shared across components.
 * Useful when you want to maintain state across multiple components.
 * 
 * @param {Object} options - Configuration options
 * @returns {Object} Message template service
 * 
 * @example
 * ```js
 * // services/messageTemplate.js
 * import { createMessageTemplateService } from './useMessageTemplate'
 * 
 * export const messageTemplateService = createMessageTemplateService({
 *   apiEndpoint: '/api/templates/generate'
 * })
 * 
 * // In any component
 * import { messageTemplateService } from '@/services/messageTemplate'
 * 
 * const { generateMessage, loading } = messageTemplateService
 * ```
 */
export function createMessageTemplateService(options = {}) {
  return useMessageTemplate(options)
}

