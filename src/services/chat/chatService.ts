import { apiClient } from '../api/client'
import type { Message } from '../../types/message'
import type { ChatRequest, ChatResponse } from '../../types/api'

export class ChatService {
  async sendMessage(
    prompt: string, 
    model?: string, 
    provider?: string,
    conversationId?: number
  ): Promise<{ message: Message, conversationId?: number }> {
    try {
      const request: ChatRequest = {
        prompt,
        model,
        provider,
        conversation_id: conversationId
      }

      const response: ChatResponse = await apiClient.sendMessage(request)

      const message: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'assistant',
        timestamp: new Date()
      }

      return {
        message,
        conversationId: response.conversation_id
      }
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to send message'
      )
    }
  }

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