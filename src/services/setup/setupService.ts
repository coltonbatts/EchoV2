import { 
  SetupStep, 
  ProviderInfo, 
  ConnectionTestResult, 
  SetupConfig, 
  LocalStorageSetupState, 
  SETUP_STORAGE_KEY,
  SETUP_VERSION
} from '../../types/setup'
import { secureStorageService } from '../secure-storage/secureStorageService'

export class SetupService {
  private static instance: SetupService
  
  private constructor() {}
  
  static getInstance(): SetupService {
    if (!SetupService.instance) {
      SetupService.instance = new SetupService()
    }
    return SetupService.instance
  }

  // Provider definitions with signup URLs and descriptions
  getProviderInfo(): ProviderInfo[] {
    return [
      {
        id: 'openai',
        name: 'openai',
        displayName: 'OpenAI',
        description: 'GPT-4, GPT-3.5 Turbo, and other OpenAI models',
        signupUrl: 'https://platform.openai.com/signup',
        features: ['GPT-4', 'GPT-3.5', 'Function calling', 'Large context'],
        pricing: '$0.01-$0.06 per 1K tokens',
        popular: true
      },
      {
        id: 'anthropic',
        name: 'anthropic',
        displayName: 'Anthropic',
        description: 'Claude models for helpful, harmless, and honest AI',
        signupUrl: 'https://console.anthropic.com/signup',
        features: ['Claude-3', 'Long context', 'Safety focused', 'Code generation'],
        pricing: '$0.25-$15 per 1M tokens',
        popular: true
      },
      {
        id: 'google',
        name: 'google',
        displayName: 'Google',
        description: 'Gemini and other Google AI models',
        signupUrl: 'https://makersuite.google.com/app/apikey',
        features: ['Gemini Pro', 'Multimodal', 'Fast inference', 'Free tier'],
        pricing: 'Free tier available'
      }
    ]
  }

  // Test API key validity for different providers
  async testApiKey(provider: string, apiKey: string, customEndpoint?: string): Promise<ConnectionTestResult> {
    if (!apiKey.trim()) {
      return {
        success: false,
        error: 'API key is required'
      }
    }

    try {
      // For OpenAI
      if (provider === 'openai') {
        const baseUrl = customEndpoint || 'https://api.openai.com/v1'
        const response = await fetch(`${baseUrl}/models`, {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: response.statusText }))
          return {
            success: false,
            error: error.error?.message || error.error || 'Invalid API key'
          }
        }

        const data = await response.json()
        return {
          success: true,
          models: data.data?.map((model: any) => model.id) || [],
          providerInfo: {
            name: 'OpenAI',
            version: 'v1'
          }
        }
      }

      // For Anthropic
      if (provider === 'anthropic') {
        const baseUrl = customEndpoint || 'https://api.anthropic.com'
        const response = await fetch(`${baseUrl}/v1/messages`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 1,
            messages: [{ role: 'user', content: 'test' }]
          })
        })

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: response.statusText }))
          return {
            success: false,
            error: error.error?.message || error.message || 'Invalid API key'
          }
        }

        return {
          success: true,
          models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
          providerInfo: {
            name: 'Anthropic',
            version: '2023-06-01'
          }
        }
      }

      // For Google (Gemini)
      if (provider === 'google') {
        const baseUrl = customEndpoint || 'https://generativelanguage.googleapis.com'
        const response = await fetch(`${baseUrl}/v1beta/models?key=${apiKey}`)

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: response.statusText }))
          return {
            success: false,
            error: error.error?.message || error.message || 'Invalid API key'
          }
        }

        const data = await response.json()
        return {
          success: true,
          models: data.models?.map((model: any) => model.name.split('/').pop()) || ['gemini-pro'],
          providerInfo: {
            name: 'Google',
            version: 'v1beta'
          }
        }
      }

      return {
        success: false,
        error: 'Unsupported provider'
      }

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Connection failed'
      }
    }
  }

  // Save configuration using secure storage for API keys
  async saveConfiguration(config: SetupConfig): Promise<boolean> {
    try {
      // Store API key securely
      await secureStorageService.storeApiKeyUniversal(
        config.provider,
        config.apiKey,
        config.customEndpoint
      )

      // Prepare configuration data without API key for backend
      const configData = {
        ai_providers: {
          default: config.provider,
          [config.provider]: {
            // API key is now stored securely, not in config
            ...(config.customEndpoint && { base_url: config.customEndpoint }),
            ...(config.selectedModel && { default_model: config.selectedModel }),
            timeout: 60,
            max_retries: 3
          }
        }
      }

      // TODO: Call backend API to update YAML configuration
      console.log('Saving configuration (API key stored securely):', configData)
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500))
      
      return true
    } catch (error) {
      console.error('Failed to save configuration:', error)
      return false
    }
  }

  // Get setup state from localStorage
  getSetupState(): LocalStorageSetupState | null {
    try {
      const stored = localStorage.getItem(SETUP_STORAGE_KEY)
      if (!stored) return null
      
      const state: LocalStorageSetupState = JSON.parse(stored)
      
      // Validate stored state version
      if (state.version !== SETUP_VERSION) {
        this.clearSetupState()
        return null
      }
      
      return state
    } catch (error) {
      console.error('Failed to get setup state:', error)
      return null
    }
  }

  // Save setup state to localStorage
  saveSetupState(state: Partial<LocalStorageSetupState>): void {
    try {
      const currentState = this.getSetupState()
      const newState: LocalStorageSetupState = {
        isComplete: false,
        lastCompletedStep: SetupStep.WELCOME,
        selectedProvider: null,
        setupTimestamp: Date.now(),
        version: SETUP_VERSION,
        ...currentState,
        ...state
      }
      
      localStorage.setItem(SETUP_STORAGE_KEY, JSON.stringify(newState))
    } catch (error) {
      console.error('Failed to save setup state:', error)
    }
  }

  // Clear setup state (for resetting setup)
  clearSetupState(): void {
    try {
      localStorage.removeItem(SETUP_STORAGE_KEY)
    } catch (error) {
      console.error('Failed to clear setup state:', error)
    }
  }

  // Check if setup is complete
  isSetupComplete(): boolean {
    const state = this.getSetupState()
    return state?.isComplete || false
  }

  // Mark setup as complete
  markSetupComplete(provider: string): void {
    this.saveSetupState({
      isComplete: true,
      lastCompletedStep: SetupStep.COMPLETION,
      selectedProvider: provider,
      setupTimestamp: Date.now()
    })
  }

  // Get default model for provider
  getDefaultModel(provider: string): string {
    const defaults: Record<string, string> = {
      openai: 'gpt-3.5-turbo',
      anthropic: 'claude-3-sonnet-20240229',
      google: 'gemini-pro'
    }
    return defaults[provider] || ''
  }

  // Validate setup configuration
  validateSetupConfig(config: SetupConfig): { isValid: boolean; errors: string[] } {
    const errors: string[] = []
    
    if (!config.provider) {
      errors.push('Provider is required')
    }
    
    if (!config.apiKey?.trim()) {
      errors.push('API key is required')
    }
    
    if (config.customEndpoint && !this.isValidUrl(config.customEndpoint)) {
      errors.push('Invalid custom endpoint URL')
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }

  // Helper to validate URLs
  private isValidUrl(url: string): boolean {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  // Get setup progress
  getSetupProgress(currentStep: SetupStep): { current: number; total: number; percentage: number } {
    const stepOrder = [
      SetupStep.WELCOME,
      SetupStep.PROVIDER_SELECTION,
      SetupStep.API_KEY_INPUT,
      SetupStep.CONNECTION_TEST,
      SetupStep.COMPLETION
    ]
    
    const current = stepOrder.indexOf(currentStep) + 1
    const total = stepOrder.length
    const percentage = Math.round((current / total) * 100)
    
    return { current, total, percentage }
  }

  // Reset setup (for debugging or user request)
  resetSetup(): void {
    this.clearSetupState()
  }

  // Check for existing localStorage API keys and offer migration
  async checkForMigration(): Promise<{ provider: string; hasData: boolean }[]> {
    return await secureStorageService.checkForMigration()
  }

  // Migrate existing localStorage API keys to secure storage
  async migrateToSecureStorage(): Promise<{ success: string[]; failed: string[] }> {
    return await secureStorageService.migrateAllFromLocalStorage()
  }

  // Initialize secure storage and handle any necessary migrations
  async initializeSecureStorage(): Promise<void> {
    try {
      if (!secureStorageService.isSecureStorageAvailable()) {
        console.warn('Secure storage not available, using localStorage fallback')
        return
      }

      // Check for data that needs migration
      const migrationNeeded = await this.checkForMigration()
      
      if (migrationNeeded.length > 0) {
        console.log(`Found ${migrationNeeded.length} API keys to migrate from localStorage`)
        
        // Auto-migrate existing keys
        const { success, failed } = await this.migrateToSecureStorage()
        
        if (success.length > 0) {
          console.log(`Successfully migrated API keys for: ${success.join(', ')}`)
        }
        
        if (failed.length > 0) {
          console.error(`Failed to migrate API keys for: ${failed.join(', ')}`)
        }
      }
    } catch (error) {
      console.error('Failed to initialize secure storage:', error)
    }
  }

  // Get stored providers from secure storage
  async getStoredProviders(): Promise<string[]> {
    try {
      return await secureStorageService.listStoredProviders()
    } catch (error) {
      console.error('Failed to get stored providers:', error)
      return []
    }
  }

  // Retrieve API key data from secure storage
  async getApiKeyData(provider: string): Promise<{ apiKey: string; customEndpoint?: string } | null> {
    try {
      const data = await secureStorageService.getApiKeyUniversal(provider)
      if (!data) return null
      
      return {
        apiKey: data.api_key,
        customEndpoint: data.custom_endpoint
      }
    } catch (error) {
      console.error(`Failed to get API key for ${provider}:`, error)
      return null
    }
  }
}

// Export singleton instance
export const setupService = SetupService.getInstance()