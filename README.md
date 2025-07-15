# EchoV2 - Modular AI Chat Platform

A modular, extensible desktop application built with **Tauri**, **React**, **TypeScript**, and **Python FastAPI** featuring a plugin-based architecture for AI model providers. Chat with local and cloud AI models through a unified interface.

## ✨ Features

- 🧩 **Plugin Architecture** - Easy integration of multiple AI providers
- 🔧 **Modular Design** - Clean separation of concerns with service layers
- 🎯 **Type Safety** - Full TypeScript integration across frontend
- ⚙️ **Configuration Management** - Environment-based YAML configuration
- 🔌 **Hot-Swappable Providers** - Switch between AI models dynamically
- 🖥️ **Desktop Native** - Cross-platform desktop app with Tauri
- 🔒 **Local-First** - Support for local AI models (Ollama) and privacy

## 🏗️ Architecture Overview

EchoV2 uses a **modular plugin architecture** that separates concerns and enables easy extensibility:

### Backend Architecture
```
backend/
├── core/
│   ├── models/           # AbstractAIProvider interface & registry
│   └── plugins/          # AI provider implementations (Ollama, OpenAI, etc.)
├── services/             # Business logic layer
├── api/routes/           # RESTful API endpoints
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

## 🚀 Quick Start

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

EchoV2's plugin system makes it easy to add new AI providers:

### Currently Supported
- **Ollama** - Local AI models (Mistral, Llama2, CodeLlama, etc.)

### Easy to Add
- **OpenAI** - GPT models
- **Anthropic** - Claude models  
- **Google** - PaLM/Gemini models
- **Custom APIs** - Any REST-based AI service

### Adding a New Provider

1. Create a new provider class implementing `AbstractAIProvider`:
```python
# backend/core/plugins/openai_provider.py
class OpenAIProvider(AbstractAIProvider):
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        # Implementation here
        pass
```

2. Register the provider in `main.py`:
```python
from core.plugins.openai_provider import OpenAIProvider
registry.register(OpenAIProvider, "openai")
```

3. Add configuration in `config/development.yaml`:
```yaml
ai_providers:
  openai:
    api_key: "your-api-key"
    base_url: "https://api.openai.com/v1"
    default_model: "gpt-4"
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

cors:
  allowed_origins: ["http://localhost:1420"]
```

## 📡 API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message to the default provider
- `POST /chat/conversation` - Send multi-turn conversation
- `GET /chat/providers` - List available AI providers
- `GET /chat/providers/{provider}/models` - Get models for a provider

### Health & Monitoring
- `GET /health` - System health check
- `GET /health/{provider}` - Provider-specific health check
- `GET /` - API information

### Example Usage

```bash
# Send a chat message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "provider": "ollama", "model": "mistral"}'

# Check system health
curl "http://localhost:8000/health"

# List available providers
curl "http://localhost:8000/chat/providers"
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

## 📋 Roadmap

- [ ] **Additional AI Providers**: OpenAI, Anthropic, Google PaLM
- [ ] **Message Persistence**: Database integration for chat history
- [ ] **Conversation Management**: Save/load conversations
- [ ] **Streaming Responses**: Real-time message streaming
- [ ] **Plugin Hot-Loading**: Dynamic plugin management
- [ ] **Multi-Model Chats**: Switch models mid-conversation
- [ ] **Theme System**: Customizable UI themes
- [ ] **Authentication**: User management and API key handling

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Tauri, React, TypeScript, and Python**