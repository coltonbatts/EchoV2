import React, { useEffect, useRef } from 'react'
import type { Message } from '../types/message'
import { sanitizeForDisplay } from '../utils/sanitization'

interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
  isStreaming?: boolean
  streamingMessage?: Message
  conversationId?: number | null
}

const ChatWindow: React.FC<ChatWindowProps> = React.memo(({ 
  messages, 
  isStreaming = false, 
  streamingMessage, 
  conversationId 
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  return (
    <div className="chat-window">
      {messages.length === 0 && (
        <div className="empty-state">
          {conversationId ? (
            <p>Continue this conversation...</p>
          ) : (
            <p>Welcome to EchoV2! Start a conversation with your local AI.</p>
          )}
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
        >
          <div className="message-content">
            <div 
              className="message-text"
              dangerouslySetInnerHTML={{ __html: sanitizeForDisplay(message.text) }}
            />
            <span className="message-time">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
      
      {/* Streaming message */}
      {isStreaming && streamingMessage && (
        <div
          key={`streaming-${streamingMessage.id}`}
          className="message assistant-message streaming-message"
        >
          <div className="message-content">
            <div 
              className="message-text streaming-text"
              dangerouslySetInnerHTML={{ __html: sanitizeForDisplay(streamingMessage.text) }}
            />
            <div className="streaming-indicator">
              <span className="cursor">|</span>
            </div>
            <span className="message-time">
              {streamingMessage.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}
      
      
      <div ref={messagesEndRef} />
    </div>
  )
})

ChatWindow.displayName = 'ChatWindow'

export default ChatWindow