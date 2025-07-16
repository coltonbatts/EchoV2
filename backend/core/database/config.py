import os
import platform
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    url: Optional[str] = None
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    class Config:
        env_prefix = "DATABASE_"


def get_user_data_directory() -> Path:
    """Get the user data directory for the application across platforms."""
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\EchoV2
        base_dir = os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return Path(base_dir) / "EchoV2"
    
    elif system == "Darwin":
        # macOS: ~/Library/Application Support/EchoV2
        return Path.home() / "Library" / "Application Support" / "EchoV2"
    
    else:
        # Linux and other Unix-like systems: ~/.local/share/EchoV2
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(base_dir) / "EchoV2"


def get_database_path() -> Path:
    """Get the database file path."""
    data_dir = get_user_data_directory()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "echo.db"


def get_database_url() -> str:
    """Get the database URL for SQLAlchemy."""
    db_path = get_database_path()
    return f"sqlite+aiosqlite:///{db_path}"


def get_database_config() -> DatabaseConfig:
    """Get the database configuration."""
    config = DatabaseConfig()
    if not config.url:
        config.url = get_database_url()
    return config