import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured logs in JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as structured JSON."""
        
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        if hasattr(record, 'provider'):
            log_entry["provider"] = record.provider
            
        if hasattr(record, 'model'):
            log_entry["model"] = record.model
            
        if hasattr(record, 'conversation_id'):
            log_entry["conversation_id"] = record.conversation_id
            
        # Add error information for exceptions
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
            
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'request_id', 'user_id', 'provider', 'model', 'conversation_id'}:
                log_entry[f"extra_{key}"] = value
        
        return json.dumps(log_entry, default=str)


class ChatServiceLogger:
    """
    Specialized logger for chat service operations with structured logging.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _add_context(self, extra: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Add contextual information to log records."""
        context = extra.copy() if extra else {}
        context.update(kwargs)
        return context
        
    def info_chat_request(
        self, 
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        conversation_id: Optional[int] = None,
        prompt_length: Optional[int] = None,
        **kwargs
    ):
        """Log chat request information."""
        extra = self._add_context(
            kwargs.get('extra', {}),
            provider=provider,
            model=model,
            conversation_id=conversation_id,
            prompt_length=prompt_length
        )
        self.logger.info(message, extra=extra)
        
    def info_chat_response(
        self, 
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        conversation_id: Optional[int] = None,
        response_length: Optional[int] = None,
        usage: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log chat response information."""
        extra = self._add_context(
            kwargs.get('extra', {}),
            provider=provider,
            model=model,
            conversation_id=conversation_id,
            response_length=response_length,
            usage=usage
        )
        self.logger.info(message, extra=extra)
        
    def warning_sanitization(
        self,
        message: str,
        original_length: int,
        sanitized_length: int,
        patterns_detected: Optional[list] = None,
        **kwargs
    ):
        """Log prompt sanitization warnings."""
        extra = self._add_context(
            kwargs.get('extra', {}),
            original_length=original_length,
            sanitized_length=sanitized_length,
            patterns_detected=patterns_detected
        )
        self.logger.warning(message, extra=extra)
        
    def error_provider_failure(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        error_type: Optional[str] = None,
        retry_count: Optional[int] = None,
        **kwargs
    ):
        """Log provider failure errors."""
        extra = self._add_context(
            kwargs.get('extra', {}),
            provider=provider,
            model=model,
            error_type=error_type,
            retry_count=retry_count
        )
        self.logger.error(message, extra=extra)
        
    def debug(self, message: str, **kwargs):
        """Log debug information."""
        extra = self._add_context(kwargs.get('extra', {}))
        self.logger.debug(message, extra=extra)
        
    def info(self, message: str, **kwargs):
        """Log general information."""
        extra = self._add_context(kwargs.get('extra', {}))
        self.logger.info(message, extra=extra)
        
    def warning(self, message: str, **kwargs):
        """Log warnings."""
        extra = self._add_context(kwargs.get('extra', {}))
        self.logger.warning(message, extra=extra)
        
    def error(self, message: str, **kwargs):
        """Log errors."""
        extra = self._add_context(kwargs.get('extra', {}))
        self.logger.error(message, extra=extra)


def setup_structured_logging(
    level: str = "INFO",
    use_json: bool = True,
    include_console: bool = True
) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_json: Whether to use JSON formatter
        include_console: Whether to include console output
    """
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(level=numeric_level, handlers=[])
    
    if include_console:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        if use_json:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        
        root_logger.addHandler(console_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_chat_logger(name: str) -> ChatServiceLogger:
    """Get a structured logger for chat service operations."""
    return ChatServiceLogger(name)