from pydantic import BaseSettings, Field
from typing import Dict, List, Any, Optional
import yaml
import os
from pathlib import Path


class ServerConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class CorsConfig(BaseSettings):
    allowed_origins: List[str] = ["http://localhost:1420"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class AIProviderConfig(BaseSettings):
    base_url: str
    default_model: str
    timeout: int = 60
    api_endpoints: Dict[str, str] = {}


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseSettings):
    server: ServerConfig
    cors: CorsConfig
    ai_providers: Dict[str, Any]
    logging: LoggingConfig
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_config(environment: str = None) -> Settings:
    """Load configuration from YAML file based on environment."""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    config_path = Path(__file__).parent.parent.parent / "config" / f"{environment}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as file:
        config_data = yaml.safe_load(file)
    
    # Convert nested dicts to appropriate models
    config_data["server"] = ServerConfig(**config_data["server"])
    config_data["cors"] = CorsConfig(**config_data["cors"])
    config_data["logging"] = LoggingConfig(**config_data["logging"])
    
    return Settings(**config_data)


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global settings
    if settings is None:
        settings = load_config()
    return settings