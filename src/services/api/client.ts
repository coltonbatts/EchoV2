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
import { createErrorFromResponse, TimeoutError, isRetryableError, getRetryDelay } from '../../types/errors'

/**
 * HTTP client for communicating with the EchoV2 backend API.
 * Provides request deduplication, retry logic, caching, and error handling.
 */
class ApiClient {
  private config: ApiConfig
  private pendingRequests: Map<string, Promise<Response>> = new Map()
  private requestCache: Map<string, { response: any; timestamp: number }> = new Map()
  private readonly CACHE_TTL = 30000 // 30 seconds

  constructor(config: ApiConfig) {
    this.config = config
  }

  private createRequestKey(url: string, options: RequestInit): string {
    const method = options.method || 'GET'
    const body = options.body ? JSON.stringify(options.body) : ''
    return `${method}:${url}:${body}`
  }

  private getCachedResponse<T>(key: string): T | null {
    const cached = this.requestCache.get(key)
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.response
    }
    if (cached) {
      this.requestCache.delete(key)
    }
    return null
  }

  private setCachedResponse<T>(key: string, response: T): void {
    this.requestCache.set(key, {
      response,
      timestamp: Date.now()
    })
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
        throw new TimeoutError('Request timed out', this.config.timeout)
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

        // Only retry if the error is retryable
        if (!isRetryableError(lastError)) {
          throw lastError
        }
        
        // Wait before retrying using smart delay calculation
        const delay = getRetryDelay(lastError, attempt)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    throw lastError
  }

  private async fetchWithDeduplication(url: string, options: RequestInit = {}): Promise<Response> {
    const requestKey = this.createRequestKey(url, options)
    
    // Check if we have a pending request for the same key
    const pendingRequest = this.pendingRequests.get(requestKey)
    if (pendingRequest) {
      return pendingRequest
    }

    // Check cache for GET requests
    if (!options.method || options.method === 'GET') {
      const cached = this.getCachedResponse<Response>(requestKey)
      if (cached) {
        return cached
      }
    }

    // Create and store the request promise
    const requestPromise = this.fetchWithRetry(url, options)
    this.pendingRequests.set(requestKey, requestPromise)

    try {
      const response = await requestPromise
      
      // Cache successful GET responses
      if ((!options.method || options.method === 'GET') && response.ok) {
        this.setCachedResponse(requestKey, response.clone())
      }

      return response
    } finally {
      // Always clean up the pending request
      this.pendingRequests.delete(requestKey)
    }
  }

  /**
   * Sends a chat message to the backend API.
   * 
   * @param request - The chat request containing prompt, model, and provider info
   * @returns Promise resolving to the chat response
   * @throws {AuthError} When authentication fails
   * @throws {NetworkError} When network issues occur
   * @throws {RateLimitError} When rate limits are exceeded
   * @throws {ValidationError} When request validation fails
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.fetchWithDeduplication(`${this.config.baseUrl}/chat`, {
      method: 'POST',
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async sendConversation(request: ConversationRequest): Promise<ChatResponse> {
    const response = await this.fetchWithDeduplication(`${this.config.baseUrl}/chat/conversation`, {
      method: 'POST',
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async getHealth(): Promise<HealthStatus> {
    const response = await this.fetchWithDeduplication(`${this.config.baseUrl}/health`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async getProviders(): Promise<ProvidersResponse> {
    const response = await this.fetchWithDeduplication(`${this.config.baseUrl}/chat/providers`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async getProviderModels(provider: string): Promise<ProviderModelsResponse> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/chat/providers/${provider}/models`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  // Conversation Management Methods

  async getConversations(limit: number = 50, offset: number = 0): Promise<ConversationSummary[]> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/conversations?limit=${limit}&offset=${offset}`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async getConversation(conversationId: number): Promise<ConversationDetail> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/conversations/${conversationId}`
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async deleteConversation(conversationId: number): Promise<DeleteConversationResponse> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/conversations/${conversationId}`,
      { method: 'DELETE' }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async updateConversationTitle(
    conversationId: number, 
    request: UpdateTitleRequest
  ): Promise<UpdateTitleResponse> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/conversations/${conversationId}/title`,
      {
        method: 'PUT',
        body: JSON.stringify(request)
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
    }

    return response.json()
  }

  async generateConversationTitle(conversationId: number): Promise<GenerateTitleResponse> {
    const response = await this.fetchWithDeduplication(
      `${this.config.baseUrl}/conversations/${conversationId}/generate-title`,
      { method: 'POST' }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      throw createErrorFromResponse(response, errorData.detail)
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