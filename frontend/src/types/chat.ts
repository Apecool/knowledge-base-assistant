export interface ChatRequest {
  session_id: string
  query: string
  stream?: boolean
  top_k?: number
}

export interface ChatResponse {
  session_id: string
  answer: string
  sources: SourceItem[]
  message_count: number
}

export interface SourceItem {
  document: string
  score: number
  heading?: string
  title?: string
  knowledge_id?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  sources?: SourceItem[]
  streaming?: boolean
}

export interface ChatSession {
  session_id: string
  message_count: number
  created_at: number
  updated_at: number
}

export interface ChatSessionDetail extends ChatSession {
  messages: Array<{
    role: string
    content: string
    timestamp: number
  }>
}

export interface CacheStats {
  total_entries: number
  active_entries: number
  expired_entries: number
  threshold: number
  ttl_seconds: number
  max_size: number
}

export interface SSESourceEvent {
  type: 'sources'
  sources: SourceItem[]
}

export interface SSETokenEvent {
  type: 'token'
  content: string
}

export interface SSEDoneEvent {
  type: 'done'
  full_content: string
}

export interface SSEErrorEvent {
  type: 'error'
  content: string
}

export type SSEEvent = SSESourceEvent | SSETokenEvent | SSEDoneEvent | SSEErrorEvent