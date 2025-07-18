import { useState, useCallback, useEffect, useRef } from 'react'
import { chatService } from '../services/chat/chatService'
import { conversationService } from '../services/conversation/conversationService'
import { apiClient } from '../services/api/client'
import type { Message, ChatState, StreamingState } from '../types/message'
import type { StreamingChatRequest } from '../types/api'
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
    error: null,
    isStreaming: false,
    streamingMessage: undefined
  })
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestQueueRef = useRef<Set<string>>(new Set())
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const sendMessage = useCallback(async (
    prompt: string, 
    model?: string, 
    provider?: string
  ): Promise<number | undefined> => {
    if (state.isLoading) return

    let requestId: string | undefined

    try {
      const validatedPrompt = validateMessage(prompt, { maxLength: 10000 })
      
      requestId = `${conversationId}-${validatedPrompt}-${model}-${provider}`
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
      if (requestId) requestQueueRef.current.delete(requestId)
      abortControllerRef.current = null
    }
  }, [state.isLoading, conversationId])

  const sendStreamingMessage = useCallback(async (
    prompt: string,
    model?: string,
    provider?: string,
    useStreaming: boolean = true
  ): Promise<number | undefined> => {
    if (state.isLoading || state.isStreaming) return

    let requestId: string | undefined

    try {
      const validatedPrompt = validateMessage(prompt, { maxLength: 10000 })
      
      requestId = `${conversationId}-${validatedPrompt}-${model}-${provider}-streaming`
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
      
      // Clear any existing streaming timeout
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current)
        streamingTimeoutRef.current = null
      }
      
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController()

      // Add user message and set streaming state
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isStreaming: true,
        isLoading: false,
        error: null,
        streamingMessage: {
          id: (Date.now() + 1).toString(),
          text: '',
          sender: 'assistant',
          timestamp: new Date()
        }
      }))

      // Create streaming request
      const streamRequest: StreamingChatRequest = {
        prompt: validatedPrompt,
        model,
        provider,
        conversation_id: conversationId || undefined,
        stream: true
      }

      let fullResponse = ''
      let finalConversationId: number | undefined

      try {
        // Stream the response
        for await (const chunk of apiClient.sendStreamingMessage(streamRequest, abortControllerRef.current)) {
          if (chunk.type === 'content' && chunk.chunk) {
            fullResponse += chunk.chunk
            
            // Update streaming message with accumulated content
            setState(prev => ({
              ...prev,
              streamingMessage: prev.streamingMessage ? {
                ...prev.streamingMessage,
                text: fullResponse
              } : undefined
            }))
            
            // Reset streaming timeout (keep connection alive)
            if (streamingTimeoutRef.current) {
              clearTimeout(streamingTimeoutRef.current)
            }
            streamingTimeoutRef.current = setTimeout(() => {
              console.warn('Streaming timeout - no chunks received recently')
            }, 10000) // 10 second timeout between chunks
          }
        }

        // Finalize the message
        const finalMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: fullResponse,
          sender: 'assistant',
          timestamp: new Date()
        }

        setState(prev => ({
          ...prev,
          messages: [...prev.messages, finalMessage],
          isStreaming: false,
          streamingMessage: undefined
        }))

        return finalConversationId

      } catch (streamError) {
        console.warn('Streaming failed, falling back to regular request:', streamError)
        
        // Fallback to non-streaming request
        setState(prev => ({
          ...prev,
          isStreaming: false,
          streamingMessage: undefined,
          isLoading: true
        }))

        const result = await chatService.sendMessage(validatedPrompt, model, provider, conversationId || undefined)
        
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, result.message],
          isLoading: false
        }))

        return result.conversationId
      }

    } catch (error) {
      // Don't show error if request was aborted
      if (error instanceof Error && error.name === 'AbortError') {
        setState(prev => ({ 
          ...prev, 
          isLoading: false, 
          isStreaming: false,
          streamingMessage: undefined
        }))
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
        isStreaming: false,
        streamingMessage: undefined,
        error: error instanceof Error ? error.message : 'Unknown error'
      }))

      return undefined
    } finally {
      if (requestId) requestQueueRef.current.delete(requestId)
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current)
        streamingTimeoutRef.current = null
      }
      abortControllerRef.current = null
    }
  }, [state.isLoading, state.isStreaming, conversationId])

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
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current)
      }
      requestQueueRef.current.clear()
    }
  }, [])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    isStreaming: state.isStreaming,
    streamingMessage: state.streamingMessage,
    error: state.error,
    sendMessage,
    sendStreamingMessage,
    clearMessages,
    clearError,
    loadConversationMessages
  }
}