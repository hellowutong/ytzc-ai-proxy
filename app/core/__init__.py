"""
Core package for AI Gateway.
"""

from core.config_manager import ConfigManager, get_config_manager, get_config
from core.config_template import (
    ConfigTemplate,
    VirtualModelsTemplate,
    FixedNodeTemplate,
    template_registry,
)
from core.logger import get_logger, initialize_logger, shutdown_logger
from core.exceptions import (
    AIGatewayException,
    ConfigurationError,
    ConfigValidationError,
    ConfigTemplateError,
    DatabaseConnectionError,
    MongoDBConnectionError,
    RedisConnectionError,
    QdrantConnectionError,
    LogError,
)
from core.middleware import setup_middleware

__all__ = [
    # Config Manager
    "ConfigManager",
    "get_config_manager",
    "get_config",
    # Config Template
    "ConfigTemplate",
    "VirtualModelsTemplate",
    "FixedNodeTemplate",
    "template_registry",
    # Logger
    "get_logger",
    "initialize_logger",
    "shutdown_logger",
    # Exceptions
    "AIGatewayException",
    "ConfigurationError",
    "ConfigValidationError",
    "ConfigTemplateError",
    "DatabaseConnectionError",
    "MongoDBConnectionError",
    "RedisConnectionError",
    "QdrantConnectionError",
    "LogError",
    # Middleware
    "setup_middleware",
]
