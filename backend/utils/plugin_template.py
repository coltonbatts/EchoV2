#!/usr/bin/env python3
"""
Plugin Template Generator for EchoV2

This utility generates a template for creating new AI provider plugins.
"""

import argparse
import os
from pathlib import Path
from datetime import datetime
import sys


PLUGIN_TEMPLATE = '''import asyncio
import time
from typing import Dict, Any, List, AsyncGenerator, Optional
from ..models.base import (
    AbstractAIProvider, ChatRequest, ChatResponse, ProviderStatus, 
    ChatMessage, StreamingChunk, PluginMetadata, PluginCapability, AIModelType
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class {class_name}Provider(AbstractAIProvider):
    """{provider_display_name} AI provider implementation with streaming support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "{default_base_url}")
        self.default_model = config.get("default_model", "{default_model}")
        self.timeout = config.get("timeout", 60)
        
        # Add any provider-specific initialization here
        self._client = None
        
        # Supported models - update this list for your provider
        self._supported_models = [
            "{default_model}",
            # Add more models here
        ]
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="{provider_display_name} Provider",
            version="1.0.0",
            description="{provider_display_name} API provider with streaming support",
            author="Your Name",
            capabilities=[
                PluginCapability.STREAMING,
                # Add more capabilities as needed:
                # PluginCapability.FUNCTION_CALLING,
                # PluginCapability.VISION,
                # PluginCapability.EMBEDDINGS,
            ],
            supported_model_types=[
                AIModelType.CHAT,
                AIModelType.TEXT_GENERATION,
                # Add more model types as needed
            ],
            dependencies=[
                # List your dependencies here, e.g.:
                # "httpx>=0.25.0",
                # "your-provider-sdk>=1.0.0"
            ],
            min_python_version="3.8",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self.api_key:
            raise ValueError("{provider_display_name} API key is required")
        
        # Initialize your provider's client here
        # Example:
        # self._client = YourProviderClient(
        #     api_key=self.api_key,
        #     base_url=self.base_url,
        #     timeout=self.timeout
        # )
        
        logger.info("{provider_display_name} provider initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._client:
            # Close any connections
            # await self._client.close()
            self._client = None
        logger.info("{provider_display_name} provider shutdown completed")
    
    async def reload(self, new_config: Dict[str, Any]) -> None:
        """Reload the provider with new configuration."""
        await self.shutdown()
        self.config = new_config
        self.api_key = new_config.get("api_key")
        self.base_url = new_config.get("base_url", "{default_base_url}")
        self.default_model = new_config.get("default_model", "{default_model}")
        self.timeout = new_config.get("timeout", 60)
        await self.initialize()
        logger.info("{provider_display_name} provider reloaded successfully")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the provided configuration."""
        required_fields = ["api_key"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"Missing required field: {{field}}")
                return False
        
        # Add any additional validation logic here
        
        return True
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        await self._ensure_initialized()
        
        if not self._client:
            raise RuntimeError("{provider_display_name} client not initialized")
        
        model = request.model or self.default_model
        
        # TODO: Implement your provider's chat completion logic here
        # This is a placeholder implementation
        
        try:
            start_time = time.time()
            
            # Example implementation - replace with actual API call:
            # response = await self._client.chat.completions.create(
            #     model=model,
            #     messages=[{{"role": msg.role, "content": msg.content}} for msg in request.messages],
            #     temperature=request.temperature,
            #     max_tokens=request.max_tokens,
            #     # ... other parameters
            # )
            
            # Placeholder response - remove this
            content = f"Hello from {{model}} via {provider_display_name}!"
            end_time = time.time()
            
            return ChatResponse(
                content=content,
                model=model,
                usage={{
                    "prompt_tokens": 0,  # Replace with actual usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }},
                metadata={{
                    "provider": "{provider_name}",
                    "response_time_ms": round((end_time - start_time) * 1000, 2)
                }}
            )
            
        except Exception as e:
            logger.error(f"{provider_display_name} completion failed: {{e}}")
            raise
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate a streaming chat completion response."""
        await self._ensure_initialized()
        
        if not self._client:
            raise RuntimeError("{provider_display_name} client not initialized")
        
        model = request.model or self.default_model
        
        # TODO: Implement your provider's streaming logic here
        # This is a placeholder implementation
        
        try:
            # Example streaming implementation - replace with actual API call:
            # stream = await self._client.chat.completions.create(
            #     model=model,
            #     messages=[{{"role": msg.role, "content": msg.content}} for msg in request.messages],
            #     stream=True,
            #     # ... other parameters
            # )
            # 
            # async for chunk in stream:
            #     if chunk.choices:
            #         delta = chunk.choices[0].delta
            #         if delta.content:
            #             yield StreamingChunk(
            #                 content=delta.content,
            #                 is_final=chunk.choices[0].finish_reason is not None,
            #                 metadata={{"provider": "{provider_name}", "model": model}}
            #             )
            
            # Placeholder streaming - remove this
            placeholder_text = f"Streaming response from {{model}} via {provider_display_name}!"
            for i, char in enumerate(placeholder_text):
                yield StreamingChunk(
                    content=char,
                    is_final=i == len(placeholder_text) - 1,
                    metadata={{"provider": "{provider_name}", "model": model}}
                )
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
        except Exception as e:
            logger.error(f"{provider_display_name} streaming failed: {{e}}")
            raise
    
    async def health_check(self) -> ProviderStatus:
        """Check if the provider is healthy and return available models."""
        try:
            await self._ensure_initialized()
            
            if not self._client:
                return ProviderStatus(
                    available=False,
                    models=[],
                    capabilities=self.get_capabilities(),
                    error="Client not initialized",
                    last_check=datetime.now()
                )
            
            start_time = time.time()
            
            # TODO: Implement actual health check
            # Example:
            # test_response = await self._client.models.list()
            # models = [model.id for model in test_response.data]
            
            # Placeholder health check - replace this
            models = self._supported_models
            is_healthy = True  # Replace with actual health check
            
            end_time = time.time()
            response_time_ms = round((end_time - start_time) * 1000, 2)
            
            if is_healthy:
                return ProviderStatus(
                    available=True,
                    models=models,
                    capabilities=self.get_capabilities(),
                    last_check=datetime.now(),
                    response_time_ms=response_time_ms
                )
            
        except Exception as e:
            logger.error(f"{provider_display_name} health check failed: {{e}}")
            return ProviderStatus(
                available=False,
                models=[],
                capabilities=self.get_capabilities(),
                error=str(e),
                last_check=datetime.now()
            )
        
        return ProviderStatus(
            available=False,
            models=[],
            capabilities=self.get_capabilities(),
            error="Unknown error",
            last_check=datetime.now()
        )
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models."""
        return self._supported_models.copy()
    
    def get_default_model(self) -> str:
        """Return the default model for this provider."""
        return self.default_model
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return the configuration schema for this provider."""
        return {{
            "type": "object",
            "properties": {{
                "api_key": {{
                    "type": "string",
                    "description": "{provider_display_name} API key",
                    "required": True
                }},
                "base_url": {{
                    "type": "string",
                    "description": "{provider_display_name} API base URL",
                    "default": "{default_base_url}"
                }},
                "default_model": {{
                    "type": "string",
                    "description": "Default model to use",
                    "default": "{default_model}",
                    "enum": self._supported_models
                }},
                "timeout": {{
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 60,
                    "minimum": 1
                }}
            }},
            "required": ["api_key"]
        }}
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific model."""
        # TODO: Return actual model information
        model_info = {{
            "{default_model}": {{
                "description": "Default model for {provider_display_name}",
                "capabilities": ["text", "chat"]
            }}
            # Add more model info here
        }}
        
        return model_info.get(model_name)
'''

CONFIG_TEMPLATE = '''  {provider_name}:
    api_key: ""  # Set your {provider_display_name} API key here or via environment variable
    base_url: "{default_base_url}"
    default_model: "{default_model}"
    timeout: 60
'''

REGISTRATION_CODE = '''# Add this to your main.py imports:
from core.plugins.{provider_name}_provider import {class_name}Provider

# Add this to your lifespan function:
registry.register({class_name}Provider, "{provider_name}")
'''

README_TEMPLATE = '''# {provider_display_name} Provider Plugin

This plugin provides integration with {provider_display_name} API for EchoV2.

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Add the provider configuration to your `config/development.yaml`:
```yaml
ai_providers:
{config_example}
```

3. Register the provider in `main.py`:
```python
{registration_code}
```

## Configuration

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| api_key | string | Yes | - | {provider_display_name} API key |
| base_url | string | No | {default_base_url} | API base URL |
| default_model | string | No | {default_model} | Default model to use |
| timeout | integer | No | 60 | Request timeout in seconds |

## Usage

Once configured, you can use the provider through the EchoV2 API:

```bash
curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{{"prompt": "Hello!", "provider": "{provider_name}", "model": "{default_model}"}}'
```

## Development

To modify this provider:

1. Edit `backend/core/plugins/{provider_name}_provider.py`
2. Update the implementation methods (marked with TODO comments)
3. Test your changes with the health check endpoint:
   ```bash
   curl "http://localhost:8000/plugins/{provider_name}/status"
   ```

## API Methods

This provider implements all required AbstractAIProvider methods:

- `chat_completion()` - Generate chat responses
- `chat_completion_stream()` - Generate streaming responses  
- `health_check()` - Check provider health
- `get_supported_models()` - List available models
- `validate_config()` - Validate configuration

## Capabilities

- ✅ Streaming responses
- ⚠️ Function calling (TODO)
- ⚠️ Vision/multimodal (TODO) 
- ⚠️ Embeddings (TODO)

Update the `metadata` property in the provider class to reflect actual capabilities.
'''


def to_class_name(provider_name: str) -> str:
    """Convert provider name to class name (e.g., 'my-provider' -> 'MyProvider')."""
    return ''.join(word.capitalize() for word in provider_name.replace('-', '_').split('_'))


def generate_plugin(
    provider_name: str,
    provider_display_name: str,
    default_base_url: str,
    default_model: str,
    output_dir: Path
) -> None:
    """Generate a complete plugin template."""
    
    class_name = to_class_name(provider_name)
    
    # Create output directory
    plugins_dir = output_dir / "core" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plugin file
    plugin_content = PLUGIN_TEMPLATE.format(
        class_name=class_name,
        provider_name=provider_name,
        provider_display_name=provider_display_name,
        default_base_url=default_base_url,
        default_model=default_model
    )
    
    plugin_file = plugins_dir / f"{provider_name}_provider.py"
    with open(plugin_file, 'w') as f:
        f.write(plugin_content)
    
    # Generate config example
    config_content = CONFIG_TEMPLATE.format(
        provider_name=provider_name,
        provider_display_name=provider_display_name,
        default_base_url=default_base_url,
        default_model=default_model
    )
    
    # Generate registration code
    registration_content = REGISTRATION_CODE.format(
        class_name=class_name,
        provider_name=provider_name
    )
    
    # Generate README
    readme_content = README_TEMPLATE.format(
        provider_display_name=provider_display_name,
        provider_name=provider_name,
        default_base_url=default_base_url,
        default_model=default_model,
        config_example=config_content,
        registration_code=registration_content
    )
    
    readme_file = output_dir / f"{provider_name}_provider_README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Generated plugin template for {provider_display_name}")
    print(f"   Plugin file: {plugin_file}")
    print(f"   README: {readme_file}")
    print()
    print("Next steps:")
    print(f"1. Implement the TODO sections in {plugin_file}")
    print(f"2. Add configuration to config/development.yaml:")
    print(config_content)
    print(f"3. Register the provider in main.py:")
    print(registration_content)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate EchoV2 AI Provider Plugin Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plugin_template.py --name custom-ai --display "Custom AI" --url "https://api.custom-ai.com" --model "gpt-custom"
  python plugin_template.py --name gemini --display "Google Gemini" --url "https://generativelanguage.googleapis.com" --model "gemini-pro"
        """
    )
    
    parser.add_argument(
        "--name", 
        required=True,
        help="Plugin name (lowercase, use hyphens for spaces, e.g., 'custom-ai')"
    )
    
    parser.add_argument(
        "--display",
        required=True, 
        help="Display name for the provider (e.g., 'Custom AI')"
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="Default base URL for the provider API"
    )
    
    parser.add_argument(
        "--model",
        required=True,
        help="Default model name"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "backend",
        help="Output directory (default: ./backend)"
    )
    
    args = parser.parse_args()
    
    # Validate provider name
    if not args.name.replace('-', '').replace('_', '').isalnum():
        print("❌ Error: Provider name must contain only letters, numbers, hyphens, and underscores")
        sys.exit(1)
    
    # Validate output directory
    if not args.output.exists():
        print(f"❌ Error: Output directory does not exist: {args.output}")
        sys.exit(1)
    
    try:
        generate_plugin(
            provider_name=args.name.lower(),
            provider_display_name=args.display,
            default_base_url=args.url,
            default_model=args.model,
            output_dir=args.output
        )
    except Exception as e:
        print(f"❌ Error generating plugin: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()