import React, { useState, useEffect } from 'react'
import { 
  SetupState, 
  SetupStep, 
  ProviderInfo, 
  SetupConfig 
} from '../types/setup'
import { setupService } from '../services/setup/setupService'

interface SetupWizardProps {
  onComplete: (config: SetupConfig) => void
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
  const [state, setState] = useState<SetupState>({
    currentStep: SetupStep.WELCOME,
    isComplete: false,
    selectedProvider: null,
    apiKey: '',
    isTestingConnection: false,
    connectionTestResult: null,
    isAdvancedMode: false,
    customEndpoint: '',
    selectedModel: '',
    error: null
  })

  const [providers] = useState<ProviderInfo[]>(setupService.getProviderInfo())

  useEffect(() => {
    // Check if there's an existing setup state
    const existingState = setupService.getSetupState()
    if (existingState && !existingState.isComplete) {
      setState(prev => ({
        ...prev,
        currentStep: existingState.lastCompletedStep,
        selectedProvider: existingState.selectedProvider
      }))
    }
  }, [])

  const nextStep = () => {
    const steps = [
      SetupStep.WELCOME,
      SetupStep.PROVIDER_SELECTION,
      SetupStep.API_KEY_INPUT,
      SetupStep.CONNECTION_TEST,
      SetupStep.COMPLETION
    ]
    
    const currentIndex = steps.indexOf(state.currentStep)
    if (currentIndex < steps.length - 1) {
      const nextStep = steps[currentIndex + 1]
      setState(prev => ({ ...prev, currentStep: nextStep, error: null }))
      
      // Save progress
      setupService.saveSetupState({
        lastCompletedStep: nextStep,
        selectedProvider: state.selectedProvider
      })
    }
  }

  const prevStep = () => {
    const steps = [
      SetupStep.WELCOME,
      SetupStep.PROVIDER_SELECTION,
      SetupStep.API_KEY_INPUT,
      SetupStep.CONNECTION_TEST,
      SetupStep.COMPLETION
    ]
    
    const currentIndex = steps.indexOf(state.currentStep)
    if (currentIndex > 0) {
      setState(prev => ({ ...prev, currentStep: steps[currentIndex - 1], error: null }))
    }
  }

  const selectProvider = (providerId: string) => {
    setState(prev => ({ 
      ...prev, 
      selectedProvider: providerId,
      selectedModel: setupService.getDefaultModel(providerId),
      connectionTestResult: null,
      error: null
    }))
  }

  const testConnection = async () => {
    if (!state.selectedProvider || !state.apiKey.trim()) {
      setState(prev => ({ ...prev, error: 'Provider and API key are required' }))
      return
    }

    setState(prev => ({ ...prev, isTestingConnection: true, error: null }))

    try {
      const result = await setupService.testApiKey(
        state.selectedProvider,
        state.apiKey,
        state.customEndpoint || undefined
      )

      setState(prev => ({ 
        ...prev, 
        connectionTestResult: result,
        isTestingConnection: false
      }))

      if (result.success) {
        // Auto-advance to next step after successful test
        setTimeout(() => nextStep(), 1000)
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isTestingConnection: false,
        error: error instanceof Error ? error.message : 'Connection test failed'
      }))
    }
  }

  const completeSetup = async () => {
    if (!state.selectedProvider || !state.apiKey.trim()) {
      setState(prev => ({ ...prev, error: 'Provider and API key are required' }))
      return
    }

    const config: SetupConfig = {
      provider: state.selectedProvider,
      apiKey: state.apiKey,
      customEndpoint: state.customEndpoint || undefined,
      selectedModel: state.selectedModel || undefined
    }

    const validation = setupService.validateSetupConfig(config)
    if (!validation.isValid) {
      setState(prev => ({ ...prev, error: validation.errors.join(', ') }))
      return
    }

    try {
      const success = await setupService.saveConfiguration(config)
      if (success) {
        setupService.markSetupComplete(state.selectedProvider)
        setState(prev => ({ ...prev, isComplete: true }))
        onComplete(config)
      } else {
        setState(prev => ({ ...prev, error: 'Failed to save configuration' }))
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Setup failed' 
      }))
    }
  }

  const progress = setupService.getSetupProgress(state.currentStep)

  const renderWelcomeStep = () => (
    <div className="setup-step">
      <div className="setup-welcome">
        <h1>Welcome to EchoV2</h1>
        <p className="setup-tagline">Start chatting in 30 seconds</p>
        <div className="setup-features">
          <div className="feature-item">
            <span className="feature-icon">🤖</span>
            <span>Multiple AI providers</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🚀</span>
            <span>Fast local chat</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔒</span>
            <span>Your data stays private</span>
          </div>
        </div>
        <button className="setup-button primary" onClick={nextStep}>
          Get Started
        </button>
      </div>
    </div>
  )

  const renderProviderSelection = () => (
    <div className="setup-step">
      <h2>Choose Your AI Provider</h2>
      <p className="setup-description">Select the AI service you'd like to use</p>
      
      <div className="provider-grid">
        {providers.map((provider) => (
          <div
            key={provider.id}
            className={`provider-card ${state.selectedProvider === provider.id ? 'selected' : ''}`}
            onClick={() => selectProvider(provider.id)}
          >
            {provider.popular && <div className="provider-badge">Popular</div>}
            <div className="provider-header">
              <h3>{provider.displayName}</h3>
              <p className="provider-description">{provider.description}</p>
            </div>
            <div className="provider-features">
              {provider.features.map((feature, index) => (
                <span key={index} className="feature-tag">{feature}</span>
              ))}
            </div>
            <div className="provider-pricing">{provider.pricing}</div>
          </div>
        ))}
      </div>

      <div className="setup-actions">
        <button className="setup-button secondary" onClick={prevStep}>
          Back
        </button>
        <button 
          className="setup-button primary" 
          onClick={nextStep}
          disabled={!state.selectedProvider}
        >
          Continue
        </button>
      </div>
    </div>
  )

  const renderApiKeyInput = () => {
    const selectedProviderInfo = providers.find(p => p.id === state.selectedProvider)
    
    return (
      <div className="setup-step">
        <h2>Enter Your API Key</h2>
        <p className="setup-description">
          Your API key will be stored securely and only used to connect to {selectedProviderInfo?.displayName}
        </p>

        <div className="api-key-section">
          <div className="input-group">
            <label htmlFor="apiKey">API Key</label>
            <input
              id="apiKey"
              type="password"
              value={state.apiKey}
              onChange={(e) => setState(prev => ({ ...prev, apiKey: e.target.value }))}
              placeholder="Enter your API key..."
              className="setup-input"
            />
          </div>

          <div className="get-key-link">
            <p>Don't have an API key? 
              <a 
                href={selectedProviderInfo?.signupUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="setup-link"
              >
                Get one here
              </a>
            </p>
          </div>

          <details className="advanced-options">
            <summary>Advanced Options</summary>
            <div className="advanced-content">
              <div className="input-group">
                <label htmlFor="customEndpoint">Custom Endpoint (optional)</label>
                <input
                  id="customEndpoint"
                  type="url"
                  value={state.customEndpoint}
                  onChange={(e) => setState(prev => ({ ...prev, customEndpoint: e.target.value }))}
                  placeholder="https://api.example.com/v1"
                  className="setup-input"
                />
              </div>
              <p className="help-text">
                Use a custom endpoint if you're using a proxy or self-hosted service
              </p>
            </div>
          </details>
        </div>

        <div className="setup-actions">
          <button className="setup-button secondary" onClick={prevStep}>
            Back
          </button>
          <button 
            className="setup-button primary" 
            onClick={testConnection}
            disabled={!state.apiKey.trim() || state.isTestingConnection}
          >
            {state.isTestingConnection ? 'Testing Connection...' : 'Test Connection'}
          </button>
        </div>
      </div>
    )
  }

  const renderConnectionTest = () => (
    <div className="setup-step">
      <h2>Connection Test</h2>
      
      {state.isTestingConnection && (
        <div className="connection-testing">
          <div className="loading-spinner"></div>
          <p>Testing connection to {providers.find(p => p.id === state.selectedProvider)?.displayName}...</p>
        </div>
      )}

      {state.connectionTestResult && (
        <div className={`connection-result ${state.connectionTestResult.success ? 'success' : 'error'}`}>
          {state.connectionTestResult.success ? (
            <div className="success-content">
              <div className="success-icon">✓</div>
              <h3>Connection Successful!</h3>
              <p>Your API key is valid and working correctly.</p>
              {state.connectionTestResult.models && (
                <div className="available-models">
                  <p>Available models: {state.connectionTestResult.models.slice(0, 3).join(', ')}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="error-content">
              <div className="error-icon">✗</div>
              <h3>Connection Failed</h3>
              <p>{state.connectionTestResult.error}</p>
              <button className="setup-button secondary" onClick={testConnection}>
                Try Again
              </button>
            </div>
          )}
        </div>
      )}

      <div className="setup-actions">
        <button className="setup-button secondary" onClick={prevStep}>
          Back
        </button>
        {state.connectionTestResult?.success && (
          <button className="setup-button primary" onClick={completeSetup}>
            Complete Setup
          </button>
        )}
      </div>
    </div>
  )

  const renderCompletion = () => (
    <div className="setup-step">
      <div className="setup-completion">
        <div className="completion-icon">🎉</div>
        <h2>Setup Complete!</h2>
        <p>EchoV2 is now configured and ready to use.</p>
        <div className="completion-summary">
          <p>Provider: <strong>{providers.find(p => p.id === state.selectedProvider)?.displayName}</strong></p>
          <p>Status: <strong>Connected</strong></p>
        </div>
        <button className="setup-button primary" onClick={() => onComplete({
          provider: state.selectedProvider!,
          apiKey: state.apiKey,
          customEndpoint: state.customEndpoint || undefined,
          selectedModel: state.selectedModel || undefined
        })}>
          Start Chatting
        </button>
      </div>
    </div>
  )

  return (
    <div className="setup-wizard">
      <div className="setup-header">
        <div className="setup-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress.percentage}%` }}
            ></div>
          </div>
          <span className="progress-text">
            Step {progress.current} of {progress.total}
          </span>
        </div>
      </div>

      <div className="setup-content">
        {state.error && (
          <div className="setup-error">
            <span className="error-icon">⚠️</span>
            <span>{state.error}</span>
            <button 
              className="error-close"
              onClick={() => setState(prev => ({ ...prev, error: null }))}
            >
              ×
            </button>
          </div>
        )}

        {state.currentStep === SetupStep.WELCOME && renderWelcomeStep()}
        {state.currentStep === SetupStep.PROVIDER_SELECTION && renderProviderSelection()}
        {state.currentStep === SetupStep.API_KEY_INPUT && renderApiKeyInput()}
        {state.currentStep === SetupStep.CONNECTION_TEST && renderConnectionTest()}
        {state.currentStep === SetupStep.COMPLETION && renderCompletion()}
      </div>
    </div>
  )
}

export default SetupWizard