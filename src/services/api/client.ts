import type { 
  ChatRequest, 
  ChatResponse, 
  ConversationRequest, 
  HealthStatus,
  ProvidersResponse,
  ProviderModelsResponse,
  ApiConfig,
  ConversationSummary,
  ConversationDetail,
  UpdateTitleRequest,
  DeleteConversationResponse,
  UpdateTitleResponse,
  GenerateTitleResponse
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

  private async fetchWithRetry(url: string, options: RequestInit = {}, maxRetries: number = 3): Promise<Response> {
    let lastError: Error = new Error('Unknown error')
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.fetchWithTimeout(url, options)
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error')
        
        // If this is the last attempt, throw the error
        if (attempt === maxRetries) {
          throw lastError
        }
        
        // Wait before retrying (exponential backoff)
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    throw lastError
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.fetchWithRetry(`${this.config.baseUrl}/chat`, {
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
    const response = await this.fetchWithRetry(`${this.config.baseUrl}/chat/conversation`, {
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
    const response = await this.fetchWithRetry(`${this.config.baseUrl}/health`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getProviders(): Promise<ProvidersResponse> {
    const response = await this.fetchWithRetry(`${this.config.baseUrl}/chat/providers`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getProviderModels(provider: string): Promise<ProviderModelsResponse> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/chat/providers/${provider}/models`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Conversation Management Methods

  async getConversations(limit: number = 50, offset: number = 0): Promise<ConversationSummary[]> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/conversations?limit=${limit}&offset=${offset}`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getConversation(conversationId: number): Promise<ConversationDetail> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/conversations/${conversationId}`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async deleteConversation(conversationId: number): Promise<DeleteConversationResponse> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/conversations/${conversationId}`,
      { method: 'DELETE' }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async updateConversationTitle(
    conversationId: number, 
    request: UpdateTitleRequest
  ): Promise<UpdateTitleResponse> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/conversations/${conversationId}/title`,
      {
        method: 'PUT',
        body: JSON.stringify(request)
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async generateConversationTitle(conversationId: number): Promise<GenerateTitleResponse> {
    const response = await this.fetchWithRetry(
      `${this.config.baseUrl}/conversations/${conversationId}/generate-title`,
      { method: 'POST' }
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