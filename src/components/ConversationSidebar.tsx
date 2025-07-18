import React, { useState, useMemo } from 'react'
import ConversationListItem from './ConversationListItem'
import type { ConversationSummary } from '../types/api'
import { useDebounce } from '../utils/debounce'
import { sanitizeSearchTerm } from '../utils/validation'

interface ConversationSidebarProps {
  conversations: ConversationSummary[]
  activeConversationId?: number | null
  isLoading: boolean
  error: string | null
  onSelectConversation: (id: number | null) => void
  onNewConversation: () => void
  onDeleteConversation: (id: number) => void
  onRenameConversation: (id: number, title: string) => void
  onRefresh: () => void
  onClearError: () => void
}

const ConversationSidebar: React.FC<ConversationSidebarProps> = (props) => {
  const {
    conversations,
    activeConversationId,
    isLoading,
    error,
    onSelectConversation,
    onNewConversation,
    onDeleteConversation,
    onRenameConversation,
    onRefresh,
    onClearError
  } = props;
  const [searchTerm, setSearchTerm] = useState('')
  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  const filteredConversations = useMemo(() => {
    if (!debouncedSearchTerm.trim()) return conversations
    
    const sanitizedTerm = sanitizeSearchTerm(debouncedSearchTerm).toLowerCase()
    if (!sanitizedTerm) return conversations

    return conversations.filter(conversation => {
      const displayTitle = conversation.title || conversation.last_message_preview || 'New Conversation'
      const preview = conversation.last_message_preview || ''
      
      return displayTitle.toLowerCase().includes(sanitizedTerm) ||
             preview.toLowerCase().includes(sanitizedTerm)
    })
  }, [conversations, debouncedSearchTerm])

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value)
  }

  const clearSearch = () => {
    setSearchTerm('')
  }

  return (
    <div className="conversation-sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button
          type="button"
          onClick={onNewConversation}
          className="new-chat-button"
          title="Start new conversation"
        >
          + New Chat
        </button>
      </div>

      <div className="search-container">
        <div className="search-input-wrapper">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="search-input"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={clearSearch}
              className="search-clear-button"
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <div className="error-message">{error}</div>
          <button
            type="button"
            onClick={onClearError}
            className="error-close-button"
            title="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      <div className="conversations-container">
        {isLoading && conversations.length === 0 ? (
          <div className="loading-state">
            <div className="loading-spinner">●</div>
            <p>Loading conversations...</p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="empty-state">
            {debouncedSearchTerm ? (
              <div>
                <p>No conversations found for "{debouncedSearchTerm}"</p>
                <button
                  type="button"
                  onClick={clearSearch}
                  className="clear-search-button"
                >
                  Clear search
                </button>
              </div>
            ) : (
              <div>
                <p>No conversations yet</p>
                <p className="empty-subtitle">Start a new conversation to get began!</p>
                <button
                  type="button"
                  onClick={onNewConversation}
                  className="start-conversation-button"
                >
                  Start Conversation
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="conversations-list">
            {filteredConversations.map((conversation) => (
              <ConversationListItem
                key={conversation.id}
                conversation={conversation}
                isActive={activeConversationId === conversation.id}
                onSelect={onSelectConversation}
                onDelete={onDeleteConversation}
                onRename={onRenameConversation}
              />
            ))}
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <button
          type="button"
          onClick={onRefresh}
          className="refresh-button"
          disabled={isLoading}
          title="Refresh conversations"
        >
          {isLoading ? '⟳' : '↻'} Refresh
        </button>
        
        <div className="conversation-count">
          {filteredConversations.length} of {conversations.length} conversations
        </div>
      </div>
    </div>
  )
}

export default ConversationSidebar