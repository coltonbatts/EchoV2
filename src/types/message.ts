export interface Message {
  id: string
  text: string
  sender: 'user' | 'assistant'
  timestamp: Date
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
  isStreaming?: boolean
  streamingMessage?: Message
}

export interface StreamingState {
  isStreaming: boolean
  currentMessage: string
  conversationId?: number
  error?: string
}