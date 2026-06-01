import apiClient from './index'
import type { ChatRequest, ChatResponse, ChatSession, ChatSessionDetail, CacheStats } from '../types/chat'

export const chatAPI = {
  /**
   * Non-streaming chat (POST /api/v1/chat/)
   */
  async send(data: ChatRequest): Promise<ChatResponse> {
    return apiClient.post('/api/v1/chat/', data)
  },

  /**
   * Streaming chat via SSE (POST /api/v1/chat/stream)
   * Returns a ReadableStream for manual consumption.
   */
  async streamSend(data: ChatRequest): Promise<Response> {
    const token = localStorage.getItem('access_token')
    return fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ ...data, stream: true }),
    })
  },

  /**
   * List all chat sessions.
   */
  async listSessions(): Promise<ChatSession[]> {
    return apiClient.get('/api/v1/chat/sessions')
  },

  /**
   * Get a specific session with full message history.
   */
  async getSession(sessionId: string): Promise<ChatSessionDetail> {
    return apiClient.get(`/api/v1/chat/sessions/${sessionId}`)
  },

  /**
   * Delete a chat session.
   */
  async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/api/v1/chat/sessions/${sessionId}`)
  },

  /**
   * Get semantic cache statistics.
   */
  async getCacheStats(): Promise<CacheStats> {
    return apiClient.get('/api/v1/chat/cache/stats')
  },

  /**
   * Clear the semantic cache.
   */
  async clearCache(): Promise<void> {
    return apiClient.post('/api/v1/chat/cache/clear')
  },
}

/**
 * Parse an SSE stream from the chat endpoint.
 * Yields parsed SSE events as they arrive.
 */
export async function* parseSSEStream(
  response: Response
): AsyncGenerator<{ type: string; data: any }, void, undefined> {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Parse complete SSE messages
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          yield { type: data.type, data }
        } catch (e) {
          // Skip malformed JSON
        }
      }
    }
  }
}