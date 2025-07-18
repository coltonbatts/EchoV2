import React, { useState, useCallback } from 'react'
import type { ConversationSummary } from '../types/api'
import { conversationService } from '../services/conversation/conversationService'

interface ConversationListItemProps {
  conversation: ConversationSummary
  isActive: boolean
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  onRename: (id: number, title: string) => void
}

const ConversationListItem: React.FC<ConversationListItemProps> = React.memo(({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conversation.title || '')
  const [showActions, setShowActions] = useState(false)

  const displayTitle = conversationService.getDisplayTitle(conversation)
  const formattedTime = conversationService.formatTimestamp(conversation.updated_at)

  const handleTitleEdit = useCallback(() => {
    setIsEditing(true)
    setEditTitle(conversation.title || displayTitle)
  }, [conversation.title, displayTitle])

  const handleTitleSave = useCallback(async () => {
    if (editTitle.trim() && editTitle !== conversation.title) {
      try {
        await onRename(conversation.id, editTitle.trim())
      } catch (error) {
        console.error('Failed to rename conversation:', error)
      }
    }
    setIsEditing(false)
  }, [editTitle, conversation.title, conversation.id, onRename])

  const handleTitleCancel = useCallback(() => {
    setIsEditing(false)
    setEditTitle(conversation.title || '')
  }, [conversation.title])

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleTitleSave()
    } else if (e.key === 'Escape') {
      handleTitleCancel()
    }
  }, [handleTitleSave, handleTitleCancel])

  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onDelete(conversation.id)
    }
  }, [conversation.id, onDelete])

  const handleSelect = useCallback(() => {
    if (!isEditing) {
      onSelect(conversation.id)
    }
  }, [isEditing, onSelect, conversation.id])

  const handleMouseEnter = useCallback(() => setShowActions(true), [])
  const handleMouseLeave = useCallback(() => setShowActions(false), [])

  return (
    <div
      className={`conversation-item ${isActive ? 'active' : ''}`}
      onClick={handleSelect}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="conversation-content">
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={handleKeyPress}
            onBlur={handleTitleSave}
            className="conversation-title-input"
            autoFocus
          />
        ) : (
          <div className="conversation-info">
            <h3 className="conversation-title">{displayTitle}</h3>
            <div className="conversation-meta">
              <span className="conversation-time">{formattedTime}</span>
              <span className="conversation-count">{conversation.message_count} messages</span>
            </div>
          </div>
        )}
      </div>

      {showActions && !isEditing && (
        <div className="conversation-actions">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              handleTitleEdit()
            }}
            className="action-button edit-button"
            title="Rename conversation"
          >
            ✏️
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="action-button delete-button"
            title="Delete conversation"
          >
            🗑️
          </button>
        </div>
      )}
    </div>
  )
})

ConversationListItem.displayName = 'ConversationListItem'

export default ConversationListItem