# EchoV2 - Modular AI Chat Platform

A modular, extensible desktop application built with **Tauri**, **React**, **TypeScript**, and **Python FastAPI** featuring a plugin-based architecture for AI model providers. Chat with local and cloud AI models through a unified interface.

## ✨ Features

- 📦 **Standalone Mac App** - Single-click installation with bundled Python backend
- 🚀 **Zero-Dependency Deployment** - No Python or package installation required for end users
- 🎯 **First-Time Setup Wizard** - "Start chatting in 30 seconds" with guided provider configuration
- 💬 **Conversation Management** - Full conversation workspace with sidebar, search, and persistence
- 🧩 **Advanced Plugin Architecture** - Hot-swappable AI providers with zero-restart deployment
- 🔄 **Streaming Support** - Real-time responses from all providers (OpenAI, Anthropic, Ollama)
- 🛠️ **Runtime Management** - Plugin discovery, configuration updates, and health monitoring via API
- 🎯 **Type Safety** - Full TypeScript integration across frontend with comprehensive validation
- ⚙️ **Configuration Management** - Environment-based YAML with runtime updates and validation
- 🔌 **Multi-Provider Support** - OpenAI GPT, Anthropic Claude, and local Ollama models
- 🖥️ **Desktop Native** - Cross-platform desktop app with Tauri
- 🔒 **Local-First** - Support for local AI models (Ollama) and privacy
- 💾 **SQLite Persistence** - Automatic conversation and message storage with cross-platform support
- 📡 **Developer Tools** - Plugin template generator and comprehensive API documentation

### 🆕 **Latest Security & Reliability Features**
- 🔐 **Secure API Key Storage** - System keyring integration (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- 🛡️ **Prompt Injection Protection** - Advanced sanitization with pattern filtering and HTML escaping
- 🔄 **Automatic Retry Logic** - Exponential backoff for transient failures (connection, timeout, network)
- 📊 **Structured Logging** - JSON-formatted logs with contextual information for better debugging
- ✅ **Comprehensive Testing** - Full test coverage for critical functionality (backend + frontend)
- 🔧 **Smart Error Handling** - Specific error messages for authentication, rate limits, and model availability

## 🏗️ Architecture Overview

EchoV2 uses a **modular plugin architecture** that separates concerns and enables easy extensibility:

### Backend Architecture
```
backend/
├── core/
│   ├── models/           # AbstractAIProvider interface, registry & manager
│   ├── plugins/          # AI provider implementations
│   │   ├── ollama_provider.py     # Local AI via Ollama
│   │   ├── openai_provider.py     # OpenAI GPT models
│   │   └── anthropic_provider.py  # Anthropic Claude models
│   └── database/         # SQLite persistence layer
│       ├── config.py     # Database configuration & user data paths
│       ├── session.py    # Async SQLAlchemy session management
│       └── models.py     # Database models (conversations, messages)
├── services/             # Business logic layer
│   ├── chat_service.py   # Chat logic with auto-persistence
│   ├── conversation_service.py  # Database operations
│   └── health_service.py # System health monitoring
├── api/routes/           # RESTful API endpoints
│   ├── chat.py          # Chat completion endpoints (now with persistence)
│   ├── conversations.py # Conversation management API
│   ├── health.py        # System health monitoring
│   └── plugins.py       # Plugin management API
├── utils/               # Developer tools
│   └── plugin_template.py # Plugin template generator
├── tests/               # Comprehensive test suite (NEW!)
│   ├── conftest.py      # Test fixtures and setup
│   ├── test_chat_service.py      # Unit tests for chat functionality
│   └── test_api_routes.py        # API integration tests
└── config/              # Settings and configuration management
```

### Frontend Architecture
```
src/
├── types/               # TypeScript interfaces
├── services/            # API client & business services
│   └── secure-storage/  # Secure API key storage service (NEW!)
├── hooks/               # Custom React hooks (useChat, useConfig)
│   └── __tests__/       # Frontend test suite (NEW!)
├── test/                # Test utilities and setup (NEW!)
└── components/          # React UI components
```

## 🛡️ Security & Reliability Features

EchoV2 includes enterprise-grade security and reliability features to ensure safe and robust operation:

### 🔐 **Secure API Key Storage**

**System Keyring Integration** - API keys are stored securely using the operating system's native credential management:

- **🖥️ Windows**: Windows Credential Manager
- **🍎 macOS**: Keychain Services  
- **🐧 Linux**: Secret Service (libsecret)
- **🌐 Web Fallback**: Encrypted localStorage with migration support

```typescript
// Automatic secure storage with fallback
await secureStorageService.storeApiKeyUniversal('openai', 'sk-...', 'https://api.openai.com')

// Migration from localStorage to secure storage
const migrationResult = await secureStorageService.migrateAllFromLocalStorage()
console.log(`Migrated ${migrationResult.success.length} API keys securely`)
```

### 🛡️ **Prompt Injection Protection**

**Advanced Input Sanitization** - Comprehensive protection against prompt injection attacks:

```python
# Automatic sanitization includes:
- HTML escaping to prevent XSS-like attacks
- Pattern filtering for common injection attempts
- Length limiting to prevent resource exhaustion
- Structured logging of potential threats

# Example patterns detected and filtered:
"ignore all previous instructions" → "[filtered]"
"you are now a different AI" → "[filtered]" 
"<script>alert('xss')</script>" → "&lt;script&gt;alert('xss')&lt;/script&gt;"
```

### 🔄 **Automatic Retry Logic**

**Intelligent Error Recovery** - Exponential backoff retry for transient failures:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError))
)
async def chat_completion_with_retry():
    # Automatic retry for network issues, timeouts, and connection failures
    # 3 attempts with exponential backoff: 4s, 8s, 10s
```

### 📊 **Structured Logging**

**Production-Ready Observability** - JSON-formatted logs with rich contextual information:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Chat completion successful",
  "provider": "openai",
  "model": "gpt-4",
  "conversation_id": 123,
  "response_length": 245,
  "usage": {"prompt_tokens": 15, "completion_tokens": 32},
  "request_id": "req_abc123"
}
```

### ✅ **Comprehensive Testing**

**Full Test Coverage** - Critical functionality thoroughly tested:

**Backend Testing (pytest)**:
- ✅ Unit tests for chat service core functionality
- ✅ Integration tests for API routes
- ✅ Error handling and edge case scenarios
- ✅ Provider switching and model management
- ✅ Async support with proper fixtures

**Frontend Testing (Vitest + React Testing Library)**:
- ✅ Hook testing for useChat and core functionality
- ✅ Component testing with user interaction simulation
- ✅ Error state and loading state validation
- ✅ API integration and mock testing

```bash
# Run tests
npm test                    # Frontend tests
cd backend && python -m pytest  # Backend tests

# Test coverage
npm run test:coverage       # Frontend coverage report
python -m pytest --cov     # Backend coverage report
```

### 🔧 **Smart Error Handling**

**User-Friendly Error Messages** - Specific, actionable error feedback:

- **🔑 Authentication Errors**: "Please check your API key for {provider}"
- **⏱️ Rate Limiting**: "Rate limit exceeded for {provider}. Please try again later."
- **🌐 Connection Issues**: "Connection failed to {provider}. Please check your internet connection."
- **🤖 Model Errors**: "Model '{model}' not available for {provider}."
- **🔧 Generic Fallback**: "Request failed for {provider}: {specific_error_details}"

## 📦 Standalone App (Recommended for Users)

**Want to just use EchoV2 without any setup?** Download the standalone Mac app!

### 🎯 One-Click Installation

1. **Download** the latest `EchoV2.app` from [Releases](https://github.com/coltonbatts/EchoV2/releases)
2. **Drag** to Applications folder
3. **Double-click** to run - the Python backend starts automatically!

### ✨ What's Included

The standalone app bundles everything you need:
- ✅ Tauri frontend (React + TypeScript)
- ✅ Python FastAPI backend (PyInstaller executable)
- ✅ All dependencies and configurations
- ✅ Automatic backend process management
- ✅ First-time setup wizard with guided configuration
- ✅ No Python installation required

### 🔧 Building Your Own Standalone App

Want to build the standalone app yourself? It's easy:

```bash
# Install prerequisites (Rust required)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Clone and build
git clone https://github.com/coltonbatts/EchoV2.git
cd EchoV2
npm install
npm run build:standalone
```

The app will be created at: `src-tauri/target/release/bundle/macos/EchoV2.app`

**📚 Detailed build instructions:** See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)

---

## 🚀 Development Setup

### Prerequisites

- **Node.js** (v18+)
- **Python** (v3.8+) 
- **Rust** (for Tauri)
- **Ollama** (for local AI models)

### Installation

1. **Clone and install dependencies:**
```bash
git clone https://github.com/coltonbatts/EchoV2.git
cd EchoV2
npm install
```

2. **Set up Python backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

3. **Start Ollama (for local AI):**
```bash
ollama pull mistral
ollama serve
```

### Running the Application

1. **Start the backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload
```

2. **Start the frontend:**
```bash
npm run tauri:dev
```

The application will open as a desktop app with the backend running at `http://localhost:8000`.

## 🔌 AI Provider Plugins

EchoV2's advanced plugin system supports hot-swappable AI providers with comprehensive management:

### Built-in Providers
- **🦙 Ollama** - Local AI models (Mistral, Llama3, CodeLlama, Gemma, etc.)
  - ✅ Streaming responses
  - ✅ Multiple model support
  - ✅ Zero configuration for local development

- **🤖 OpenAI** - GPT models with full feature support
  - ✅ GPT-4, GPT-3.5-turbo variants
  - ✅ Streaming responses
  - ✅ Function calling
  - ✅ Vision capabilities

- **🧠 Anthropic** - Claude models with advanced capabilities
  - ✅ Claude-3 (Opus, Sonnet, Haiku)
  - ✅ Claude-2 series
  - ✅ Streaming responses
  - ✅ Vision and multimodal support

### 🚀 Creating Custom Providers

**Method 1: Use the Plugin Template Generator (Recommended)**
```bash
cd backend
python utils/plugin_template.py \
  --name "custom-ai" \
  --display "Custom AI" \
  --url "https://api.custom-ai.com" \
  --model "custom-model-v1"
```

**Method 2: Manual Implementation**
```python
# backend/core/plugins/custom_provider.py
class CustomProvider(AbstractAIProvider):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Provider",
            capabilities=[PluginCapability.STREAMING],
            # ... other metadata
        )
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        # Your implementation here
        pass
```

**Configuration & Registration**
```yaml
# config/development.yaml
ai_providers:
  custom:
    api_key: "your-api-key"
    base_url: "https://api.custom-ai.com"
    default_model: "custom-model-v1"
```

```python
# main.py
registry.register(CustomProvider, "custom")
```

## ⚙️ Configuration

### Environment-Based Configuration

EchoV2 uses YAML configuration files for different environments:

- `config/development.yaml` - Development settings
- `config/production.yaml` - Production settings

### Key Configuration Options

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: true

ai_providers:
  default: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    default_model: "mistral"
    timeout: 60
  openai:
    api_key: ""  # Set your OpenAI API key
    default_model: "gpt-3.5-turbo"
    timeout: 60
  anthropic:
    api_key: ""  # Set your Anthropic API key
    default_model: "claude-3-sonnet-20240229"
    max_tokens: 4096

cors:
  allowed_origins: ["http://localhost:1420"]
```

## 💬 Conversation Management

EchoV2 features a **comprehensive conversation workspace** that transforms the app from a stateless chat into a persistent conversation platform, allowing users to build complex, multi-turn conversations over time.

### 🎯 **Key Features**
- **✅ Conversation Sidebar** - Browse and manage all conversations with search functionality
- **✅ Auto-Title Generation** - Intelligent titles automatically generated from first user message
- **✅ Conversation Persistence** - Active conversation remembered across app sessions
- **✅ Inline Editing** - Rename conversations directly in the sidebar
- **✅ Search & Filter** - Find conversations by title or content preview
- **✅ New Chat Functionality** - Easy access to start fresh conversations
- **✅ Cross-Session Continuity** - Pick up conversations exactly where you left off

### 🔄 **User Workflows**
1. **Start New Conversation** → Auto-generates title → Persists automatically
2. **Continue Previous Conversation** → Click from sidebar → Loads full history  
3. **Search Conversations** → Filter by title or content preview
4. **Organize Conversations** → Rename, delete, or browse by date
5. **Seamless Multi-Session** → Active conversation remembered between app launches

### 📱 **Interface Layout**
```
┌─────────────────────────────────────────────────────┐
│ EchoV2 - Active Conversation Title  [Provider][Model]│
├─────────────┬───────────────────────────────────────┤
│ Sidebar     │ Chat Messages                         │
│             │                                       │
│ 🔍 Search   │ ┌─ User: Hello                        │
│             │ └─ AI: Hi! How can I help?            │
│ Conversation│                                       │
│ 1 ⭐        │ ┌─ User: What's the weather?           │
│ Conversation│ └─ AI: I don't have access to...       │
│ 2           │                                       │
│ Conversation│                                       │
│ 3           │                                       │
│             │                                       │
│ [+ New]     │ [Input field.....................] 📤 │
└─────────────┴───────────────────────────────────────┘
```

## 💾 SQLite Persistence

EchoV2 features **automatic conversation and message storage** with SQLite, providing seamless chat history without requiring any configuration.

### 🔧 **Database Features**
- **✅ Automatic Storage** - All messages saved transparently to SQLite database
- **✅ Cross-Platform** - User data stored in appropriate OS-specific directories
- **✅ Backward Compatible** - Existing API interface unchanged
- **✅ Conversation Tracking** - Messages grouped by conversation with auto-generated titles
- **✅ Rich Metadata** - Provider, model, usage stats, and timestamps stored
- **✅ Zero Configuration** - Database created automatically on first run

### 📁 **Database Location**
- **macOS**: `~/Library/Application Support/EchoV2/echo.db`
- **Windows**: `%APPDATA%\EchoV2\echo.db`
- **Linux**: `~/.local/share/EchoV2/echo.db`

### 🔄 **How It Works**
1. **Send a message** via `/chat` endpoint
2. **User message** automatically saved to database
3. **AI response** saved with metadata (provider, model, usage)
4. **Conversation title** auto-generated from first message
5. **Conversation ID** returned in API response for tracking

### 📊 **Database Schema**
```sql
conversations (
    id INTEGER PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    timestamp TIMESTAMP,
    provider TEXT,
    model TEXT,
    message_metadata JSON  -- Usage stats, finish_reason, etc.
)
```

### 🔗 **API Integration**
```bash
# Send message with optional conversation_id
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "provider": "ollama", "conversation_id": 123}'

# Response includes conversation_id for tracking
{
  "response": "Hello! How can I help you today?",
  "model": "mistral",
  "provider": "ollama",
  "conversation_id": 123,
  "metadata": {...}
}
```

## 📡 API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message to the default provider (now with persistence)
- `POST /chat/conversation` - Send multi-turn conversation (now with persistence)
- `GET /chat/providers` - List available AI providers
- `GET /chat/providers/{provider}/models` - Get models for a provider

### Conversation Management API
- `GET /conversations` - List all conversations with metadata and pagination
- `GET /conversations/{id}` - Get full conversation with all messages
- `DELETE /conversations/{id}` - Delete a conversation and all its messages
- `PUT /conversations/{id}/title` - Update conversation title
- `POST /conversations/{id}/generate-title` - Auto-generate title from first message

### Plugin Management API
- `GET /plugins/` - List all registered providers
- `GET /plugins/{name}/status` - Get provider health and status
- `POST /plugins/{name}/reload` - Hot-reload provider with new config
- `PUT /plugins/{name}/config` - Update provider configuration
- `GET /plugins/{name}/config-schema` - Get configuration schema
- `POST /plugins/discover` - Auto-discover plugins from directory
- `GET /plugins/health` - Health check all providers

### Health & Monitoring
- `GET /health` - System health check
- `GET /health/{provider}` - Provider-specific health check
- `GET /` - API information

## 🎯 First-Time Setup Wizard

EchoV2 features a **modern setup wizard** that gets you chatting in 30 seconds, designed with the user experience of apps like Slack and Discord.

### ✨ **Key Features**
- **🚀 "Start chatting in 30 seconds"** - Streamlined onboarding experience
- **🎯 Smart Provider Selection** - OpenAI, Anthropic, and Google with clear descriptions
- **🔗 Direct API Key Links** - One-click access to provider signup pages
- **🔒 Real-time Validation** - Test API keys before saving configuration
- **⚙️ Advanced Options** - Collapsible section for custom endpoints and local AI
- **📊 Progress Tracking** - Visual progress bar and step indicators
- **🎨 Modern UI** - Gradient backgrounds, smooth animations, and responsive design

### 🔄 **Setup Flow**
1. **Welcome Screen** → Features overview and benefits
2. **Provider Selection** → Choose from OpenAI, Anthropic, or Google
3. **API Key Input** → Secure input with direct signup links
4. **Connection Test** → Real-time validation and error handling
5. **Completion** → Ready to start chatting!

### 🛠️ **Technical Details**
- **localStorage Persistence** - Setup state saved across sessions
- **TypeScript Throughout** - Full type safety and error handling
- **Responsive Design** - Works perfectly on desktop
- **Configuration Integration** - Seamlessly integrates with existing config system

### Example Usage

```bash
# Send a chat message to specific provider (now with persistence)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "provider": "openai", "model": "gpt-4"}'

# Continue a conversation using conversation_id
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me more", "provider": "openai", "conversation_id": 123}'

# List all conversations
curl "http://localhost:8000/conversations"

# Get a specific conversation with all messages
curl "http://localhost:8000/conversations/123"

# Update conversation title
curl -X PUT "http://localhost:8000/conversations/123/title" \
  -H "Content-Type: application/json" \
  -d '{"title": "My AI Research Session"}'

# Auto-generate conversation title
curl -X POST "http://localhost:8000/conversations/123/generate-title"

# Delete a conversation
curl -X DELETE "http://localhost:8000/conversations/123"

# Enable streaming responses
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a story", "provider": "anthropic", "stream": true}'

# Hot-reload a provider with new configuration
curl -X POST "http://localhost:8000/plugins/openai/reload" \
  -H "Content-Type: application/json" \
  -d '{"provider_name": "openai", "config": {"api_key": "sk-new-key...", "default_model": "gpt-4"}}'

# Check provider health
curl "http://localhost:8000/plugins/ollama/status"

# List all providers
curl "http://localhost:8000/plugins/"
```

## 🛠️ Development

### Project Structure

```
EchoV2/
├── config/                 # Configuration files
│   ├── development.yaml
│   └── production.yaml
├── backend/
│   ├── core/
│   │   ├── models/        # Base interfaces & registry
│   │   └── plugins/       # AI provider implementations
│   ├── services/          # Business logic (ChatService, HealthService)
│   ├── api/routes/        # API endpoint definitions
│   └── config/            # Settings management
├── src/
│   ├── types/             # TypeScript interfaces
│   ├── services/          # API client & business services
│   ├── hooks/             # Custom React hooks
│   └── components/        # React UI components
├── src-tauri/             # Tauri desktop configuration
└── dist/                  # Built frontend assets
```

### Development Commands

```bash
# Frontend development with hot reload
npm run dev

# Backend development with auto-reload
cd backend && uvicorn main:app --reload

# Build for production
npm run build

# Build standalone Mac app
npm run build:standalone

# Run tests
npm test                          # Frontend tests (Vitest + RTL)
npm run test:ui                   # Frontend tests with UI
npm run test:coverage             # Frontend test coverage
cd backend && python -m pytest   # Backend tests (pytest)
cd backend && python -m pytest --cov  # Backend test coverage

# Type checking
npm run tsc

# Tauri development (desktop app)
npm run tauri:dev

# Build desktop app
npm run tauri:build
```

### Code Style & Standards

- **Backend**: Python with type hints, Pydantic for validation
- **Frontend**: TypeScript with strict mode, ESLint for linting
- **Architecture**: Clean Architecture with dependency injection
- **API**: RESTful design with OpenAPI/Swagger documentation

## 🔍 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python dependencies
cd backend && pip install -r requirements.txt

# Verify configuration
cd backend && python -c "from config.settings import get_settings; print(get_settings())"
```

**Frontend build errors:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Check TypeScript
npm run tsc
```

**Ollama connection issues:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**Provider not available:**
- Check provider configuration in YAML files
- Verify API keys and endpoints
- Check provider health: `curl http://localhost:8000/health/{provider}`

### Getting Help

- Check the [Issues](https://github.com/coltonbatts/EchoV2/issues) page
- Review configuration files for typos
- Ensure all dependencies are installed
- Check logs for detailed error messages

## 🤝 Contributing

Contributions are welcome! Please feel free to:

1. **Add new AI providers** - Implement `AbstractAIProvider` interface
2. **Improve UI/UX** - Enhance the React frontend
3. **Add features** - Multi-model chats, themes, authentication, etc.
4. **Fix bugs** - Check the issues page
5. **Improve documentation** - Help others understand the codebase

### Development Setup for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-provider`
3. Make your changes following the existing patterns
4. Add tests if applicable
5. Submit a pull request

## 🔥 Plugin Architecture & Hot-Swapping

EchoV2 features a production-ready plugin architecture with zero-downtime management:

### 🚀 **Hot-Swapping Capabilities**
- **Zero-restart provider updates** - Change configurations without stopping the service
- **Dynamic plugin loading** - Add new providers at runtime
- **Automatic failover** - Health monitoring with seamless fallbacks
- **Configuration validation** - Real-time validation with detailed error reporting

### 🛠️ **Developer Experience**
- **Plugin template generator** - Generate boilerplate with `python utils/plugin_template.py`
- **Comprehensive validation** - Type checking and configuration schema validation
- **Live debugging** - Health check endpoints and detailed logging
- **Auto-discovery** - Automatic detection of new plugins in directories

### 📚 **Documentation**
- **[Plugin Architecture Guide](PLUGIN_ARCHITECTURE.md)** - Complete implementation guide
- **Configuration schemas** - Available via API endpoints
- **Best practices** - Type safety, error handling, and performance tips

## 📋 Roadmap

### ✅ **Completed Features**
- [x] **Advanced Plugin Architecture** - Hot-swappable providers with runtime management ✅
- [x] **Streaming Responses** - Real-time message streaming for all providers ✅
- [x] **Multi-Provider Support** - OpenAI, Anthropic, Ollama integration ✅
- [x] **Plugin Hot-Loading** - Dynamic plugin management ✅
- [x] **Standalone Mac App** - PyInstaller + Tauri bundling with auto-backend management ✅
- [x] **Message Persistence** - SQLite database integration for chat history ✅
- [x] **Conversation Management** - Automatic conversation tracking and storage ✅
- [x] **First-Time Setup Wizard** - Modern onboarding experience with guided configuration ✅
- [x] **🆕 Comprehensive Testing** - Full test coverage for backend and frontend ✅
- [x] **🆕 Secure API Key Storage** - System keyring integration with migration ✅
- [x] **🆕 Prompt Injection Protection** - Advanced sanitization and security ✅
- [x] **🆕 Retry Logic & Error Handling** - Intelligent failure recovery ✅
- [x] **🆕 Structured Logging** - Production-ready observability ✅

### 🚧 **Upcoming Features**
- [ ] **Multi-Model Chats** - Switch models mid-conversation
- [ ] **Theme System** - Customizable UI themes
- [ ] **Enhanced Authentication** - Advanced user management
- [ ] **Windows/Linux Standalone** - Cross-platform standalone builds
- [ ] **Export/Import** - Conversation backup and restore
- [ ] **Search & Analytics** - Advanced conversation search and usage analytics

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Tauri, React, TypeScript, and Python**