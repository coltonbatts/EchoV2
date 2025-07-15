import React, { useEffect, useRef } from 'react'
import type { Message } from '../types/message'

interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="chat-window">
      {messages.length === 0 && (
        <div className="empty-state">
          <p>Welcome to EchoV2! Start a conversation with your local AI.</p>
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
        >
          <div className="message-content">
            <pre className="message-text">{message.text}</pre>
            <span className="message-time">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
      
      {isLoading && (
        <div className="message assistant-message">
          <div className="message-content">
            <div className="loading-indicator">
              <span>●</span>
              <span>●</span>
              <span>●</span>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  )
}

export default ChatWindow