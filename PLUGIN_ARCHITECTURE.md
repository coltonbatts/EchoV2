# EchoV2 Plugin Architecture Guide

EchoV2 features a comprehensive plugin architecture that allows for easy integration of AI model providers with support for hot-swapping, streaming, and runtime management.

## 🏗️ Architecture Overview

The plugin system is built around several key components:

- **AbstractAIProvider**: Base interface that all providers must implement
- **ProviderRegistry**: Central registry for plugin management and hot-swapping
- **ModelManager**: High-level routing and provider coordination
- **Plugin API**: REST endpoints for runtime plugin management

## 🔌 Creating a New Provider Plugin

### Method 1: Using the Template Generator (Recommended)

Use the built-in template generator to create a new provider:

```bash
cd backend
python utils/plugin_template.py \
  --name "custom-ai" \
  --display "Custom AI" \
  --url "https://api.custom-ai.com" \
  --model "custom-model-v1"
```

This generates:
- Complete provider implementation with TODOs
- Configuration examples
- Registration code
- Documentation

### Method 2: Manual Implementation

1. **Create the provider class**:

```python
# backend/core/plugins/custom_provider.py
from ..models.base import AbstractAIProvider, PluginMetadata, PluginCapability

class CustomProvider(AbstractAIProvider):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Provider",
            version="1.0.0",
            description="Custom AI provider",
            author="Your Name",
            capabilities=[PluginCapability.STREAMING],
            # ... other metadata
        )
    
    async def initialize(self) -> None:
        # Initialize your provider
        pass
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        # Implement chat completion
        pass
    
    # ... implement other required methods
```

2. **Register the provider**:

```python
# main.py
from core.plugins.custom_provider import CustomProvider

# In lifespan function:
registry.register(CustomProvider, "custom")
```

3. **Add configuration**:

```yaml
# config/development.yaml
ai_providers:
  custom:
    api_key: "your-api-key"
    base_url: "https://api.custom-ai.com"
    default_model: "custom-model-v1"
```

## 🔄 Hot-Swapping and Runtime Management

### Plugin Management API

The plugin system provides REST endpoints for runtime management:

```bash
# List all providers
GET /plugins/

# Get provider status and health
GET /plugins/{provider_name}/status

# Reload provider with new config
POST /plugins/{provider_name}/reload
{
  "provider_name": "openai",
  "config": {
    "api_key": "new-key",
    "default_model": "gpt-4"
  }
}

# Update configuration without reload
PUT /plugins/{provider_name}/config
{
  "api_key": "updated-key"
}

# Discover new plugins
POST /plugins/discover

# Health check all providers
GET /plugins/health
```

### Hot-Swapping Examples

**Reload a provider with new configuration**:
```bash
curl -X POST "http://localhost:8000/plugins/openai/reload" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "openai",
    "config": {
      "api_key": "sk-new-key...",
      "default_model": "gpt-4-turbo"
    }
  }'
```

**Update configuration without restart**:
```bash
curl -X PUT "http://localhost:8000/plugins/openai/config" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 0.7,
    "timeout": 120
  }'
```

## 📊 Provider Capabilities

Providers can declare their capabilities using the `PluginCapability` enum:

```python
capabilities=[
    PluginCapability.STREAMING,          # Supports streaming responses
    PluginCapability.FUNCTION_CALLING,   # Supports function/tool calling
    PluginCapability.VISION,             # Supports image understanding
    PluginCapability.EMBEDDINGS,         # Supports text embeddings
    PluginCapability.FINE_TUNING,        # Supports model fine-tuning
    PluginCapability.BATCH_PROCESSING,   # Supports batch requests
]
```

## 🔄 Streaming Support

All providers must implement streaming support:

```python
async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
    """Generate streaming response chunks."""
    async for chunk in your_streaming_api_call():
        yield StreamingChunk(
            content=chunk.text,
            is_final=chunk.is_done,
            metadata={"provider": "your-provider"}
        )
```

Usage:
```python
# Enable streaming in requests
request = ChatRequest(
    messages=[ChatMessage(role="user", content="Hello")],
    stream=True
)

async for chunk in provider.chat_completion_stream(request):
    print(chunk.content, end="", flush=True)
    if chunk.is_final:
        break
```

## ⚙️ Configuration Management

### Configuration Schema

Providers can define JSON schemas for their configuration:

```python
def get_config_schema(self) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "API key for authentication",
                "required": True
            },
            "timeout": {
                "type": "integer", 
                "default": 60,
                "minimum": 1
            }
        },
        "required": ["api_key"]
    }
```

### Environment-Based Configuration

Configuration supports environment-specific overrides:

```yaml
# config/development.yaml
ai_providers:
  openai:
    api_key: "dev-key"
    
# config/production.yaml  
ai_providers:
  openai:
    api_key: "prod-key"
    timeout: 120
```

### Runtime Configuration Updates

Configuration can be updated without restarting:

```python
# Update provider config
await registry.update_provider_config("openai", {
    "timeout": 120,
    "max_retries": 5
})

# Provider automatically reloads with new config
```

## 🔍 Plugin Discovery

The system supports automatic plugin discovery:

```python
# Discover plugins from directory
discovered = await registry.discover_plugins(Path("plugins/"))

# Plugins are automatically registered if they follow naming convention:
# - File: {name}_provider.py  
# - Class: {Name}Provider extends AbstractAIProvider
```

## 🏥 Health Monitoring

Built-in health monitoring with automatic failover:

```python
# Check individual provider health
status = await provider.health_check()
print(f"Available: {status.available}")
print(f"Models: {status.models}")
print(f"Response time: {status.response_time_ms}ms")

# Check all providers
all_status = await registry.health_check_all()
for name, status in all_status.items():
    print(f"{name}: {'✅' if status.available else '❌'}")
```

## 🛡️ Error Handling and Validation

### Configuration Validation

```python
def validate_config(self, config: Dict[str, Any]) -> bool:
    """Validate provider configuration."""
    if not config.get("api_key"):
        logger.error("API key is required")
        return False
    
    if config.get("timeout", 0) <= 0:
        logger.error("Timeout must be positive")
        return False
    
    return True
```

### Graceful Error Handling

```python
try:
    response = await provider.chat_completion(request)
except Exception as e:
    logger.error(f"Provider failed: {e}")
    # Automatic fallback to backup provider
    response = await fallback_provider.chat_completion(request)
```

## 📚 Built-in Provider Examples

### Ollama Provider (Local AI)
- **Capabilities**: Streaming, Embeddings
- **Models**: Mistral, Llama2, CodeLlama, Llama3, Gemma
- **Configuration**: `base_url`, `default_model`, `timeout`

### OpenAI Provider
- **Capabilities**: Streaming, Function Calling, Vision  
- **Models**: GPT-4, GPT-3.5-turbo variants
- **Configuration**: `api_key`, `organization`, `base_url`

### Anthropic Provider  
- **Capabilities**: Streaming, Vision, Multimodal
- **Models**: Claude-3 (Opus/Sonnet/Haiku), Claude-2
- **Configuration**: `api_key`, `max_tokens`, `base_url`

## 🚀 Advanced Features

### Multi-Provider Conversations

Switch providers mid-conversation:

```python
# Start with Ollama
response1 = await model_manager.chat_completion(request, "ollama")

# Switch to OpenAI for complex reasoning
request.messages.append(ChatMessage(role="assistant", content=response1.content))
request.messages.append(ChatMessage(role="user", content="Explain this in detail"))
response2 = await model_manager.chat_completion(request, "openai")
```

### Plugin Lifecycle Events

```python
class YourProvider(AbstractAIProvider):
    async def initialize(self) -> None:
        """Called once during startup"""
        self.setup_connections()
    
    async def shutdown(self) -> None:
        """Called during graceful shutdown"""
        await self.cleanup_resources()
    
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Called during hot-reload"""
        await self.shutdown()
        self.config = new_config
        await self.initialize()
```

### Model Information

Providers can expose detailed model information:

```python
def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
    return {
        "context_length": 4096,
        "training_data": "Up to 2023",
        "capabilities": ["text", "code"],
        "cost_per_token": 0.002
    }
```

## 🔧 Development Tools

### Plugin Testing

```bash
# Test provider health
curl "http://localhost:8000/plugins/your-provider/status"

# Test chat completion  
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "provider": "your-provider"}'

# Test streaming
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "provider": "your-provider", "stream": true}'
```

### Configuration Validation

```bash
# Validate configuration schema
curl "http://localhost:8000/plugins/your-provider/config-schema"

# Test configuration update
curl -X PUT "http://localhost:8000/plugins/your-provider/config" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 30}'
```

## 📋 Best Practices

1. **Always implement streaming** - Even if your provider doesn't natively support it
2. **Provide comprehensive metadata** - Include all capabilities and model types
3. **Validate configuration thoroughly** - Catch errors early with detailed validation
4. **Handle errors gracefully** - Provide meaningful error messages
5. **Use async/await properly** - Don't block the event loop
6. **Log important events** - Help with debugging and monitoring
7. **Follow naming conventions** - Use `{name}_provider.py` and `{Name}Provider` class
8. **Document your provider** - Include configuration options and examples

## 🚨 Troubleshooting

### Common Issues

**Provider not loading**:
- Check file naming convention (`{name}_provider.py`)
- Ensure class extends `AbstractAIProvider`
- Verify all abstract methods are implemented

**Configuration errors**:
- Check YAML syntax in config files
- Ensure required fields are provided
- Validate against provider's schema

**Runtime errors**:
- Check provider logs for detailed error messages
- Verify API keys and endpoints
- Test provider health endpoint

**Hot-reload failures**:
- Ensure new configuration is valid
- Check for resource cleanup in `shutdown()` method
- Verify provider can reinitialize properly

### Debug Commands

```bash
# Check provider status
curl "http://localhost:8000/plugins/{provider}/status"

# View all provider metadata  
curl "http://localhost:8000/plugins/metadata"

# Test health checks
curl "http://localhost:8000/plugins/health"

# Discover available plugins
curl -X POST "http://localhost:8000/plugins/discover"
```

This plugin architecture provides a powerful foundation for integrating any AI provider while maintaining clean interfaces, runtime flexibility, and production-ready features.