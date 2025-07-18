# EchoV2 Streaming Implementation

This document provides a complete guide to the streaming functionality implemented in EchoV2, allowing real-time AI responses that build character by character.

## Overview

The streaming implementation consists of:

- **Backend**: FastAPI endpoints with Server-Sent Events (SSE) support
- **Frontend**: React components with real-time UI updates
- **API Client**: Streaming-enabled HTTP client with ReadableStream
- **Error Handling**: Robust fallback mechanisms and timeout management
- **Performance**: Optimized memory management and request deduplication

## Backend Implementation

### 1. Streaming Endpoint

**File**: `backend/api/routes/chat.py`

```python
@router.post("/")
async def chat_completion(request: ChatRequestModel):
    """Send a message to AI (streaming or non-streaming)."""
    if request.stream:
        # Return Server-Sent Events stream
        generator = chat_service.send_message_stream(...)
        return StreamingResponse(
            create_sse_stream(generator),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Return complete response
        return ChatResponseModel(...)
```

### 2. Chat Service Streaming Method

**File**: `backend/services/chat_service.py`

```python
async def send_message_stream(self, prompt: str, ...) -> AsyncGenerator[str, None]:
    """Stream AI response chunks."""
    # Validate and sanitize prompt
    # Save user message to database
    # Stream response from model manager
    async for chunk in self.model_manager.chat_completion_stream(...):
        yield chunk
    # Save complete response to database
```

## Frontend Implementation

### 1. TypeScript Types

**File**: `src/types/api.ts`

```typescript
// Streaming request/response types
export interface StreamChunk {
  chunk?: string
  type: 'content' | 'done' | 'error'
  message?: string
}

export interface StreamingChatRequest extends ChatRequest {
  stream: true
}
```

**File**: `src/types/message.ts`

```typescript
// Enhanced chat state with streaming
export interface ChatState {
  messages: Message[]
  isLoading: boolean
  isStreaming?: boolean
  streamingMessage?: Message
  error: string | null
}
```

### 2. API Client Streaming Method

**File**: `src/services/api/client.ts`

```typescript
async* sendStreamingMessage(
  request: StreamingChatRequest,
  abortController?: AbortController
): AsyncGenerator<StreamChunk, StreamingResponse, unknown> {
  // Set up fetch with ReadableStream
  // Parse Server-Sent Events
  // Yield chunks as they arrive
  // Handle errors and cleanup
}
```

### 3. Enhanced useChat Hook

**File**: `src/hooks/useChat.ts`

```typescript
export const useChat = (conversationId?: number | null) => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    isStreaming: false,
    streamingMessage: undefined,
    error: null
  })

  const sendStreamingMessage = useCallback(async (prompt: string, ...) => {
    // Set streaming state
    // Create streaming request
    // Process chunks in real-time
    // Handle fallback to non-streaming
    // Manage cleanup and memory
  }, [])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    isStreaming: state.isStreaming,
    streamingMessage: state.streamingMessage,
    sendMessage,           // Regular non-streaming
    sendStreamingMessage,  // New streaming method
    // ... other methods
  }
}
```

### 4. Updated ChatWindow Component

**File**: `src/components/ChatWindow.tsx`

```typescript
interface ChatWindowProps {
  messages: Message[]
  isLoading: boolean
  isStreaming?: boolean
  streamingMessage?: Message
  conversationId?: number | null
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  isStreaming = false,
  streamingMessage,
  conversationId
}) => {
  // Render regular messages
  // Render streaming message with typing indicator
  // Auto-scroll on updates
}
```

## Usage Examples

### Basic Streaming Usage

```typescript
import { useChat } from '../hooks/useChat'

const MyComponent = () => {
  const { 
    messages, 
    isStreaming, 
    streamingMessage, 
    sendStreamingMessage 
  } = useChat()

  const handleSend = async (prompt: string) => {
    await sendStreamingMessage(prompt, 'gpt-4', 'openai')
  }

  return (
    <ChatWindow
      messages={messages}
      isStreaming={isStreaming}
      streamingMessage={streamingMessage}
    />
  )
}
```

### Complete Example Component

**File**: `src/components/StreamingChatExample.tsx`

A complete implementation showing:
- Streaming toggle control
- Provider/model selection
- Real-time status indicators
- Error handling with fallback
- Memory cleanup

## Features

### ✅ Real-time Streaming
- Character-by-character response building
- Immediate feedback to users
- Smooth typing animation with cursor

### ✅ Robust Error Handling
- Automatic fallback to non-streaming on failure
- Network timeout management
- Connection drop recovery

### ✅ Performance Optimized
- Request deduplication
- Memory leak prevention
- Efficient stream processing
- Proper cleanup on component unmount

### ✅ Production Ready
- TypeScript type safety
- Comprehensive error boundaries
- Secure prompt sanitization
- Database persistence

### ✅ User Experience
- Visual streaming indicators
- Loading states
- Progress animations
- Responsive design

## Configuration

### Backend Requirements

1. **Model Manager Streaming Support**: Your model manager must implement `chat_completion_stream()` method
2. **Database**: Messages are saved to database for conversation persistence
3. **Security**: Prompt sanitization and validation included

### Frontend Configuration

```typescript
// Enable streaming by default
const defaultConfig = {
  enableStreaming: true,
  streamingTimeout: 60000,    // 60 seconds
  chunkTimeout: 10000,        // 10 seconds between chunks
  fallbackOnError: true
}
```

## API Reference

### Backend Endpoints

- `POST /chat` - Chat completion (streaming when `stream: true`)
- `POST /chat/conversation` - Multi-turn conversation

### Request Format

```json
{
  "prompt": "Hello, how are you?",
  "model": "gpt-4",
  "provider": "openai",
  "conversation_id": 123,
  "stream": true
}
```

### SSE Response Format

```
data: {"chunk": "Hello", "type": "content"}
data: {"chunk": " there", "type": "content"}
data: {"type": "done"}
```

### Frontend Hooks

```typescript
const {
  messages,              // Message[]
  isLoading,            // boolean
  isStreaming,          // boolean
  streamingMessage,     // Message | undefined
  error,                // string | null
  sendMessage,          // (prompt, model?, provider?) => Promise<number>
  sendStreamingMessage, // (prompt, model?, provider?) => Promise<number>
  clearMessages,        // () => void
  clearError           // () => void
} = useChat(conversationId?)
```

## Error Handling

The implementation includes comprehensive error handling:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Streaming Failures**: Graceful fallback to non-streaming
3. **Timeout Management**: Configurable timeouts for requests and chunks
4. **Memory Management**: Proper cleanup of streams and timers
5. **User Feedback**: Clear error messages and recovery options

## Performance Considerations

- **Debounced Updates**: UI updates are optimized to prevent excessive re-renders
- **Memory Efficient**: Streaming chunks are processed incrementally
- **Request Deduplication**: Prevents duplicate requests
- **Proper Cleanup**: All resources are cleaned up on component unmount

## Browser Compatibility

- **Chrome**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support

Requires browsers with ReadableStream and Server-Sent Events support (all modern browsers).

## Troubleshooting

### Common Issues

1. **Streaming not working**: Check backend model manager implementation
2. **Connection timeouts**: Adjust timeout configurations
3. **Memory leaks**: Ensure proper component cleanup
4. **Fallback not triggered**: Check error handling logic

### Debug Mode

Enable debug logging:

```typescript
// Add to your component
useEffect(() => {
  console.log('Streaming state:', { isStreaming, streamingMessage })
}, [isStreaming, streamingMessage])
```

## Security

- **Prompt Injection Protection**: Server-side sanitization
- **XSS Prevention**: Content sanitization in UI
- **Resource Limits**: Request timeouts and size limits
- **Input Validation**: Client and server-side validation

This implementation provides a robust, production-ready streaming solution for EchoV2 that enhances user experience while maintaining security and performance standards.