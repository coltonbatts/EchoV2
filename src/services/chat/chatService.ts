import { apiClient } from '../api/client'

export class ChatService {

  async checkHealth() {
    try {
      return await apiClient.getHealth()
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to check health'
      )
    }
  }

  async getProviders() {
    try {
      return await apiClient.getProviders()
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to get providers'
      )
    }
  }

  async getProviderModels(provider: string) {
    try {
      return await apiClient.getProviderModels(provider)
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to get provider models'
      )
    }
  }
}

// Global service instance
export const chatService = new ChatService()