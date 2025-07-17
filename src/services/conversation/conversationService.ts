import { apiClient } from '../api/client'
import type { 
  ConversationSummary, 
  ConversationDetail,
  UpdateTitleRequest
} from '../../types/api'

export class ConversationService {
  async getConversations(limit: number = 50, offset: number = 0): Promise<ConversationSummary[]> {
    try {
      return await apiClient.getConversations(limit, offset)
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to fetch conversations'
      )
    }
  }

  async getConversation(conversationId: number): Promise<ConversationDetail> {
    try {
      return await apiClient.getConversation(conversationId)
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to fetch conversation'
      )
    }
  }

  async deleteConversation(conversationId: number): Promise<void> {
    try {
      await apiClient.deleteConversation(conversationId)
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to delete conversation'
      )
    }
  }

  async updateConversationTitle(conversationId: number, title: string): Promise<void> {
    try {
      const request: UpdateTitleRequest = { title }
      await apiClient.updateConversationTitle(conversationId, request)
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to update conversation title'
      )
    }
  }

  async generateConversationTitle(conversationId: number): Promise<string> {
    try {
      const response = await apiClient.generateConversationTitle(conversationId)
      return response.title
    } catch (error) {
      throw new Error(
        error instanceof Error 
          ? error.message 
          : 'Failed to generate conversation title'
      )
    }
  }

  // Helper method to format timestamps
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  // Helper method to generate display title
  getDisplayTitle(conversation: ConversationSummary): string {
    if (conversation.title) {
      return conversation.title
    }
    
    if (conversation.last_message_preview) {
      const preview = conversation.last_message_preview.trim()
      return preview.length > 0 ? preview : 'New Conversation'
    }
    
    return 'New Conversation'
  }
}

// Global service instance
export const conversationService = new ConversationService()