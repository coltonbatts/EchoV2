import { useState, useEffect, useCallback } from 'react'
import { chatService } from '../services/chat/chatService'
import type { HealthStatus, ProvidersResponse } from '../types/api'

interface ConfigState {
  health: HealthStatus | null
  providers: ProvidersResponse | null
  selectedProvider: string
  selectedModel: string
  providerModels: Record<string, string[]>
  isLoading: boolean
  error: string | null
}

export const useConfig = () => {
  const [state, setState] = useState<ConfigState>({
    health: null,
    providers: null,
    selectedProvider: '',
    selectedModel: '',
    providerModels: {},
    isLoading: false,
    error: null
  })

  const checkHealth = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const health = await chatService.checkHealth()
      setState(prev => ({ ...prev, health, isLoading: false }))
      return health
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Health check failed'
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }))
      throw error
    }
  }, [])

  const loadProviders = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const providers = await chatService.getProviders()
      setState(prev => ({ 
        ...prev, 
        providers, 
        selectedProvider: prev.selectedProvider || providers.default,
        isLoading: false 
      }))
      return providers
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load providers'
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }))
      throw error
    }
  }, [])

  const loadProviderModels = useCallback(async (provider: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const response = await chatService.getProviderModels(provider)
      setState(prev => ({
        ...prev,
        providerModels: {
          ...prev.providerModels,
          [provider]: response.models
        },
        selectedModel: prev.selectedModel || response.models[0] || '',
        isLoading: false
      }))
      return response
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load models'
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }))
      throw error
    }
  }, [])

  const setSelectedProvider = useCallback((provider: string) => {
    setState(prev => ({ ...prev, selectedProvider: provider }))
    
    // Load models for the new provider if not already loaded
    if (!state.providerModels[provider]) {
      loadProviderModels(provider)
    }
  }, [state.providerModels, loadProviderModels])

  const setSelectedModel = useCallback((model: string) => {
    setState(prev => ({ ...prev, selectedModel: model }))
  }, [])

  // Initialize providers on mount
  useEffect(() => {
    loadProviders()
  }, [loadProviders])

  // Load models when provider changes
  useEffect(() => {
    if (state.selectedProvider && !state.providerModels[state.selectedProvider]) {
      loadProviderModels(state.selectedProvider)
    }
  }, [state.selectedProvider, state.providerModels, loadProviderModels])

  return {
    health: state.health,
    providers: state.providers,
    selectedProvider: state.selectedProvider,
    selectedModel: state.selectedModel,
    providerModels: state.providerModels,
    isLoading: state.isLoading,
    error: state.error,
    checkHealth,
    loadProviders,
    loadProviderModels,
    setSelectedProvider,
    setSelectedModel
  }
}