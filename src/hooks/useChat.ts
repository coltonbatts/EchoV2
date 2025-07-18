import { useState, useCallback, useEffect, useRef } from 'react'
import { chatService } from '../services/chat/chatService'
import { conversationService } from '../services/conversation/conversationService'
import type { Message, ChatState } from '../types/message'
import { validateMessage } from '../utils/validation'

/**
 * A React hook that manages chat functionality including sending messages,
 * loading conversation history, and managing chat state.
 *
 * @param conversationId - Optional conversation ID to load messages from
 * @returns Chat state and methods for interacting with the chat
 *
 * @example
 * ```tsx
 * const { messages, isLoading, sendMessage } = useChat(123)
 * 
 * // Send a message
 * const conversationId = await sendMessage("Hello", "gpt-4", "openai")
 * ```
 */
export const useChat = (conversationId?: number | null) => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null
  })
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestQueueRef = useRef<Set<string>>(new Set())

  const sendMessage = useCallback(async (
    prompt: string, 
    model?: string, 
    provider?: string
  ): Promise<number | undefined> => {
    if (state.isLoading) return

    try {
      const validatedPrompt = validateMessage(prompt, { maxLength: 10000 })
      
      // Create request ID for deduplication
      const requestId = `${conversationId}-${validatedPrompt}-${model}-${provider}`
      if (requestQueueRef.current.has(requestId)) {
        return // Prevent duplicate requests
      }
      requestQueueRef.current.add(requestId)

      const userMessage: Message = {
        id: Date.now().toString(),
        text: validatedPrompt,
        sender: 'user',
        timestamp: new Date()
      }

      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController()

      // Add user message and set loading state
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        error: null
      }))

      const result = await chatService.sendMessage(validatedPrompt, model, provider, conversationId || undefined)
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, result.message],
        isLoading: false
      }))

      return result.conversationId
    } catch (error) {
      // Don't show error if request was aborted
      if (error instanceof Error && error.name === 'AbortError') {
        setState(prev => ({ ...prev, isLoading: false }))
        return undefined
      }

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
    } finally {
      // Clean up request from queue
      requestQueueRef.current.delete(requestId)
      abortControllerRef.current = null
    }
    } catch (validationError) {
      // Handle validation errors
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: `Validation Error: ${validationError instanceof Error ? validationError.message : 'Invalid input'}`,
        sender: 'assistant',
        timestamp: new Date()
      }

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        error: validationError instanceof Error ? validationError.message : 'Validation failed'
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
    // Cancel any pending requests before loading conversation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
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

  // Cleanup effect to abort pending requests on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      requestQueueRef.current.clear()
    }
  }, [])

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