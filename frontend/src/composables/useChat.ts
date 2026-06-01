import { ref, reactive } from 'vue'
import { chatAPI, parseSSEStream } from '../api/chat'
import type { ChatMessage, SourceItem } from '../types/chat'

export function useChat() {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const sessionId = ref('')
  const error = ref('')
  const sources = ref<SourceItem[]>([])
  let abortController: AbortController | null = null

  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
  }

  function newSession() {
    sessionId.value = generateId()
    messages.value = []
    sources.value = []
    error.value = ''
  }

  // Auto-init first session
  if (!sessionId.value) {
    newSession()
  }

  async function sendMessage(query: string) {
    if (!query.trim() || loading.value) return

    // Add user message
    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: query,
      timestamp: Date.now(),
    }
    messages.value.push(userMsg)

    // Add placeholder AI message
    const aiMsgId = generateId()
    const aiMsg: ChatMessage = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      streaming: true,
    }
    messages.value.push(aiMsg)

    loading.value = true
    error.value = ''

    try {
      const response = await chatAPI.streamSend({
        session_id: sessionId.value,
        query,
        stream: true,
        top_k: 5,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }

      // Parse SSE stream
      for await (const event of parseSSEStream(response)) {
        if (event.type === 'sources') {
          sources.value = event.data.sources
        } else if (event.type === 'token') {
          const msg = messages.value.find(m => m.id === aiMsgId)
          if (msg) {
            msg.content += event.data.content
          }
        } else if (event.type === 'done') {
          const msg = messages.value.find(m => m.id === aiMsgId)
          if (msg) {
            msg.streaming = false
          }
        } else if (event.type === 'error') {
          error.value = event.data.content
          const msg = messages.value.find(m => m.id === aiMsgId)
          if (msg) {
            msg.content = `错误: ${event.data.content}`
            msg.streaming = false
          }
        }
      }
    } catch (err: any) {
      error.value = err.message || '请求失败'
      const msg = messages.value.find(m => m.id === aiMsgId)
      if (msg) {
        msg.content = `请求失败: ${error.value}`
        msg.streaming = false
      }
    } finally {
      loading.value = false
    }
  }

  function abortStream() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    const streaming = messages.value.find(m => m.streaming)
    if (streaming) {
      streaming.streaming = false
    }
    loading.value = false
  }

  function clearMessages() {
    messages.value = []
    sources.value = []
    error.value = ''
  }

  return {
    messages,
    loading,
    sessionId,
    error,
    sources,
    sendMessage,
    abortStream,
    clearMessages,
    newSession,
  }
}