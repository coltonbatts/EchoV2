import { useState, useCallback, useEffect } from 'react'
import { chatService } from '../services/chat/chatService'
import { conversationService } from '../services/conversation/conversationService'
import type { Message, ChatState } from '../types/message'

export const useChat = (conversationId?: number | null) => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null
  })

  const sendMessage = useCallback(async (
    prompt: string, 
    model?: string, 
    provider?: string
  ): Promise<number | undefined> => {
    if (!prompt.trim() || state.isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: prompt,
      sender: 'user',
      timestamp: new Date()
    }

    // Add user message and set loading state
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null
    }))

    try {
      const result = await chatService.sendMessage(prompt, model, provider, conversationId || undefined)
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, result.message],
        isLoading: false
      }))

      return result.conversationId
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Error: ${error instanceof Error ? error.message : 'Could not connect to backend'}`,
        sender: 'assistant',
        timestamp: new Date()
      }

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }))

      return undefined
    }
  }, [state.isLoading, conversationId])

  const clearMessages = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: [],
      error: null
    }))
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null
    }))
  }, [])

  const loadConversationMessages = useCallback(async (convId: number) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const conversation = await conversationService.getConversation(convId)
      
      const messages: Message[] = conversation.messages.map(msg => ({
        id: msg.id.toString(),
        text: msg.content,
        sender: msg.role as 'user' | 'assistant',
        timestamp: new Date(msg.timestamp)
      }))

      setState(prev => ({
        ...prev,
        messages,
        isLoading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load conversation'
      }))
    }
  }, [])

  // Load conversation messages when conversationId changes
  useEffect(() => {
    if (conversationId) {
      loadConversationMessages(conversationId)
    } else {
      // Clear messages for new conversation
      setState(prev => ({
        ...prev,
        messages: [],
        error: null
      }))
    }
  }, [conversationId, loadConversationMessages])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage,
    clearMessages,
    clearError,
    loadConversationMessages
  }
}