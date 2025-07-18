import { renderHook, act, waitFor } from '../../test/test-utils'
import { useChat } from '../useChat'
import { mockFetch, mockFetchError, createMockMessage } from '../../test/test-utils'

// Mock the services
vi.mock('../../services/chat/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    checkHealth: vi.fn(),
  },
}))

vi.mock('../../services/conversation/conversationService', () => ({
  conversationService: {
    getConversation: vi.fn(),
  },
}))

import { chatService } from '../../services/chat/chatService'
import { conversationService } from '../../services/conversation/conversationService'

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should initialize with empty state', () => {
      const { result } = renderHook(() => useChat())

      expect(result.current.messages).toEqual([])
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBe(null)
    })
  })

  describe('sendMessage', () => {
    it('should send message successfully', async () => {
      const mockResponse = {
        message: createMockMessage({
          text: 'Hello! How can I help you?',
          sender: 'assistant',
        }),
        conversationId: 123,
      }

      vi.mocked(chatService.sendMessage).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useChat())

      await act(async () => {
        const conversationId = await result.current.sendMessage('Hello')
        expect(conversationId).toBe(123)
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.messages).toHaveLength(2) // user + assistant
      expect(result.current.messages[0].text).toBe('Hello')
      expect(result.current.messages[0].sender).toBe('user')
      expect(result.current.messages[1].text).toBe('Hello! How can I help you?')
      expect(result.current.messages[1].sender).toBe('assistant')
      expect(result.current.error).toBe(null)
    })

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'Failed to connect to backend'
      vi.mocked(chatService.sendMessage).mockRejectedValueOnce(new Error(errorMessage))

      const { result } = renderHook(() => useChat())

      await act(async () => {
        const conversationId = await result.current.sendMessage('Hello')
        expect(conversationId).toBe(undefined)
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.messages).toHaveLength(2) // user + error message
      expect(result.current.messages[0].text).toBe('Hello')
      expect(result.current.messages[0].sender).toBe('user')
      expect(result.current.messages[1].text).toContain(errorMessage)
      expect(result.current.messages[1].sender).toBe('assistant')
      expect(result.current.error).toBe(errorMessage)
    })

    it('should prevent sending while loading', async () => {
      vi.mocked(chatService.sendMessage).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('First message')
      })

      await act(async () => {
        const secondResult = await result.current.sendMessage('Second message')
        expect(secondResult).toBe(undefined)
      })

      expect(vi.mocked(chatService.sendMessage)).toHaveBeenCalledTimes(1)
    })

    it('should not send empty messages', async () => {
      const { result } = renderHook(() => useChat())

      await act(async () => {
        const conversationId = await result.current.sendMessage('')
        expect(conversationId).toBe(undefined)
      })

      expect(vi.mocked(chatService.sendMessage)).not.toHaveBeenCalled()
      expect(result.current.messages).toHaveLength(0)
    })

    it('should pass model and provider parameters', async () => {
      const mockResponse = {
        message: createMockMessage({ sender: 'assistant' }),
        conversationId: 123,
      }

      vi.mocked(chatService.sendMessage).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Hello', 'gpt-4', 'openai')
      })

      expect(vi.mocked(chatService.sendMessage)).toHaveBeenCalledWith(
        'Hello',
        'gpt-4',
        'openai',
        undefined
      )
    })
  })

  describe('conversation loading', () => {
    it('should load conversation messages when conversationId changes', async () => {
      const mockConversation = {
        id: 1,
        title: 'Test Conversation',
        messages: [
          {
            id: 1,
            role: 'user',
            content: 'Hello',
            timestamp: new Date().toISOString(),
          },
          {
            id: 2,
            role: 'assistant',
            content: 'Hi there!',
            timestamp: new Date().toISOString(),
          },
        ],
      }

      vi.mocked(conversationService.getConversation).mockResolvedValueOnce(mockConversation)

      const { result } = renderHook(() => useChat(1))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].text).toBe('Hello')
      expect(result.current.messages[0].sender).toBe('user')
      expect(result.current.messages[1].text).toBe('Hi there!')
      expect(result.current.messages[1].sender).toBe('assistant')
    })

    it('should handle conversation loading errors', async () => {
      const errorMessage = 'Failed to load conversation'
      vi.mocked(conversationService.getConversation).mockRejectedValueOnce(
        new Error(errorMessage)
      )

      const { result } = renderHook(() => useChat(1))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe(errorMessage)
      expect(result.current.messages).toHaveLength(0)
    })

    it('should clear messages when conversation changes to null', async () => {
      const { result, rerender } = renderHook(
        ({ conversationId }) => useChat(conversationId),
        { initialProps: { conversationId: 1 } }
      )

      // Set some initial messages
      act(() => {
        result.current.messages.push(createMockMessage())
      })

      // Change to null conversation
      rerender({ conversationId: null })

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(0)
        expect(result.current.error).toBe(null)
      })
    })
  })

  describe('utility functions', () => {
    it('should clear messages', () => {
      const { result } = renderHook(() => useChat())

      // Add a message first
      act(() => {
        result.current.sendMessage('Hello')
      })

      act(() => {
        result.current.clearMessages()
      })

      expect(result.current.messages).toHaveLength(0)
      expect(result.current.error).toBe(null)
    })

    it('should clear errors', () => {
      const { result } = renderHook(() => useChat())

      // Manually set an error
      act(() => {
        vi.mocked(chatService.sendMessage).mockRejectedValueOnce(new Error('Test error'))
        result.current.sendMessage('Hello')
      })

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBe(null)
    })

    it('should load conversation messages manually', async () => {
      const mockConversation = {
        id: 123,
        title: 'Manual Load Test',
        messages: [
          {
            id: 1,
            role: 'user',
            content: 'Manual message',
            timestamp: new Date().toISOString(),
          },
        ],
      }

      vi.mocked(conversationService.getConversation).mockResolvedValueOnce(mockConversation)

      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.loadConversationMessages(123)
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.messages).toHaveLength(1)
      expect(result.current.messages[0].text).toBe('Manual message')
    })
  })

  describe('edge cases', () => {
    it('should handle undefined conversation service response', async () => {
      vi.mocked(conversationService.getConversation).mockResolvedValueOnce(null as any)

      const { result } = renderHook(() => useChat(1))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })

    it('should handle malformed message data', async () => {
      const mockResponse = {
        message: null, // Invalid message
        conversationId: 123,
      }

      vi.mocked(chatService.sendMessage).mockResolvedValueOnce(mockResponse as any)

      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should handle gracefully without crashing
      // User message + null message response (handled as error)
      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].text).toBe('Hello')
      expect(result.current.messages[1]).toBe(null)
    })
  })
})