import { useState, useCallback, useEffect } from 'react'
import { conversationService } from '../services/conversation/conversationService'
import type { ConversationSummary } from '../types/api'

interface ConversationsState {
  conversations: ConversationSummary[]
  isLoading: boolean
  error: string | null
  activeConversationId: number | null
}

export const useConversations = () => {
  const [state, setState] = useState<ConversationsState>({
    conversations: [],
    isLoading: false,
    error: null,
    activeConversationId: null
  })

  const loadConversations = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const conversations = await conversationService.getConversations()
      setState(prev => ({
        ...prev,
        conversations,
        isLoading: false
      }))
      return conversations
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load conversations'
      }))
      return []
    }
  }, [])

  const selectConversation = useCallback((conversationId: number | null) => {
    setState(prev => ({
      ...prev,
      activeConversationId: conversationId
    }))
    
    // Persist active conversation to localStorage
    if (conversationId !== null) {
      localStorage.setItem('echov2_active_conversation', conversationId.toString())
    } else {
      localStorage.removeItem('echov2_active_conversation')
    }
  }, [])

  const deleteConversation = useCallback(async (conversationId: number) => {
    try {
      await conversationService.deleteConversation(conversationId)
      
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.filter(conv => conv.id !== conversationId),
        activeConversationId: prev.activeConversationId === conversationId ? null : prev.activeConversationId
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to delete conversation'
      }))
      throw error
    }
  }, [])

  const renameConversation = useCallback(async (conversationId: number, title: string) => {
    try {
      await conversationService.updateConversationTitle(conversationId, title)
      
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.map(conv =>
          conv.id === conversationId ? { ...conv, title } : conv
        )
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to rename conversation'
      }))
      throw error
    }
  }, [])

  const newConversation = useCallback(() => {
    selectConversation(null)
  }, [selectConversation])

  const refreshConversations = useCallback(() => {
    loadConversations()
  }, [loadConversations])

  const updateConversationInList = useCallback((updatedConversation: ConversationSummary) => {
    setState(prev => ({
      ...prev,
      conversations: prev.conversations.map(conv =>
        conv.id === updatedConversation.id ? updatedConversation : conv
      )
    }))
  }, [])

  const addNewConversationToList = useCallback((newConversation: ConversationSummary) => {
    setState(prev => ({
      ...prev,
      conversations: [newConversation, ...prev.conversations]
    }))
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  // Load conversations and restore active conversation on mount
  useEffect(() => {
    const initializeConversations = async () => {
      const conversations = await loadConversations()
      
      // Restore active conversation from localStorage
      const savedConversationId = localStorage.getItem('echov2_active_conversation')
      if (savedConversationId) {
        const conversationId = parseInt(savedConversationId, 10)
        if (!isNaN(conversationId)) {
          // Verify the conversation still exists before setting it as active
          const conversationExists = conversations.some(conv => conv.id === conversationId)
          if (conversationExists) {
            setState(prev => ({
              ...prev,
              activeConversationId: conversationId
            }))
          } else {
            // Clean up invalid conversation ID from localStorage
            localStorage.removeItem('echov2_active_conversation')
          }
        }
      }
    }
    
    initializeConversations()
  }, [loadConversations])

  return {
    conversations: state.conversations,
    isLoading: state.isLoading,
    error: state.error,
    activeConversationId: state.activeConversationId,
    selectConversation,
    deleteConversation,
    renameConversation,
    newConversation,
    refreshConversations,
    updateConversationInList,
    addNewConversationToList,
    clearError
  }
}