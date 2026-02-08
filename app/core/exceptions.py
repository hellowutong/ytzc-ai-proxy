"""
Custom exceptions for the AI Gateway application.
"""

from typing import Any, Dict, Optional


class AIGatewayException(Exception):
    """Base exception for AI Gateway."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(AIGatewayException):
    """Raised when there's a configuration error."""
    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass


class ConfigTemplateError(ConfigurationError):
    """Raised when template constraints are violated."""
    pass


class DatabaseConnectionError(AIGatewayException):
    """Raised when database connection fails."""
    pass


class MongoDBConnectionError(DatabaseConnectionError):
    """Raised when MongoDB connection fails."""
    pass


class RedisConnectionError(DatabaseConnectionError):
    """Raised when Redis connection fails."""
    pass


class QdrantConnectionError(DatabaseConnectionError):
    """Raised when Qdrant connection fails."""
    pass


class LogError(AIGatewayException):
    """Raised when logging operation fails."""
    pass


class NotFoundException(AIGatewayException):
    """Raised when a resource is not found."""
    pass


class ValidationException(AIGatewayException):
    """Raised when validation fails."""
    pass
