import { invoke } from '@tauri-apps/api/tauri'

export interface ApiKeyData {
  provider: string
  api_key: string
  custom_endpoint?: string
}

export class SecureStorageService {
  private static instance: SecureStorageService
  
  private constructor() {}
  
  static getInstance(): SecureStorageService {
    if (!SecureStorageService.instance) {
      SecureStorageService.instance = new SecureStorageService()
    }
    return SecureStorageService.instance
  }

  /**
   * Store an API key securely using the system keyring
   */
  async storeApiKey(
    provider: string, 
    apiKey: string, 
    customEndpoint?: string
  ): Promise<void> {
    try {
      await invoke('store_api_key', {
        provider,
        apiKey,
        customEndpoint: customEndpoint || null
      })
    } catch (error) {
      throw new Error(`Failed to store API key: ${error}`)
    }
  }

  /**
   * Retrieve an API key from secure storage
   */
  async getApiKey(provider: string): Promise<ApiKeyData | null> {
    try {
      const result = await invoke<ApiKeyData | null>('get_api_key', { provider })
      return result
    } catch (error) {
      throw new Error(`Failed to retrieve API key: ${error}`)
    }
  }

  /**
   * Delete an API key from secure storage
   */
  async deleteApiKey(provider: string): Promise<void> {
    try {
      await invoke('delete_api_key', { provider })
    } catch (error) {
      throw new Error(`Failed to delete API key: ${error}`)
    }
  }

  /**
   * List all providers that have stored API keys
   */
  async listStoredProviders(): Promise<string[]> {
    try {
      const result = await invoke<string[]>('list_stored_providers')
      return result
    } catch (error) {
      throw new Error(`Failed to list stored providers: ${error}`)
    }
  }

  /**
   * Migrate API key from localStorage to secure storage
   */
  async migrateFromLocalStorage(
    provider: string, 
    apiKey: string, 
    customEndpoint?: string
  ): Promise<void> {
    try {
      await invoke('migrate_from_localstorage', {
        provider,
        apiKey,
        customEndpoint: customEndpoint || null
      })
      
      // Remove from localStorage after successful migration
      localStorage.removeItem(`api_key_${provider}`)
      localStorage.removeItem(`custom_endpoint_${provider}`)
    } catch (error) {
      throw new Error(`Failed to migrate API key: ${error}`)
    }
  }

  /**
   * Check if we're running in Tauri (desktop app)
   */
  isSecureStorageAvailable(): boolean {
    return typeof window !== 'undefined' && '__TAURI__' in window
  }

  /**
   * Fallback to localStorage for web or when secure storage fails
   */
  async storeApiKeyFallback(
    provider: string, 
    apiKey: string, 
    customEndpoint?: string
  ): Promise<void> {
    console.warn('Using localStorage fallback for API key storage')
    localStorage.setItem(`api_key_${provider}`, apiKey)
    if (customEndpoint) {
      localStorage.setItem(`custom_endpoint_${provider}`, customEndpoint)
    }
  }

  /**
   * Fallback to localStorage for web or when secure storage fails
   */
  async getApiKeyFallback(provider: string): Promise<ApiKeyData | null> {
    const apiKey = localStorage.getItem(`api_key_${provider}`)
    if (!apiKey) return null
    
    const customEndpoint = localStorage.getItem(`custom_endpoint_${provider}`)
    
    return {
      provider,
      api_key: apiKey,
      custom_endpoint: customEndpoint || undefined
    }
  }

  /**
   * Universal store method that uses secure storage when available, falls back to localStorage
   */
  async storeApiKeyUniversal(
    provider: string, 
    apiKey: string, 
    customEndpoint?: string
  ): Promise<void> {
    if (this.isSecureStorageAvailable()) {
      try {
        await this.storeApiKey(provider, apiKey, customEndpoint)
        return
      } catch (error) {
        console.error('Secure storage failed, falling back to localStorage:', error)
      }
    }
    
    await this.storeApiKeyFallback(provider, apiKey, customEndpoint)
  }

  /**
   * Universal get method that tries secure storage first, falls back to localStorage
   */
  async getApiKeyUniversal(provider: string): Promise<ApiKeyData | null> {
    if (this.isSecureStorageAvailable()) {
      try {
        const result = await this.getApiKey(provider)
        if (result) return result
      } catch (error) {
        console.error('Secure storage retrieval failed, falling back to localStorage:', error)
      }
    }
    
    return await this.getApiKeyFallback(provider)
  }

  /**
   * Check for existing localStorage data and offer migration
   */
  async checkForMigration(): Promise<{ provider: string; hasData: boolean }[]> {
    const commonProviders = ['openai', 'anthropic', 'google', 'ollama']
    const migrationNeeded: { provider: string; hasData: boolean }[] = []
    
    for (const provider of commonProviders) {
      const apiKey = localStorage.getItem(`api_key_${provider}`)
      migrationNeeded.push({
        provider,
        hasData: !!apiKey
      })
    }
    
    return migrationNeeded.filter(item => item.hasData)
  }

  /**
   * Migrate all existing localStorage API keys to secure storage
   */
  async migrateAllFromLocalStorage(): Promise<{ success: string[]; failed: string[] }> {
    const success: string[] = []
    const failed: string[] = []
    
    const toMigrate = await this.checkForMigration()
    
    for (const { provider } of toMigrate) {
      try {
        const apiKey = localStorage.getItem(`api_key_${provider}`)
        const customEndpoint = localStorage.getItem(`custom_endpoint_${provider}`)
        
        if (apiKey) {
          await this.migrateFromLocalStorage(provider, apiKey, customEndpoint || undefined)
          success.push(provider)
        }
      } catch (error) {
        console.error(`Failed to migrate ${provider}:`, error)
        failed.push(provider)
      }
    }
    
    return { success, failed }
  }
}

// Export singleton instance
export const secureStorageService = SecureStorageService.getInstance()