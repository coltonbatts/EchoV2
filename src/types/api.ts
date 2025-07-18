export interface ChatRequest {
  prompt: string
  model?: string
  provider?: string
  conversation_id?: number
  stream?: boolean
}

export interface ConversationRequest {
  messages: ConversationMessage[]
  model?: string
  provider?: string
  conversation_id?: number
  stream?: boolean
}

export interface ChatResponse {
  response: string
  model: string
  provider?: string
  metadata?: Record<string, any>
  conversation_id?: number
}

export interface ConversationMessage {
  role: string
  content: string
}

export interface HealthStatus {
  status: string
  providers?: Record<string, ProviderStatus>
  summary?: {
    total_providers: number
    healthy_providers: number
    default_provider: string
  }
  error?: string
}

export interface ProviderStatus {
  available: boolean
  models: string[]
  error?: string
}

export interface ProvidersResponse {
  providers: string[]
  default: string
}

export interface ProviderModelsResponse {
  provider: string
  models: string[]
}

export interface ApiConfig {
  baseUrl: string
  timeout: number
}

// Conversation Management Types
export interface ConversationSummary {
  id: number
  title?: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface MessageDetail {
  id: number
  role: string
  content: string
  timestamp: string
  provider?: string
  model?: string
  message_metadata?: Record<string, any>
}

export interface ConversationDetail {
  id: number
  title?: string
  created_at: string
  updated_at: string
  messages: MessageDetail[]
}

export interface UpdateTitleRequest {
  title: string
}

export interface DeleteConversationResponse {
  message: string
}

export interface UpdateTitleResponse {
  message: string
}

export interface GenerateTitleResponse {
  title: string
  message: string
}

// Streaming-specific types
export interface StreamChunk {
  chunk?: string
  type: 'content' | 'done' | 'error'
  message?: string
}

export interface StreamingChatRequest extends ChatRequest {
  stream: true
}

export interface StreamingResponse {
  conversationId?: number
  model?: string
  provider?: string
}