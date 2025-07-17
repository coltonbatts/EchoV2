import React, { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import ConversationSidebar from './components/ConversationSidebar'
import { useChat } from './hooks/useChat'
import { useConfig } from './hooks/useConfig'
import { useConversations } from './hooks/useConversations'
import { conversationService } from './services/conversation/conversationService'

function App() {
  const [input, setInput] = useState('')
  
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
    updateConversationInList,
    addNewConversationToList,
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

  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || chatLoading) return

    const conversationId = await sendMessage(input, selectedModel, selectedProvider)
    setInput('')

    // If we got a new conversation ID and we're not in an active conversation, update the active conversation
    if (conversationId && !activeConversationId) {
      selectConversation(conversationId)
      
      // Auto-generate title for new conversation after a short delay
      setTimeout(async () => {
        try {
          await conversationService.generateConversationTitle(conversationId)
          refreshConversations()
        } catch (error) {
          console.warn('Failed to auto-generate conversation title:', error)
          // Still refresh to show the conversation in the sidebar
          refreshConversations()
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

  return (
    <div className="app">
      <div className="app-layout">
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
            <ChatWindow 
              messages={messages} 
              isLoading={chatLoading} 
              conversationId={activeConversationId}
            />
            
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