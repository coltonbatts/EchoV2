export interface SetupState {
  currentStep: SetupStep
  isComplete: boolean
  selectedProvider: string | null
  apiKey: string
  isTestingConnection: boolean
  connectionTestResult: ConnectionTestResult | null
  isAdvancedMode: boolean
  customEndpoint: string
  selectedModel: string
  error: string | null
}

export enum SetupStep {
  WELCOME = 'welcome',
  PROVIDER_SELECTION = 'provider_selection',
  API_KEY_INPUT = 'api_key_input',
  CONNECTION_TEST = 'connection_test',
  ADVANCED_OPTIONS = 'advanced_options',
  COMPLETION = 'completion'
}

export interface ProviderInfo {
  id: string
  name: string
  displayName: string
  description: string
  iconUrl?: string
  signupUrl: string
  features: string[]
  pricing: string
  popular?: boolean
}

export interface ConnectionTestResult {
  success: boolean
  error?: string
  models?: string[]
  providerInfo?: {
    name: string
    version?: string
    limits?: Record<string, any>
  }
}

export interface SetupConfig {
  provider: string
  apiKey: string
  customEndpoint?: string
  selectedModel?: string
  advancedOptions?: Record<string, any>
}

export interface SetupProgress {
  currentStep: SetupStep
  totalSteps: number
  completedSteps: number
  progress: number
}

export interface SetupValidationResult {
  isValid: boolean
  errors: string[]
  warnings?: string[]
}

export interface LocalStorageSetupState {
  isComplete: boolean
  lastCompletedStep: SetupStep
  selectedProvider: string | null
  setupTimestamp: number
  version: string
}

export interface ProviderTemplate {
  id: string
  name: string
  config: {
    api_key: string
    base_url?: string
    default_model?: string
    timeout?: number
    max_retries?: number
    [key: string]: any
  }
}

export interface SetupError {
  code: string
  message: string
  details?: any
  retryable: boolean
}

export const SETUP_STORAGE_KEY = 'echov2_setup_state'
export const SETUP_VERSION = '1.0.0'