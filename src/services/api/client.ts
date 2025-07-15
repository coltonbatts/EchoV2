import type { 
  ChatRequest, 
  ChatResponse, 
  ConversationRequest, 
  HealthStatus,
  ProvidersResponse,
  ProviderModelsResponse,
  ApiConfig 
} from '../../types/api'

class ApiClient {
  private config: ApiConfig

  constructor(config: ApiConfig) {
    this.config = config
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })
      
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timed out')
      }
      throw error
    }
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.baseUrl}/chat`, {
      method: 'POST',
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async sendConversation(request: ConversationRequest): Promise<ChatResponse> {
    const response = await this.fetchWithTimeout(`${this.config.baseUrl}/chat/conversation`, {
      method: 'POST',
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getHealth(): Promise<HealthStatus> {
    const response = await this.fetchWithTimeout(`${this.config.baseUrl}/health`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getProviders(): Promise<ProvidersResponse> {
    const response = await this.fetchWithTimeout(`${this.config.baseUrl}/chat/providers`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getProviderModels(provider: string): Promise<ProviderModelsResponse> {
    const response = await this.fetchWithTimeout(
      `${this.config.baseUrl}/chat/providers/${provider}/models`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }
}

// Default configuration
const defaultConfig: ApiConfig = {
  baseUrl: 'http://localhost:8000',
  timeout: 60000, // 60 seconds
}

// Global API client instance
export const apiClient = new ApiClient(defaultConfig)

// Export for custom configurations
export { ApiClient }
export type { ApiConfig }