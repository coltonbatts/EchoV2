import React, { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import { useChat } from './hooks/useChat'
import { useConfig } from './hooks/useConfig'

function App() {
  const [input, setInput] = useState('')
  const { messages, isLoading, sendMessage } = useChat()
  const { 
    selectedProvider, 
    selectedModel, 
    providers, 
    providerModels,
    setSelectedProvider,
    setSelectedModel 
  } = useConfig()

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    await sendMessage(input, selectedModel, selectedProvider)
    setInput('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>EchoV2 - Local AI Chat</h1>
        <div className="config-section">
          {providers && (
            <div className="provider-selector">
              <label>Provider:</label>
              <select 
                value={selectedProvider} 
                onChange={(e) => setSelectedProvider(e.target.value)}
                disabled={isLoading}
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
                disabled={isLoading}
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
        <ChatWindow messages={messages} isLoading={isLoading} />
        
        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            rows={3}
          />
          <button 
            onClick={handleSendMessage} 
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </main>
    </div>
  )
}

export default App