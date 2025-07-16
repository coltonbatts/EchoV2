# EchoV2 - Modular AI Chat Platform

A modular, extensible desktop application built with **Tauri**, **React**, **TypeScript**, and **Python FastAPI** featuring a plugin-based architecture for AI model providers. Chat with local and cloud AI models through a unified interface.

## ✨ Features

- 📦 **Standalone Mac App** - Single-click installation with bundled Python backend (NEW!)
- 🚀 **Zero-Dependency Deployment** - No Python or package installation required for end users
- 🧩 **Advanced Plugin Architecture** - Hot-swappable AI providers with zero-restart deployment
- 🔄 **Streaming Support** - Real-time responses from all providers (OpenAI, Anthropic, Ollama)
- 🛠️ **Runtime Management** - Plugin discovery, configuration updates, and health monitoring via API
- 🎯 **Type Safety** - Full TypeScript integration across frontend with comprehensive validation
- ⚙️ **Configuration Management** - Environment-based YAML with runtime updates and validation
- 🔌 **Multi-Provider Support** - OpenAI GPT, Anthropic Claude, and local Ollama models
- 🖥️ **Desktop Native** - Cross-platform desktop app with Tauri
- 🔒 **Local-First** - Support for local AI models (Ollama) and privacy
- 📡 **Developer Tools** - Plugin template generator and comprehensive API documentation

## 🏗️ Architecture Overview

EchoV2 uses a **modular plugin architecture** that separates concerns and enables easy extensibility:

### Backend Architecture
```
backend/
├── core/
│   ├── models/           # AbstractAIProvider interface, registry & manager
│   └── plugins/          # AI provider implementations
│       ├── ollama_provider.py     # Local AI via Ollama
│       ├── openai_provider.py     # OpenAI GPT models
│       └── anthropic_provider.py  # Anthropic Claude models
├── services/             # Business logic layer
├── api/routes/           # RESTful API endpoints
│   ├── chat.py          # Chat completion endpoints
│   ├── health.py        # System health monitoring
│   └── plugins.py       # Plugin management API
├── utils/               # Developer tools
│   └── plugin_template.py # Plugin template generator
└── config/              # Settings and configuration management
```

### Frontend Architecture
```
src/
├── types/               # TypeScript interfaces
├── services/            # API client & business services
├── hooks/               # Custom React hooks (useChat, useConfig)
└── components/          # React UI components
```

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

## 📡 API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message to the default provider
- `POST /chat/conversation` - Send multi-turn conversation
- `GET /chat/providers` - List available AI providers
- `GET /chat/providers/{provider}/models` - Get models for a provider

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

### Example Usage

```bash
# Send a chat message to specific provider
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "provider": "openai", "model": "gpt-4"}'

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

# Build standalone Mac app (NEW!)
npm run build:standalone

# Run tests (when implemented)
npm test
cd backend && python -m pytest

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
3. **Add features** - Message history, conversation management, etc.
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

- [x] **Advanced Plugin Architecture** - Hot-swappable providers with runtime management ✅
- [x] **Streaming Responses** - Real-time message streaming for all providers ✅
- [x] **Multi-Provider Support** - OpenAI, Anthropic, Ollama integration ✅
- [x] **Plugin Hot-Loading** - Dynamic plugin management ✅
- [x] **Standalone Mac App** - PyInstaller + Tauri bundling with auto-backend management ✅
- [ ] **Message Persistence** - Database integration for chat history
- [ ] **Conversation Management** - Save/load conversations
- [ ] **Multi-Model Chats** - Switch models mid-conversation
- [ ] **Theme System** - Customizable UI themes
- [ ] **Authentication** - User management and API key handling
- [ ] **Windows/Linux Standalone** - Cross-platform standalone builds

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Tauri, React, TypeScript, and Python**