import React, { useState, useCallback, useEffect, useRef } from 'react'
import ChatWindow from './components/ChatWindow'
import ConversationSidebar from './components/ConversationSidebar'
import SetupWizard from './components/SetupWizard'
import { ErrorBoundaryWrapper } from './components/ErrorBoundary'
import { useChat } from './hooks/useChat'
import { useConfig } from './hooks/useConfig'
import { useConversations } from './hooks/useConversations'
import { conversationService } from './services/conversation/conversationService'
import { setupService } from './services/setup/setupService'
import { SetupConfig } from './types/setup'

function App() {
  const [input, setInput] = useState('')
  const [isSetupComplete, setIsSetupComplete] = useState<boolean>(false)
  const [isCheckingSetup, setIsCheckingSetup] = useState<boolean>(true)
  const titleGenerationTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Conversation management
  const {
    conversations,
    isLoading: conversationsLoading,
    error: conversationsError,
    activeConversationId,
    selectConversation,
    deleteConversation,
    renameConversation,
    newConversation,
    refreshConversations,
    clearError: clearConversationsError
  } = useConversations()

  // Chat functionality
  const { messages, isLoading: chatLoading, sendMessage } = useChat(activeConversationId)
  
  // Provider configuration
  const { 
    selectedProvider, 
    selectedModel, 
    providers, 
    providerModels,
    setSelectedProvider,
    setSelectedModel 
  } = useConfig()

  // Check setup completion status on app load
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const isComplete = setupService.isSetupComplete()
        setIsSetupComplete(isComplete)
      } catch (error) {
        console.error('Failed to check setup status:', error)
        setIsSetupComplete(false)
      } finally {
        setIsCheckingSetup(false)
      }
    }
    
    checkSetupStatus()
  }, [])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (titleGenerationTimeoutRef.current) {
        clearTimeout(titleGenerationTimeoutRef.current)
      }
    }
  }, [])

  // Handle setup completion
  const handleSetupComplete = useCallback((config: SetupConfig) => {
    setIsSetupComplete(true)
    console.log('Setup completed with config:', config)
    // The setupService already marks setup as complete
  }, [])

  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || chatLoading) return

    const conversationId = await sendMessage(input, selectedModel, selectedProvider)
    setInput('')

    // If we got a new conversation ID and we're not in an active conversation, update the active conversation
    if (conversationId && !activeConversationId) {
      selectConversation(conversationId)
      
      // Clear any existing timeout
      if (titleGenerationTimeoutRef.current) {
        clearTimeout(titleGenerationTimeoutRef.current)
      }

      // Auto-generate title for new conversation after a short delay
      titleGenerationTimeoutRef.current = setTimeout(async () => {
        try {
          await conversationService.generateConversationTitle(conversationId)
          refreshConversations()
        } catch (error) {
          console.warn('Failed to auto-generate conversation title:', error)
          // Still refresh to show the conversation in the sidebar
          refreshConversations()
        } finally {
          titleGenerationTimeoutRef.current = null
        }
      }, 1000)
    } else if (conversationId && activeConversationId) {
      // Update the conversation in the list to reflect new message
      refreshConversations()
    }
  }, [input, chatLoading, sendMessage, selectedModel, selectedProvider, activeConversationId, selectConversation, refreshConversations])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSelectConversation = useCallback((conversationId: number | null) => {
    selectConversation(conversationId)
  }, [selectConversation])

  const getActiveConversationTitle = () => {
    if (!activeConversationId) return 'New Conversation'
    
    const activeConversation = conversations.find(conv => conv.id === activeConversationId)
    if (!activeConversation) return 'New Conversation'
    
    return activeConversation.title || 'Untitled Conversation'
  }

  // Show loading state while checking setup
  if (isCheckingSetup) {
    return (
      <div className="app">
        <div className="loading-state">
          <div className="loading-spinner">⏳</div>
          <p>Loading EchoV2...</p>
        </div>
      </div>
    )
  }

  // Show setup wizard if setup is not complete
  if (!isSetupComplete) {
    return <SetupWizard onComplete={handleSetupComplete} />
  }

  // Show main app if setup is complete
  return (
    <div className="app">
      <div className="app-layout">
        <ErrorBoundaryWrapper>
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            isLoading={conversationsLoading}
            error={conversationsError}
            onSelectConversation={handleSelectConversation}
            onNewConversation={newConversation}
            onDeleteConversation={deleteConversation}
            onRenameConversation={renameConversation}
            onRefresh={refreshConversations}
            onClearError={clearConversationsError}
          />
        </ErrorBoundaryWrapper>
        
        <div className="main-content">
          <header className="app-header">
            <div className="conversation-header">
              <h1>{getActiveConversationTitle()}</h1>
              <div className="conversation-subtitle">
                EchoV2 - Local AI Chat
              </div>
            </div>
            
            <div className="config-section">
              {providers && (
                <div className="provider-selector">
                  <label>Provider:</label>
                  <select 
                    value={selectedProvider} 
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    disabled={chatLoading}
                  >
                    {providers.providers.map(provider => (
                      <option key={provider} value={provider}>{provider}</option>
                    ))}
                  </select>
                </div>
              )}
              
              {selectedProvider && providerModels[selectedProvider] && (
                <div className="model-selector">
                  <label>Model:</label>
                  <select 
                    value={selectedModel} 
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={chatLoading}
                  >
                    {providerModels[selectedProvider].map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </header>
          
          <main className="app-main">
            <ErrorBoundaryWrapper>
              <ChatWindow 
                messages={messages} 
                isLoading={chatLoading} 
                conversationId={activeConversationId}
              />
            </ErrorBoundaryWrapper>
            
            <div className="input-container">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={chatLoading}
                rows={3}
              />
              <button 
                onClick={handleSendMessage} 
                disabled={!input.trim() || chatLoading}
              >
                {chatLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

export default App