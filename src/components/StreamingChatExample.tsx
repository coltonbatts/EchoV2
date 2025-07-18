import React, { useState } from 'react'
import { useChat } from '../hooks/useChat'
import ChatWindow from './ChatWindow'

/**
 * Example component demonstrating how to use the streaming chat functionality
 * This can be used as a reference or directly integrated into your main app
 */
const StreamingChatExample: React.FC = () => {
  const [input, setInput] = useState('')
  const [selectedModel, setSelectedModel] = useState<string>()
  const [selectedProvider, setSelectedProvider] = useState<string>()
  
  const {
    messages,
    isLoading,
    isStreaming,
    streamingMessage,
    error,
    sendStreamingMessage,
    clearMessages,
    clearError
  } = useChat()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading || isStreaming) return

    try {
      // Use streaming for real-time responses
      await sendStreamingMessage(input.trim(), selectedModel, selectedProvider)
      setInput('')
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="streaming-chat-example">
      <div className="chat-header">
        <h2>EchoV2 Streaming Chat</h2>
        <div className="chat-controls">
          <div className="model-selectors">
            <select
              value={selectedProvider || ''}
              onChange={(e) => setSelectedProvider(e.target.value || undefined)}
              disabled={isLoading || isStreaming}
            >
              <option value="">Default Provider</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="ollama">Ollama</option>
            </select>
            
            <select
              value={selectedModel || ''}
              onChange={(e) => setSelectedModel(e.target.value || undefined)}
              disabled={isLoading || isStreaming}
            >
              <option value="">Default Model</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>Error: {error}</span>
          <button onClick={clearError} className="error-close-button">×</button>
        </div>
      )}

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        isStreaming={isStreaming}
        streamingMessage={streamingMessage}
      />

      <form onSubmit={handleSubmit} className="input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            isStreaming 
              ? "Streaming in progress..." 
              : isLoading 
                ? "Processing..." 
                : "Type your message here..."
          }
          disabled={isLoading || isStreaming}
          rows={3}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading || isStreaming}
        >
          {isStreaming ? 'Streaming...' : isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>

      <div className="chat-actions">
        <button
          onClick={clearMessages}
          disabled={isLoading || isStreaming}
          className="secondary-button"
        >
          Clear Chat
        </button>
        
        <div className="status-indicators">
          {isStreaming && (
            <div className="status-indicator streaming">
              <span className="status-dot"></span>
              Streaming response...
            </div>
          )}
          {isLoading && !isStreaming && (
            <div className="status-indicator loading">
              <span className="status-dot"></span>
              Loading...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StreamingChatExample