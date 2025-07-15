export interface ChatRequest {
  prompt: string
  model?: string
  provider?: string
}

export interface ConversationRequest {
  messages: ConversationMessage[]
  model?: string
  provider?: string
}

export interface ChatResponse {
  response: string
  model: string
  provider?: string
  metadata?: Record<string, any>
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