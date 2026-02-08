# FastAPI Backend Framework with Template Pattern Configuration Management

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete FastAPI backend framework with ConfigManager using Template Pattern, dual logging system (MongoDB + file), and database connections to MongoDB, Redis, and Qdrant.

**Architecture:** The framework uses a Template Pattern for configuration management where `virtual_models` sections allow dynamic key management (add/delete/modify), while all other sections have fixed structure (values only). The ConfigManager provides hot-reload capabilities and strict validation. Dual logging sends logs to both MongoDB collections and rotating file outputs.

**Tech Stack:** FastAPI, Motor (async MongoDB), redis-py, qdrant-client, Pydantic, PyYAML, watchdog, loguru

---

## Overview

This implementation creates a production-ready FastAPI backend with:
1. **ConfigManager with Template Pattern**: Abstract base class for configuration management
2. **Dual Logging System**: MongoDB + file logging with rotation
3. **Database Connections**: MongoDB (Motor), Redis, Qdrant with health checks
4. **FastAPI Application**: With middleware, CORS, and health check endpoints

---

## Task 1: Create Project Directory Structure

**Step 1: Create all necessary directories**

Run:
```bash
mkdir -p app/core app/db app/models app/utils app/api/v1/endpoints logs/system logs/operation logs/error
```

**Step 2: Verify structure**

Expected structure after creation:
```
app/
├── main.py
├── requirements.txt
├── Dockerfile
├── config.yml
├── core/
│   ├── __init__.py
│   ├── config_manager.py
│   ├── config_template.py
│   ├── logger.py
│   ├── exceptions.py
│   └── middleware.py
├── db/
│   ├── __init__.py
│   ├── mongodb.py
│   ├── redis.py
│   └── qdrant.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   └── log.py
├── api/
│   └── v1/
│       ├── __init__.py
│       └── endpoints/
│           ├── __init__.py
│           └── health.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

**Step 3: Commit**

```bash
git add app/ logs/
git commit -m "chore: create FastAPI project directory structure"
```

---

## Task 2: Create Requirements File

**Files:**
- Create: `app/requirements.txt`

**Step 1: Write requirements.txt**

```
# FastAPI and Server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Configuration
pyyaml==6.0.1
watchdog==3.0.0

# Database
motor==3.3.2
redis==5.0.1
qdrant-client==1.7.0

# Logging
loguru==0.7.2

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0

# Utilities
python-dotenv==1.0.0
httpx==0.26.0
```

**Step 2: Commit**

```bash
git add app/requirements.txt
git commit -m "chore: add Python dependencies"
```

---

## Task 3: Create Core Exceptions

**Files:**
- Create: `app/core/exceptions.py`

**Step 1: Write exceptions.py**

```python
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
```

**Step 2: Commit**

```bash
git add app/core/exceptions.py
git commit -m "feat: add custom exceptions for AI Gateway"
```

---

## Task 4: Create Pydantic Base Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/base.py`

**Step 1: Write models/__init__.py**

```python
"""
Models package.
"""

from app.models.base import BaseModel, TimestampMixin
from app.models.log import LogEntry, SystemLog, OperationLog

__all__ = [
    "BaseModel",
    "TimestampMixin", 
    "LogEntry",
    "SystemLog",
    "OperationLog",
]
```

**Step 2: Write models/base.py**

```python
"""
Base Pydantic models for the application.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def touch(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class ResponseBase(BaseModel):
    """Base response model."""
    
    success: bool = True
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    
class ErrorResponse(ResponseBase):
    """Error response model."""
    
    success: bool = False
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class HealthStatus(BaseModel):
    """Health check status model."""
    
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0.0"
```

**Step 3: Commit**

```bash
git add app/models/
git commit -m "feat: add base Pydantic models"
```

---

## Task 5: Create Log Models

**Files:**
- Create: `app/models/log.py`

**Step 1: Write models/log.py**

```python
"""
Log models for dual logging system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import Field
from app.models.base import BaseModel


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogEntry(BaseModel):
    """Base log entry model."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel = LogLevel.INFO
    message: str
    source: str = "system"  # Component that generated the log
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None  # For request tracing
    
    def to_mongodb_doc(self) -> Dict[str, Any]:
        """Convert to MongoDB document format."""
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
        }
    
    def to_file_line(self) -> str:
        """Convert to file log line format."""
        meta_str = ""
        if self.metadata:
            import json
            meta_str = f" | {json.dumps(self.metadata, ensure_ascii=False)}"
        
        trace_str = f" [{self.trace_id}]" if self.trace_id else ""
        
        return (
            f"{self.timestamp.isoformat()} "
            f"[{self.level.value}] "
            f"[{self.source}]{trace_str} "
            f"{self.message}{meta_str}"
        )


class SystemLog(LogEntry):
    """System log entry."""
    
    log_type: str = "system"
    component: str = ""  # Specific component (e.g., "config_manager", "mongodb")
    event_type: Optional[str] = None  # Event classification
    
    def to_mongodb_doc(self) -> Dict[str, Any]:
        """Convert to MongoDB document format."""
        doc = super().to_mongodb_doc()
        doc.update({
            "log_type": self.log_type,
            "component": self.component,
            "event_type": self.event_type,
        })
        return doc


class OperationLog(LogEntry):
    """Operation log entry for user actions."""
    
    log_type: str = "operation"
    operation: str = ""  # Operation name (e.g., "config_update", "model_call")
    user_id: Optional[str] = None
    resource_type: Optional[str] = None  # Type of resource affected
    resource_id: Optional[str] = None
    status: str = "success"  # success, failure, pending
    duration_ms: Optional[int] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    
    def to_mongodb_doc(self) -> Dict[str, Any]:
        """Convert to MongoDB document format."""
        doc = super().to_mongodb_doc()
        doc.update({
            "log_type": self.log_type,
            "operation": self.operation,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "request_data": self.request_data,
            "response_data": self.response_data,
        })
        return doc
```

**Step 2: Commit**

```bash
git add app/models/log.py
git commit -m "feat: add log models for dual logging system"
```

---

## Task 6: Create Config Template (Template Pattern Base)

**Files:**
- Create: `app/core/config_template.py`

**Step 1: Write config_template.py**

```python
"""
Configuration Template Pattern implementation.

This module defines the Template Pattern for configuration management:
- ConfigTemplate: Abstract base class defining the template interface
- VirtualModelsTemplate: Allows add/delete/modify operations
- FixedNodeTemplate: Only value changes allowed (keys fixed)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple
from app.core.exceptions import ConfigTemplateError, ConfigValidationError


class ConfigTemplate(ABC):
    """
    Abstract base class for configuration templates.
    
    Implements the Template Pattern for configuration management.
    Subclasses define specific constraints for different config sections.
    """
    
    def __init__(self, path: str, allowed_keys: Optional[Set[str]] = None):
        """
        Initialize template.
        
        Args:
            path: Dot-notation path to this config section (e.g., "ai-gateway.router")
            allowed_keys: Set of allowed keys, None means any key is allowed
        """
        self.path = path
        self.allowed_keys = allowed_keys
    
    @abstractmethod
    def can_add_key(self, key: str) -> bool:
        """Check if a new key can be added to this section."""
        pass
    
    @abstractmethod
    def can_delete_key(self, key: str) -> bool:
        """Check if a key can be deleted from this section."""
        pass
    
    @abstractmethod
    def can_modify_structure(self) -> bool:
        """Check if the structure (keys) can be modified."""
        pass
    
    def validate_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a value before setting it.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Base implementation allows any value
        return True, None
    
    def get_allowed_keys(self) -> Optional[Set[str]]:
        """Get the set of allowed keys, None if any key is allowed."""
        return self.allowed_keys
    
    def validate_structure(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the entire structure of a configuration section.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.allowed_keys is None:
            # Any structure is allowed
            return True, None
        
        current_keys = set(config.keys())
        
        # Check for unexpected keys
        unexpected = current_keys - self.allowed_keys
        if unexpected:
            return False, f"Unexpected keys at {self.path}: {unexpected}. " \
                         f"Allowed keys: {self.allowed_keys}"
        
        return True, None


class VirtualModelsTemplate(ConfigTemplate):
    """
    Template for virtual_models section.
    
    Allows full CRUD operations on virtual model configurations.
    Virtual models can be added, deleted, and their structure modified.
    """
    
    def __init__(self):
        super().__init__(
            path="ai-gateway.virtual_models",
            allowed_keys=None  # Any key (virtual model name) is allowed
        )
    
    def can_add_key(self, key: str) -> bool:
        """Always allow adding new virtual models."""
        return True
    
    def can_delete_key(self, key: str) -> bool:
        """Always allow deleting virtual models."""
        return True
    
    def can_modify_structure(self) -> bool:
        """Virtual model structure can be modified."""
        return True
    
    def validate_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate virtual model configuration."""
        if not isinstance(value, dict):
            return False, f"Virtual model '{key}' must be a dictionary"
        
        # Required fields for virtual models
        required_fields = {"proxy_key", "base_url", "current", "use"}
        missing = required_fields - set(value.keys())
        
        if missing:
            return False, f"Virtual model '{key}' missing required fields: {missing}"
        
        return True, None


class FixedNodeTemplate(ConfigTemplate):
    """
    Template for fixed-structure configuration nodes.
    
    Only allows value changes, structure (keys) is fixed.
    Cannot add or delete keys, only modify values.
    """
    
    def __init__(self, path: str, allowed_keys: Set[str], 
                 value_validators: Optional[Dict[str, callable]] = None):
        """
        Initialize fixed node template.
        
        Args:
            path: Dot-notation path to this config section
            allowed_keys: Set of allowed keys (structure is fixed)
            value_validators: Optional dict of key -> validator function
        """
        super().__init__(path, allowed_keys)
        self.value_validators = value_validators or {}
    
    def can_add_key(self, key: str) -> bool:
        """Cannot add keys to fixed nodes."""
        return False
    
    def can_delete_key(self, key: str) -> bool:
        """Cannot delete keys from fixed nodes."""
        return False
    
    def can_modify_structure(self) -> bool:
        """Fixed node structure cannot be modified."""
        return False
    
    def validate_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate value using custom validator if available."""
        if key not in self.allowed_keys:
            return False, f"Key '{key}' is not allowed in {self.path}. " \
                         f"Allowed keys: {self.allowed_keys}"
        
        if key in self.value_validators:
            return self.value_validators[key](value)
        
        return True, None


class RootTemplate(ConfigTemplate):
    """
    Template for root configuration level.
    
    Defines which top-level sections exist and their constraints.
    """
    
    # Define fixed top-level keys
    TOP_LEVEL_KEYS = {
        "app", "storage", "web_search", "ai-gateway", "log"
    }
    
    def __init__(self):
        super().__init__(
            path="root",
            allowed_keys=self.TOP_LEVEL_KEYS
        )
    
    def can_add_key(self, key: str) -> bool:
        """Cannot add new top-level sections."""
        return False
    
    def can_delete_key(self, key: str) -> bool:
        """Cannot delete top-level sections."""
        return False
    
    def can_modify_structure(self) -> bool:
        """Root structure cannot be modified."""
        return False


class TemplateRegistry:
    """
    Registry for configuration templates.
    
    Maps configuration paths to their respective templates.
    """
    
    def __init__(self):
        self._templates: Dict[str, ConfigTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default templates for known config sections."""
        # Root level
        self.register(RootTemplate())
        
        # Virtual models - allows full CRUD
        self.register(VirtualModelsTemplate())
        
        # Fixed sections - only value changes allowed
        self.register(FixedNodeTemplate(
            path="app",
            allowed_keys={"host", "port", "debug"}
        ))
        
        self.register(FixedNodeTemplate(
            path="storage",
            allowed_keys={"mongodb", "qdrant", "redis"}
        ))
        
        self.register(FixedNodeTemplate(
            path="storage.mongodb",
            allowed_keys={"host", "port", "username", "password", "database"}
        ))
        
        self.register(FixedNodeTemplate(
            path="storage.qdrant",
            allowed_keys={"host", "port", "collection"}
        ))
        
        self.register(FixedNodeTemplate(
            path="storage.redis",
            allowed_keys={"host", "port"}
        ))
        
        self.register(FixedNodeTemplate(
            path="log",
            allowed_keys={"system", "operation"}
        ))
        
        self.register(FixedNodeTemplate(
            path="log.system",
            allowed_keys={"level", "storage", "retention"}
        ))
        
        self.register(FixedNodeTemplate(
            path="log.operation",
            allowed_keys={"level", "storage", "retention"}
        ))
    
    def register(self, template: ConfigTemplate):
        """Register a template for a config path."""
        self._templates[template.path] = template
    
    def get_template(self, path: str) -> Optional[ConfigTemplate]:
        """
        Get template for a given path.
        
        Returns exact match or most specific parent template.
        """
        # Try exact match first
        if path in self._templates:
            return self._templates[path]
        
        # Try parent paths (more specific = longer match)
        parts = path.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent_path = ".".join(parts[:i])
            if parent_path in self._templates:
                return self._templates[parent_path]
        
        # Return root template as default
        return self._templates.get("root")
    
    def get_template_for_key(self, parent_path: str, key: str) -> Optional[ConfigTemplate]:
        """Get template for a key within a parent path."""
        full_path = f"{parent_path}.{key}" if parent_path != "root" else key
        return self.get_template(full_path)


# Global template registry instance
template_registry = TemplateRegistry()
```

**Step 2: Commit**

```bash
git add app/core/config_template.py
git commit -m "feat: implement Config Template Pattern with VirtualModels and FixedNode templates"
```

---

## Task 7: Create ConfigManager with Hot Reload

**Files:**
- Create: `app/core/config_manager.py`

**Step 1: Write config_manager.py**

```python
"""
Configuration Manager with Template Pattern and Hot Reload.

Provides singleton ConfigManager with:
- Template-based validation (virtual_models CRUD, others fixed)
- Hot reload support via file watching
- YAML persistence
- Thread-safe operations
"""

import asyncio
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.core.config_template import (
    ConfigTemplate,
    FixedNodeTemplate,
    VirtualModelsTemplate,
    template_registry,
)
from app.core.exceptions import ConfigValidationError, ConfigTemplateError
from app.core.logger import get_logger

# Setup logger for config operations
logger = get_logger("config_manager")


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for configuration file changes."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self._debounce_timer = None
        self._debounce_lock = threading.Lock()
    
    def on_modified(self, event):
        if event.src_path == str(self.config_manager.config_path):
            # Debounce rapid file changes
            with self._debounce_lock:
                if self._debounce_timer:
                    self._debounce_timer.cancel()
                self._debounce_timer = threading.Timer(0.5, self._reload_config)
                self._debounce_timer.start()
    
    def _reload_config(self):
        """Trigger config reload."""
        logger.info("Configuration file changed, reloading...")
        try:
            self.config_manager.reload()
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")


class ConfigManager:
    """
    Singleton Configuration Manager with Template Pattern support.
    
    Features:
    - Template-based validation
    - Hot reload via file watching
    - YAML persistence
    - Thread-safe operations
    """
    
    _instance: Optional['ConfigManager'] = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs) -> 'ConfigManager':
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None, enable_watch: bool = True):
        if self._initialized:
            return
        
        self._initialized = True
        self._config_path = Path(config_path) if config_path else Path("config.yml")
        self._config: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._observer: Optional[Observer] = None
        self._enable_watch = enable_watch
        
        # Load initial configuration
        self.reload()
        
        # Start file watcher if enabled
        if self._enable_watch:
            self._start_watching()
    
    def _start_watching(self):
        """Start watching configuration file for changes."""
        if self._observer:
            return
        
        handler = ConfigFileHandler(self)
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self._config_path.parent),
            recursive=False
        )
        self._observer.start()
        logger.info(f"Started watching config file: {self._config_path}")
    
    def _stop_watching(self):
        """Stop file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching config file")
    
    @property
    def config_path(self) -> Path:
        """Get configuration file path."""
        return self._config_path
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration (read-only access)."""
        with self._lock:
            return self._deep_copy(self._config)
    
    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of an object."""
        import copy
        return copy.deepcopy(obj)
    
    def reload(self):
        """Reload configuration from file."""
        with self._lock:
            if not self._config_path.exists():
                raise ConfigValidationError(
                    f"Configuration file not found: {self._config_path}"
                )
            
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._config = yaml.safe_load(content) or {}
                
                # Validate against templates
                self._validate_full_config()
                
                logger.info("Configuration loaded successfully")
                
            except yaml.YAMLError as e:
                raise ConfigValidationError(f"Invalid YAML format: {e}")
            except Exception as e:
                raise ConfigValidationError(f"Failed to load configuration: {e}")
    
    def save(self):
        """Save current configuration to file."""
        with self._lock:
            try:
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(
                        self._config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False
                    )
                logger.info("Configuration saved successfully")
            except Exception as e:
                raise ConfigValidationError(f"Failed to save configuration: {e}")
    
    def _validate_full_config(self):
        """Validate entire configuration against templates."""
        root_template = template_registry.get_template("root")
        valid, error = root_template.validate_structure(self._config)
        if not valid:
            raise ConfigValidationError(error)
        
        # Validate each top-level section
        for key, value in self._config.items():
            if isinstance(value, dict):
                self._validate_section(key, value)
    
    def _validate_section(self, path: str, section: Dict[str, Any]):
        """Validate a configuration section."""
        template = template_registry.get_template(path)
        
        if template:
            valid, error = template.validate_structure(section)
            if not valid:
                raise ConfigValidationError(error)
        
        # Recursively validate nested sections
        for key, value in section.items():
            if isinstance(value, dict):
                nested_path = f"{path}.{key}"
                self._validate_section(nested_path, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Dot-notation path (e.g., "ai-gateway.virtual_models.demo1")
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        with self._lock:
            parts = key.split(".")
            value = self._config
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return self._deep_copy(value)
    
    def set(self, key: str, value: Any, validate: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Dot-notation path
            value: Value to set
            validate: Whether to validate against templates
        
        Returns:
            Tuple of (success, error_message)
        """
        with self._lock:
            parts = key.split(".")
            parent_path = ".".join(parts[:-1]) if len(parts) > 1 else "root"
            target_key = parts[-1]
            
            # Get template for parent
            parent_template = template_registry.get_template(parent_path)
            
            # Check if we can modify this key
            if parent_template and not parent_template.can_modify_structure():
                # For fixed nodes, check if key exists
                parent = self._get_parent_dict(parts[:-1])
                if parent is None:
                    return False, f"Parent path not found: {parent_path}"
                
                if target_key not in parent:
                    return False, f"Cannot add new key '{target_key}' to fixed structure at {parent_path}"
            
            # Validate value if template exists
            if validate and parent_template:
                valid, error = parent_template.validate_value(target_key, value)
                if not valid:
                    return False, error
            
            # Set the value
            parent = self._get_parent_dict(parts[:-1], create=True)
            if parent is None:
                return False, f"Failed to navigate to path: {parent_path}"
            
            parent[target_key] = value
            
            # Auto-save
            self.save()
            
            logger.info(f"Configuration updated: {key}")
            return True, None
    
    def add_key(self, path: str, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Add a new key to a configuration section.
        
        Only allowed for VirtualModelsTemplate sections.
        
        Args:
            path: Parent path (e.g., "ai-gateway.virtual_models")
            key: New key name
            value: Value for the new key
        
        Returns:
            Tuple of (success, error_message)
        """
        with self._lock:
            template = template_registry.get_template(path)
            
            if not template:
                return False, f"No template found for path: {path}"
            
            if not template.can_add_key(key):
                return False, f"Cannot add key '{key}' to {path}. Structure is fixed."
            
            # Validate the new value
            valid, error = template.validate_value(key, value)
            if not valid:
                return False, error
            
            # Get parent section
            parent = self._get_parent_dict(path.split("."))
            if parent is None:
                return False, f"Parent section not found: {path}"
            
            if key in parent:
                return False, f"Key '{key}' already exists in {path}"
            
            # Add the key
            parent[key] = value
            
            # Auto-save
            self.save()
            
            logger.info(f"Added new key '{key}' to {path}")
            return True, None
    
    def delete_key(self, path: str, key: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a key from a configuration section.
        
        Only allowed for VirtualModelsTemplate sections.
        
        Args:
            path: Parent path
            key: Key to delete
        
        Returns:
            Tuple of (success, error_message)
        """
        with self._lock:
            template = template_registry.get_template(path)
            
            if not template:
                return False, f"No template found for path: {path}"
            
            if not template.can_delete_key(key):
                return False, f"Cannot delete key '{key}' from {path}. Structure is fixed."
            
            # Get parent section
            parent = self._get_parent_dict(path.split("."))
            if parent is None:
                return False, f"Parent section not found: {path}"
            
            if key not in parent:
                return False, f"Key '{key}' not found in {path}"
            
            # Delete the key
            del parent[key]
            
            # Auto-save
            self.save()
            
            logger.info(f"Deleted key '{key}' from {path}")
            return True, None
    
    def _get_parent_dict(self, parts: List[str], create: bool = False) -> Optional[Dict[str, Any]]:
        """
        Navigate to a parent dictionary by path parts.
        
        Args:
            parts: Path parts to navigate
            create: If True, create missing intermediate sections
        
        Returns:
            Parent dictionary or None if not found
        """
        current = self._config
        
        for part in parts:
            if part == "":
                continue
            
            if part not in current:
                if create:
                    current[part] = {}
                else:
                    return None
            
            if not isinstance(current[part], dict):
                if create:
                    current[part] = {}
                else:
                    return None
            
            current = current[part]
        
        return current
    
    def get_virtual_models(self) -> Dict[str, Any]:
        """Get all virtual models configuration."""
        return self.get("ai-gateway.virtual_models", {})
    
    def get_virtual_model(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific virtual model configuration."""
        models = self.get_virtual_models()
        return models.get(name)
    
    def add_virtual_model(self, name: str, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Add a new virtual model."""
        return self.add_key("ai-gateway.virtual_models", name, config)
    
    def delete_virtual_model(self, name: str) -> Tuple[bool, Optional[str]]:
        """Delete a virtual model."""
        return self.delete_key("ai-gateway.virtual_models", name)
    
    def get_database_config(self, db_type: str) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get(f"storage.{db_type}", {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return self.get("app", {})
    
    def get_log_config(self, log_type: str) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get(f"log.{log_type}", {})
    
    def shutdown(self):
        """Shutdown config manager and file watcher."""
        self._stop_watching()
        ConfigManager._instance = None
        self._initialized = False


# Convenience function to get config manager instance
def get_config_manager(config_path: Optional[str] = None, 
                       enable_watch: bool = True) -> ConfigManager:
    """
    Get or create ConfigManager instance.
    
    Args:
        config_path: Path to config file (default: config.yml)
        enable_watch: Whether to enable file watching
    
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_path, enable_watch)


# Global config accessor
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value by key (convenience function)."""
    return get_config_manager().get(key, default)
```

**Step 2: Commit**

```bash
git add app/core/config_manager.py
git commit -m "feat: implement ConfigManager with Template Pattern and hot reload"
```

---

## Task 8: Create Dual Logger (MongoDB + File)

**Files:**
- Create: `app/core/logger.py`

**Step 1: Write logger.py**

```python
"""
Dual Logging System: MongoDB + File Output.

Features:
- Logs to MongoDB collections (system_logs, operation_logs)
- Logs to rotating files (daily rotation, 30-day retention)
- ERROR logs mandatory to file
- Async MongoDB logging
- Log levels: DEBUG, INFO, WARNING, ERROR
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from queue import Queue
from threading import Thread, Lock

from loguru import logger as loguru_logger

from app.models.log import LogEntry, LogLevel, SystemLog, OperationLog
from app.core.exceptions import LogError


class MongoDBLogHandler:
    """Async handler for MongoDB logging."""
    
    def __init__(self, mongodb_client=None):
        self.mongodb_client = mongodb_client
        self._queue: Queue = Queue()
        self._lock = Lock()
        self._worker_thread: Optional[Thread] = None
        self._running = False
        self._buffer: list = []
        self._buffer_size = 100
        self._flush_interval = 5  # seconds
    
    def start(self):
        """Start the async logging worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def stop(self):
        """Stop the logging worker and flush remaining logs."""
        self._running = False
        if self._worker_thread:
            self._flush_buffer()
            self._worker_thread.join(timeout=10)
    
    def _worker_loop(self):
        """Worker thread loop for async MongoDB writes."""
        last_flush = datetime.now()
        
        while self._running:
            try:
                # Process queue
                while not self._queue.empty():
                    log_entry = self._queue.get_nowait()
                    self._buffer.append(log_entry)
                    
                    if len(self._buffer) >= self._buffer_size:
                        self._flush_buffer()
                
                # Periodic flush
                if (datetime.now() - last_flush).seconds >= self._flush_interval:
                    if self._buffer:
                        self._flush_buffer()
                    last_flush = datetime.now()
                
                import time
                time.sleep(0.1)
                
            except Exception as e:
                # Log to stderr if MongoDB logging fails
                print(f"MongoDB logging error: {e}", file=sys.stderr)
    
    def _flush_buffer(self):
        """Flush buffered logs to MongoDB."""
        if not self._buffer or not self.mongodb_client:
            return
        
        try:
            with self._lock:
                logs_to_write = self._buffer[:]
                self._buffer = []
            
            # Separate logs by type
            system_logs = [log for log in logs_to_write if isinstance(log, SystemLog)]
            operation_logs = [log for log in logs_to_write if isinstance(log, OperationLog)]
            
            # Write to appropriate collections
            if system_logs and self.mongodb_client:
                collection = self.mongodb_client.system_logs
                docs = [log.to_mongodb_doc() for log in system_logs]
                collection.insert_many(docs)
            
            if operation_logs and self.mongodb_client:
                collection = self.mongodb_client.operation_logs
                docs = [log.to_mongodb_doc() for log in operation_logs]
                collection.insert_many(docs)
                
        except Exception as e:
            print(f"Failed to flush logs to MongoDB: {e}", file=sys.stderr)
    
    def emit(self, log_entry: LogEntry):
        """Queue a log entry for MongoDB writing."""
        if self._running:
            self._queue.put(log_entry)


class DualLogger:
    """
    Dual logging system that logs to both MongoDB and file.
    
    Features:
    - MongoDB: Async writes to system_logs and operation_logs collections
    - File: Daily rotation, 30-day retention, ERROR logs mandatory
    """
    
    def __init__(self, name: str = "app"):
        self.name = name
        self._mongodb_handler: Optional[MongoDBLogHandler] = None
        self._log_dir: Optional[Path] = None
        self._initialized = False
        self._mongodb_client = None
        
        # Configure loguru logger
        self._logger = loguru_logger.bind(name=name)
        self._configure_loguru()
    
    def _configure_loguru(self):
        """Configure loguru logger."""
        # Remove default handler
        loguru_logger.remove()
        
        # Console handler for development
        loguru_logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level="DEBUG",
            colorize=True
        )
    
    def initialize(self, 
                   mongodb_client=None,
                   log_dir: str = "./logs",
                   system_level: str = "INFO",
                   operation_level: str = "INFO"):
        """
        Initialize the dual logger.
        
        Args:
            mongodb_client: Motor/MongoDB client
            log_dir: Directory for log files
            system_level: Log level for system logs
            operation_level: Log level for operation logs
        """
        if self._initialized:
            return
        
        self._mongodb_client = mongodb_client
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup MongoDB handler
        if mongodb_client:
            self._mongodb_handler = MongoDBLogHandler(mongodb_client)
            self._mongodb_handler.start()
        
        # Setup file handlers with rotation
        self._setup_file_handlers(system_level, operation_level)
        
        self._initialized = True
        self.info("Dual logger initialized")
    
    def _setup_file_handlers(self, system_level: str, operation_level: str):
        """Setup file logging with rotation."""
        # System logs
        system_log_path = self._log_dir / "system" / "system_{time:YYYY-MM-DD}.log"
        system_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(system_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level=system_level,
            rotation="00:00",  # Daily rotation
            retention="30 days",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("log_type") == "system"
        )
        
        # Operation logs
        operation_log_path = self._log_dir / "operation" / "operation_{time:YYYY-MM-DD}.log"
        operation_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(operation_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level=operation_level,
            rotation="00:00",
            retention="30 days",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("log_type") == "operation"
        )
        
        # ERROR logs (mandatory, includes all log types)
        error_log_path = self._log_dir / "error" / "error_{time:YYYY-MM-DD}.log"
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(error_log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
            level="ERROR",
            rotation="00:00",
            retention="30 days",
            encoding="utf-8"
        )
    
    def _log(self, level: LogLevel, message: str, 
             log_type: str = "system",
             source: str = "system",
             metadata: Optional[Dict[str, Any]] = None,
             **kwargs):
        """Internal logging method."""
        # Create log entry for MongoDB
        if log_type == "system":
            log_entry = SystemLog(
                level=level,
                message=message,
                source=source,
                metadata=metadata or {},
                **kwargs
            )
        else:
            log_entry = OperationLog(
                level=level,
                message=message,
                source=source,
                metadata=metadata or {},
                **kwargs
            )
        
        # Log to MongoDB (async)
        if self._mongodb_handler:
            self._mongodb_handler.emit(log_entry)
        
        # Log to file via loguru
        extra = {"log_type": log_type, "name": self.name}
        extra.update(kwargs)
        
        log_method = getattr(self._logger, level.value.lower())
        log_method(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log WARNING level message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def shutdown(self):
        """Shutdown logger and cleanup."""
        if self._mongodb_handler:
            self._mongodb_handler.stop()
        self.info("Dual logger shutdown")


# Global logger instance
_logger_instance: Optional[DualLogger] = None
_logger_lock = Lock()


def get_logger(name: str = "app") -> DualLogger:
    """
    Get or create logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        DualLogger instance
    """
    global _logger_instance
    
    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = DualLogger(name)
        return _logger_instance


def initialize_logger(mongodb_client=None, log_dir: str = "./logs",
                     system_level: str = "INFO", operation_level: str = "INFO"):
    """
    Initialize the global logger.
    
    Args:
        mongodb_client: MongoDB client for async logging
        log_dir: Directory for log files
        system_level: System log level
        operation_level: Operation log level
    """
    logger = get_logger()
    logger.initialize(
        mongodb_client=mongodb_client,
        log_dir=log_dir,
        system_level=system_level,
        operation_level=operation_level
    )
    return logger


def shutdown_logger():
    """Shutdown the global logger."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.shutdown()
        _logger_instance = None
```

**Step 2: Commit**

```bash
git add app/core/logger.py
git commit -m "feat: implement dual logging system (MongoDB + file with rotation)"
```

---

## Task 9: Create Database Connections

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/mongodb.py`
- Create: `app/db/redis.py`
- Create: `app/db/qdrant.py`

**Step 1: Write db/__init__.py**

```python
"""
Database connections package.
"""

from app.db.mongodb import MongoDBClient, get_mongodb_client
from app.db.redis import RedisClient, get_redis_client
from app.db.qdrant import QdrantClient, get_qdrant_client

__all__ = [
    "MongoDBClient",
    "get_mongodb_client",
    "RedisClient", 
    "get_redis_client",
    "QdrantClient",
    "get_qdrant_client",
]
```

**Step 2: Write db/mongodb.py**

```python
"""
MongoDB connection with Motor async driver.

Features:
- Async connection pooling
- Connection retry logic
- Health check support
- Auto-reconnection
"""

import asyncio
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config_manager import get_config
from app.core.exceptions import MongoDBConnectionError
from app.core.logger import get_logger

logger = get_logger("mongodb")


class MongoDBClient:
    """MongoDB client with connection pooling and retry logic."""
    
    _instance: Optional['MongoDBClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'MongoDBClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._config: Optional[Dict[str, Any]] = None
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to MongoDB with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.mongodb", {})
        
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 27017)
        username = self._config.get("username")
        password = self._config.get("password")
        database = self._config.get("database", "ai_gateway")
        
        # Build connection string
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            uri = f"mongodb://{host}:{port}/{database}"
        
        # Connect with retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MongoDB at {host}:{port} (attempt {attempt + 1}/{max_retries})")
                
                self._client = AsyncIOMotorClient(
                    uri,
                    serverSelectionTimeoutMS=5000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                )
                
                # Verify connection
                await self._client.admin.command('ping')
                
                self._db = self._client[database]
                
                # Create collections if they don't exist
                await self._ensure_collections()
                
                logger.info("MongoDB connected successfully")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise MongoDBConnectionError(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
    
    async def _ensure_collections(self):
        """Ensure required collections exist."""
        if not self._db:
            return
        
        collections = await self._db.list_collection_names()
        
        # Create system_logs collection
        if "system_logs" not in collections:
            await self._db.create_collection("system_logs")
            await self._db.system_logs.create_index("timestamp")
            await self._db.system_logs.create_index("level")
            await self._db.system_logs.create_index("source")
            logger.info("Created system_logs collection")
        
        # Create operation_logs collection
        if "operation_logs" not in collections:
            await self._db.create_collection("operation_logs")
            await self._db.operation_logs.create_index("timestamp")
            await self._db.operation_logs.create_index("level")
            await self._db.operation_logs.create_index("operation")
            await self._db.operation_logs.create_index("user_id")
            logger.info("Created operation_logs collection")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB disconnected")
    
    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy."""
        if not self._client:
            return False
        
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Get MongoDB client."""
        return self._client
    
    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get MongoDB database."""
        return self._db
    
    @property
    def system_logs(self):
        """Get system_logs collection."""
        if self._db:
            return self._db.system_logs
        return None
    
    @property
    def operation_logs(self):
        """Get operation_logs collection."""
        if self._db:
            return self._db.operation_logs
        return None


# Global instance accessor
async def get_mongodb_client() -> MongoDBClient:
    """Get MongoDB client instance."""
    client = MongoDBClient()
    if client.client is None:
        await client.connect()
    return client
```

**Step 3: Write db/redis.py**

```python
"""
Redis connection with async support.

Features:
- Connection pooling
- Connection retry logic
- Health check support
"""

import asyncio
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError

from app.core.config_manager import get_config
from app.core.exceptions import RedisConnectionError as CustomRedisConnectionError
from app.core.logger import get_logger

logger = get_logger("redis")


class RedisClient:
    """Redis client with connection pooling and retry logic."""
    
    _instance: Optional['RedisClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'RedisClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[aioredis.Redis] = None
        self._config: Optional[Dict[str, Any]] = None
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to Redis with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.redis", {})
        
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 6379)
        
        # Connect with retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Redis at {host}:{port} (attempt {attempt + 1}/{max_retries})")
                
                self._client = aioredis.Redis(
                    host=host,
                    port=port,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30,
                    max_connections=50,
                )
                
                # Verify connection
                await self._client.ping()
                
                logger.info("Redis connected successfully")
                return
                
            except (RedisConnectionError, TimeoutError) as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise CustomRedisConnectionError(f"Failed to connect to Redis after {max_retries} attempts: {e}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis disconnected")
    
    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self._client:
            return False
        
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[aioredis.Redis]:
        """Get Redis client."""
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._client:
            return None
        return await self._client.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """Set key-value pair with optional expiration."""
        if not self._client:
            return
        await self._client.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """Delete key."""
        if not self._client:
            return
        await self._client.delete(key)


# Global instance accessor
async def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    client = RedisClient()
    if client.client is None:
        await client.connect()
    return client
```

**Step 4: Write db/qdrant.py**

```python
"""
Qdrant connection for vector database.

Features:
- Async connection
- Collection management
- Health check support
"""

import asyncio
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient as SyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from app.core.config_manager import get_config
from app.core.exceptions import QdrantConnectionError
from app.core.logger import get_logger

logger = get_logger("qdrant")


class QdrantClient:
    """Qdrant client wrapper for vector database operations."""
    
    _instance: Optional['QdrantClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'QdrantClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[SyncQdrantClient] = None
        self._config: Optional[Dict[str, Any]] = None
    
    def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to Qdrant with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.qdrant", {})
        
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 6333)
        collection = self._config.get("collection", "knowledge_base")
        
        # Connect with retry
        import time
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Qdrant at {host}:{port} (attempt {attempt + 1}/{max_retries})")
                
                self._client = SyncQdrantClient(host=host, port=port)
                
                # Verify connection by getting collections
                self._client.get_collections()
                
                # Ensure collection exists
                self._ensure_collection(collection)
                
                logger.info("Qdrant connected successfully")
                return
                
            except Exception as e:
                logger.warning(f"Qdrant connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise QdrantConnectionError(f"Failed to connect to Qdrant after {max_retries} attempts: {e}")
    
    def _ensure_collection(self, collection_name: str):
        """Ensure collection exists, create if not."""
        if not self._client:
            return
        
        try:
            self._client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' exists")
        except UnexpectedResponse:
            # Collection doesn't exist, create it
            logger.info(f"Creating collection '{collection_name}'")
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"Collection '{collection_name}' created")
    
    def disconnect(self):
        """Disconnect from Qdrant."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Qdrant disconnected")
    
    def health_check(self) -> bool:
        """Check if Qdrant connection is healthy."""
        if not self._client:
            return False
        
        try:
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[SyncQdrantClient]:
        """Get Qdrant client."""
        return self._client
    
    def get_collection(self, collection_name: Optional[str] = None):
        """Get collection handle."""
        if not self._client:
            return None
        
        name = collection_name or self._config.get("collection", "knowledge_base")
        return name


# Global instance accessor
def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    client = QdrantClient()
    if client.client is None:
        client.connect()
    return client
```

**Step 5: Commit**

```bash
git add app/db/
git commit -m "feat: implement database connections (MongoDB, Redis, Qdrant)"
```

---

## Task 10: Create Middleware

**Files:**
- Create: `app/core/middleware.py`

**Step 1: Write middleware.py**

```python
"""
FastAPI middleware for CORS, logging, and error handling.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger
from app.models.base import ErrorResponse

logger = get_logger("middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate trace ID
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request {request.method} {request.url.path}",
            log_type="operation",
            operation="http_request",
            trace_id=trace_id,
            request_data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response
            logger.info(
                f"Response {response.status_code} in {duration_ms}ms",
                log_type="operation",
                operation="http_response",
                trace_id=trace_id,
                duration_ms=duration_ms,
                response_data={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                f"Request failed: {str(e)}",
                log_type="operation",
                operation="http_error",
                trace_id=trace_id,
                duration_ms=duration_ms,
            )
            
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions and return consistent error responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except Exception as e:
            trace_id = getattr(request.state, 'trace_id', 'unknown')
            
            logger.error(
                f"Unhandled exception: {str(e)}",
                log_type="system",
                source="error_middleware",
                trace_id=trace_id,
                metadata={"exception": str(e), "type": type(e).__name__}
            )
            
            # Return JSON error response
            from fastapi.responses import JSONResponse
            
            error_response = ErrorResponse(
                success=False,
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                error_details={"trace_id": trace_id}
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )


def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI app."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    logger.info("Middleware setup complete")
```

**Step 2: Commit**

```bash
git add app/core/middleware.py
git commit -m "feat: add FastAPI middleware (CORS, logging, error handling)"
```

---

## Task 11: Create Core Package __init__.py

**Files:**
- Create: `app/core/__init__.py`

**Step 1: Write core/__init__.py**

```python
"""
Core package for AI Gateway.
"""

from app.core.config_manager import ConfigManager, get_config_manager, get_config
from app.core.config_template import (
    ConfigTemplate,
    VirtualModelsTemplate,
    FixedNodeTemplate,
    template_registry,
)
from app.core.logger import get_logger, initialize_logger, shutdown_logger
from app.core.exceptions import (
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
from app.core.middleware import setup_middleware

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
```

**Step 2: Commit**

```bash
git add app/core/__init__.py
git commit -m "chore: add core package exports"
```

---

## Task 12: Create Health Check Endpoints

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/v1/__init__.py`
- Create: `app/api/v1/endpoints/__init__.py`
- Create: `app/api/v1/endpoints/health.py`

**Step 1: Write api/__init__.py**

```python
"""
API package.
"""
```

**Step 2: Write api/v1/__init__.py**

```python
"""
API v1 package.
"""

from app.api.v1.endpoints.health import router as health_router

__all__ = ["health_router"]
```

**Step 3: Write api/v1/endpoints/__init__.py**

```python
"""
API v1 endpoints.
"""
```

**Step 4: Write api/v1/endpoints/health.py**

```python
"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from app.models.base import HealthStatus, ResponseBase
from app.db.mongodb import get_mongodb_client
from app.db.redis import get_redis_client
from app.db.qdrant import get_qdrant_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Overall health check endpoint.
    Returns status of all services.
    """
    services = {}
    overall_status = "healthy"
    
    # Check MongoDB
    try:
        mongo_client = await get_mongodb_client()
        mongo_healthy = await mongo_client.health_check()
        services["mongodb"] = "healthy" if mongo_healthy else "unhealthy"
        if not mongo_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["mongodb"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Redis
    try:
        redis_client = await get_redis_client()
        redis_healthy = await redis_client.health_check()
        services["redis"] = "healthy" if redis_healthy else "unhealthy"
        if not redis_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Qdrant
    try:
        qdrant_client = get_qdrant_client()
        qdrant_healthy = qdrant_client.health_check()
        services["qdrant"] = "healthy" if qdrant_healthy else "unhealthy"
        if not qdrant_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["qdrant"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        services=services
    )


@router.get("/ready", response_model=ResponseBase)
async def readiness_check():
    """
    Readiness probe for Kubernetes.
    Returns 200 when application is ready to serve traffic.
    """
    return ResponseBase(
        success=True,
        message="Application is ready"
    )


@router.get("/live", response_model=ResponseBase)
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    Returns 200 when application is alive.
    """
    return ResponseBase(
        success=True,
        message="Application is alive"
    )


@router.get("/mongodb", response_model=ResponseBase)
async def mongodb_health():
    """MongoDB specific health check."""
    try:
        client = await get_mongodb_client()
        healthy = await client.health_check()
        return ResponseBase(
            success=healthy,
            message="MongoDB is healthy" if healthy else "MongoDB is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"MongoDB health check failed: {str(e)}"
        )


@router.get("/redis", response_model=ResponseBase)
async def redis_health():
    """Redis specific health check."""
    try:
        client = await get_redis_client()
        healthy = await client.health_check()
        return ResponseBase(
            success=healthy,
            message="Redis is healthy" if healthy else "Redis is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"Redis health check failed: {str(e)}"
        )


@router.get("/qdrant", response_model=ResponseBase)
async def qdrant_health():
    """Qdrant specific health check."""
    try:
        client = get_qdrant_client()
        healthy = client.health_check()
        return ResponseBase(
            success=healthy,
            message="Qdrant is healthy" if healthy else "Qdrant is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"Qdrant health check failed: {str(e)}"
        )
```

**Step 5: Commit**

```bash
git add app/api/
git commit -m "feat: add health check endpoints for all services"
```

---

## Task 13: Create Utils Helpers

**Files:**
- Create: `app/utils/__init__.py`
- Create: `app/utils/helpers.py`

**Step 1: Write utils/__init__.py**

```python
"""
Utilities package.
"""

from app.utils.helpers import generate_id, deep_merge, truncate_string

__all__ = ["generate_id", "deep_merge", "truncate_string"]
```

**Step 2: Write utils/helpers.py**

```python
"""
Utility helper functions.
"""

import uuid
from typing import Any, Dict


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with values to override
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: Input string
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with dot notation."""
    keys = key.split(".")
    value = dictionary
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value
```

**Step 3: Commit**

```bash
git add app/utils/
git commit -m "chore: add utility helper functions"
```

---

## Task 14: Create FastAPI Main Application

**Files:**
- Create: `app/main.py`

**Step 1: Write main.py**

```python
"""
AI Gateway FastAPI Application Entry Point.

This is the main entry point for the FastAPI application.
It initializes all components including:
- Configuration Manager with hot reload
- Dual logging system (MongoDB + file)
- Database connections (MongoDB, Redis, Qdrant)
- API routes and middleware
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core import (
    get_config_manager,
    initialize_logger,
    shutdown_logger,
    setup_middleware,
    get_logger,
)
from app.db.mongodb import get_mongodb_client
from app.db.redis import get_redis_client
from app.db.qdrant import get_qdrant_client
from app.api.v1 import health_router

# Get logger
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up AI Gateway...")
    
    try:
        # Initialize ConfigManager
        config_path = os.getenv("CONFIG_PATH", "config.yml")
        config_manager = get_config_manager(config_path, enable_watch=True)
        logger.info(f"Configuration loaded from {config_path}")
        
        # Get log configuration
        log_config = config_manager.get_log_config("system")
        log_level = log_config.get("level", "INFO")
        log_path = log_config.get("storage", {}).get("path", "./logs")
        
        # Connect to MongoDB first (needed for logging)
        mongo_client = await get_mongodb_client()
        logger.info("MongoDB connection established")
        
        # Initialize logger with MongoDB
        initialize_logger(
            mongodb_client=mongo_client,
            log_dir=log_path,
            system_level=log_level,
            operation_level="INFO"
        )
        logger.info("Dual logging system initialized")
        
        # Connect to Redis
        redis_client = await get_redis_client()
        logger.info("Redis connection established")
        
        # Connect to Qdrant
        qdrant_client = get_qdrant_client()
        logger.info("Qdrant connection established")
        
        logger.info("AI Gateway startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Gateway...")
    
    try:
        # Disconnect from databases
        mongo_client = MongoDBClient()
        await mongo_client.disconnect()
        logger.info("MongoDB disconnected")
        
        redis_client = RedisClient()
        await redis_client.disconnect()
        logger.info("Redis disconnected")
        
        qdrant_client = QdrantClient()
        qdrant_client.disconnect()
        logger.info("Qdrant disconnected")
        
        # Shutdown logger
        shutdown_logger()
        
        # Shutdown ConfigManager
        config_manager = get_config_manager()
        config_manager.shutdown()
        
        logger.info("AI Gateway shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Gateway",
    description="AI Gateway with Template Pattern Configuration Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/config")
async def get_current_config():
    """Get current configuration (for admin purposes)."""
    from app.core import get_config_manager
    config_manager = get_config_manager()
    return config_manager.config


# Import at end to avoid circular imports
from app.db.mongodb import MongoDBClient
from app.db.redis import RedisClient
from app.db.qdrant import QdrantClient


if __name__ == "__main__":
    import uvicorn
    
    # Get app config
    config_manager = get_config_manager()
    app_config = config_manager.get_app_config()
    
    host = app_config.get("host", "0.0.0.0")
    port = app_config.get("port", 8000)
    debug = app_config.get("debug", False)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
```

**Step 2: Commit**

```bash
git add app/main.py
git commit -m "feat: create FastAPI main application with lifespan management"
```

---

## Task 15: Create Dockerfile

**Files:**
- Create: `app/Dockerfile`

**Step 1: Write Dockerfile**

```dockerfile
# AI Gateway FastAPI Application Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create log directories
RUN mkdir -p /app/logs/system /app/logs/operation /app/logs/error

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config.yml

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Step 2: Commit**

```bash
git add app/Dockerfile
git commit -m "chore: add Dockerfile for FastAPI application"
```

---

## Task 16: Create Test Cases

**Files:**
- Create: `app/tests/__init__.py`
- Create: `app/tests/test_config_manager.py`
- Create: `app/tests/test_logger.py`

**Step 1: Write tests/__init__.py**

```python
"""
Test package.
"""
```

**Step 2: Write tests/test_config_manager.py**

```python
"""
Tests for ConfigManager with Template Pattern.
"""

import pytest
import tempfile
import os
from pathlib import Path

from app.core.config_manager import ConfigManager, get_config_manager
from app.core.exceptions import ConfigValidationError, ConfigTemplateError


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        config_content = """
app:
  host: "0.0.0.0"
  port: 8000
  debug: false

storage:
  mongodb:
    host: "mongo"
    port: 27017

ai-gateway:
  virtual_models:
    test_model:
      proxy_key: "test_key"
      base_url: "http://test.com"
      current: "small"
      use: true
      small:
        model: "test-small"
        api_key: "key"
        base_url: "http://test.com"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create ConfigManager instance."""
        # Reset singleton for tests
        ConfigManager._instance = None
        cm = ConfigManager(temp_config_file, enable_watch=False)
        yield cm
        cm.shutdown()
        ConfigManager._instance = None
    
    def test_singleton_pattern(self, temp_config_file):
        """Test that ConfigManager is a singleton."""
        ConfigManager._instance = None
        cm1 = ConfigManager(temp_config_file, enable_watch=False)
        cm2 = ConfigManager(temp_config_file, enable_watch=False)
        
        assert cm1 is cm2
        
        cm1.shutdown()
        ConfigManager._instance = None
    
    def test_load_config(self, config_manager):
        """Test loading configuration from file."""
        config = config_manager.config
        
        assert "app" in config
        assert config["app"]["host"] == "0.0.0.0"
        assert config["app"]["port"] == 8000
    
    def test_get_config_value(self, config_manager):
        """Test getting configuration values."""
        assert config_manager.get("app.host") == "0.0.0.0"
        assert config_manager.get("app.port") == 8000
        assert config_manager.get("nonexistent.key", "default") == "default"
    
    def test_set_config_value_fixed_node(self, config_manager):
        """Test setting values in fixed nodes."""
        success, error = config_manager.set("app.port", 9000)
        
        assert success is True
        assert error is None
        assert config_manager.get("app.port") == 9000
    
    def test_set_config_value_cannot_add_key_to_fixed(self, config_manager):
        """Test that adding keys to fixed nodes is blocked."""
        success, error = config_manager.set("app.new_key", "value")
        
        assert success is False
        assert "Cannot add new key" in error
    
    def test_add_virtual_model(self, config_manager):
        """Test adding new virtual model (allowed)."""
        new_model = {
            "proxy_key": "new_key",
            "base_url": "http://new.com",
            "current": "big",
            "use": True,
            "small": {
                "model": "new-small",
                "api_key": "key",
                "base_url": "http://new.com"
            }
        }
        
        success, error = config_manager.add_virtual_model("new_model", new_model)
        
        assert success is True
        assert error is None
        assert config_manager.get_virtual_model("new_model") is not None
    
    def test_delete_virtual_model(self, config_manager):
        """Test deleting virtual model (allowed)."""
        success, error = config_manager.delete_virtual_model("test_model")
        
        assert success is True
        assert error is None
        assert config_manager.get_virtual_model("test_model") is None
    
    def test_cannot_delete_fixed_key(self, config_manager):
        """Test that deleting fixed keys is blocked."""
        success, error = config_manager.delete_key("app", "host")
        
        assert success is False
        assert "Cannot delete key" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 3: Write tests/test_logger.py**

```python
"""
Tests for Dual Logger.
"""

import pytest
import tempfile
from pathlib import Path

from app.models.log import LogEntry, SystemLog, OperationLog, LogLevel


class TestLogModels:
    """Test cases for log models."""
    
    def test_log_entry_creation(self):
        """Test creating a log entry."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            source="test"
        )
        
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.source == "test"
    
    def test_system_log_to_mongodb_doc(self):
        """Test SystemLog to MongoDB document conversion."""
        log = SystemLog(
            level=LogLevel.ERROR,
            message="System error",
            source="test",
            component="test_component",
            event_type="error_event"
        )
        
        doc = log.to_mongodb_doc()
        
        assert doc["level"] == "ERROR"
        assert doc["message"] == "System error"
        assert doc["component"] == "test_component"
        assert doc["event_type"] == "error_event"
    
    def test_operation_log_to_mongodb_doc(self):
        """Test OperationLog to MongoDB document conversion."""
        log = OperationLog(
            level=LogLevel.INFO,
            message="Operation completed",
            source="test",
            operation="test_op",
            user_id="user123",
            status="success",
            duration_ms=100
        )
        
        doc = log.to_mongodb_doc()
        
        assert doc["operation"] == "test_op"
        assert doc["user_id"] == "user123"
        assert doc["status"] == "success"
        assert doc["duration_ms"] == 100
    
    def test_log_to_file_line(self):
        """Test log entry to file line conversion."""
        log = SystemLog(
            level=LogLevel.WARNING,
            message="Warning message",
            source="test",
            trace_id="abc123"
        )
        
        line = log.to_file_line()
        
        assert "WARNING" in line
        assert "Warning message" in line
        assert "[abc123]" in line


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 4: Commit**

```bash
git add app/tests/
git commit -m "test: add unit tests for ConfigManager and Logger"
```

---

## Task 17: Create Example Usage Script

**Files:**
- Create: `app/example_usage.py`

**Step 1: Write example_usage.py**

```python
"""
Example usage of AI Gateway components.

This script demonstrates how to use the ConfigManager,
Logger, and database connections.
"""

import asyncio
from app.core import get_config_manager, get_logger, initialize_logger
from app.db.mongodb import get_mongodb_client
from app.db.redis import get_redis_client
from app.db.qdrant import get_qdrant_client


async def example_config_manager():
    """Example: ConfigManager usage."""
    print("\n=== ConfigManager Example ===")
    
    # Get config manager
    cm = get_config_manager()
    
    # Get values
    print(f"App host: {cm.get('app.host')}")
    print(f"App port: {cm.get('app.port')}")
    
    # Get virtual models
    vmodels = cm.get_virtual_models()
    print(f"Virtual models: {list(vmodels.keys())}")
    
    # Get specific model
    model = cm.get_virtual_model("demo1")
    if model:
        print(f"demo1 current model: {model.get('current')}")
    
    # Try to set value (allowed - changing existing key)
    success, error = cm.set("app.port", 8001)
    print(f"Set app.port: {success}")
    
    # Try to add key to fixed node (blocked)
    success, error = cm.set("app.new_field", "value")
    print(f"Add to fixed node: {success}, Error: {error}")


async def example_logger():
    """Example: Logger usage."""
    print("\n=== Logger Example ===")
    
    # Get logger
    logger = get_logger("example")
    
    # Log messages
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    print("Logged messages to MongoDB and file")


async def example_databases():
    """Example: Database connections."""
    print("\n=== Database Connections Example ===")
    
    # MongoDB
    try:
        mongo = await get_mongodb_client()
        healthy = await mongo.health_check()
        print(f"MongoDB health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    
    # Redis
    try:
        redis = await get_redis_client()
        healthy = await redis.health_check()
        print(f"Redis health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"Redis connection failed: {e}")
    
    # Qdrant
    try:
        qdrant = get_qdrant_client()
        healthy = qdrant.health_check()
        print(f"Qdrant health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"Qdrant connection failed: {e}")


async def main():
    """Main example runner."""
    print("AI Gateway Component Examples")
    print("=" * 50)
    
    try:
        # ConfigManager examples
        await example_config_manager()
        
        # Database examples
        await example_databases()
        
        # Logger examples (after MongoDB is connected)
        mongo = await get_mongodb_client()
        initialize_logger(mongodb_client=mongo)
        await example_logger()
        
    except Exception as e:
        print(f"Example failed: {e}")
    
    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Commit**

```bash
git add app/example_usage.py
git commit -m "docs: add example usage script"
```

---

## Task 18: Create Verification and Testing Guide

**Files:**
- Create: `app/README.md`

**Step 1: Write README.md**

```markdown
# AI Gateway FastAPI Backend

FastAPI backend framework with Template Pattern Configuration Management.

## Features

- **ConfigManager with Template Pattern**: Virtual models allow CRUD, other sections fixed
- **Dual Logging**: MongoDB + file logging with rotation
- **Database Connections**: MongoDB (Motor), Redis, Qdrant
- **Health Checks**: Comprehensive health endpoints
- **Hot Reload**: Configuration auto-reloads on file changes

## Quick Start

### 1. Install Dependencies

```bash
cd app
pip install -r requirements.txt
```

### 2. Ensure Docker Services are Running

```bash
# From project root
docker-compose up -d mongo redis qdrant
```

### 3. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py script
python main.py
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API documentation
curl http://localhost:8000/docs
```

## Project Structure

```
app/
├── main.py                 # FastAPI entry point
├── requirements.txt        # Dependencies
├── Dockerfile             # Container config
├── config.yml             # Configuration file
├── core/                  # Core components
│   ├── config_manager.py  # ConfigManager with Template Pattern
│   ├── config_template.py # Template definitions
│   ├── logger.py          # Dual logging system
│   ├── exceptions.py      # Custom exceptions
│   └── middleware.py      # FastAPI middleware
├── db/                    # Database connections
│   ├── mongodb.py         # MongoDB (Motor)
│   ├── redis.py           # Redis
│   └── qdrant.py          # Qdrant
├── models/                # Pydantic models
│   ├── base.py            # Base models
│   └── log.py             # Log models
├── api/                   # API routes
│   └── v1/
│       └── endpoints/
│           └── health.py  # Health check endpoints
└── utils/                 # Utilities
    └── helpers.py         # Helper functions
```

## Configuration

### Template Pattern Rules

1. **Virtual Models**: Full CRUD allowed
   - Can add new models
   - Can delete existing models
   - Can modify structure

2. **Fixed Nodes**: Values only
   - Cannot add new keys
   - Cannot delete keys
   - Can only change values

### Example Config Operations

```python
from app.core import get_config_manager

cm = get_config_manager()

# Read config
port = cm.get("app.port")

# Modify value (allowed)
cm.set("app.port", 9000)

# Add virtual model (allowed)
cm.add_virtual_model("new_model", {...})

# Delete virtual model (allowed)
cm.delete_virtual_model("old_model")

# Add key to fixed node (BLOCKED)
cm.set("app.new_key", "value")  # Error!
```

## API Endpoints

### Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Overall health status |
| `GET /api/v1/health/ready` | Readiness probe |
| `GET /api/v1/health/live` | Liveness probe |
| `GET /api/v1/health/mongodb` | MongoDB health |
| `GET /api/v1/health/redis` | Redis health |
| `GET /api/v1/health/qdrant` | Qdrant health |

### Configuration

| Endpoint | Description |
|----------|-------------|
| `GET /config` | Get current configuration |

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
cd app
python -m pytest tests/ -v
```

### Manual Testing

```bash
# Start services
docker-compose up -d

# Run example usage
python example_usage.py

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test config hot reload
# 1. Edit config.yml
# 2. Watch logs for reload message
```

## Docker Deployment

### Build Image

```bash
cd app
docker build -t ai-gateway:latest .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config.yml:/app/config.yml \
  -e CONFIG_PATH=/app/config.yml \
  --name ai-gateway \
  ai-gateway:latest
```

## Logging

### MongoDB Collections

- `system_logs`: System events
- `operation_logs`: User operations

### File Output

- `./logs/system/`: System logs
- `./logs/operation/`: Operation logs
- `./logs/error/`: Error logs (all errors)

Log rotation: Daily, 30-day retention

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `config.yml` | Path to config file |
| `PYTHONPATH` | `/app` | Python path |

## License

MIT
```

**Step 2: Commit**

```bash
git add app/README.md
git commit -m "docs: add comprehensive README with usage examples"
```

---

## Task 19: Final Verification

**Step 1: Run syntax checks**

```bash
cd app
python -m py_compile main.py
python -m py_compile core/config_manager.py
python -m py_compile core/logger.py
python -m py_compile db/mongodb.py
```

**Step 2: Run tests**

```bash
cd app
python -m pytest tests/ -v
```

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: final verification and project completion"
```

---

## Summary

This implementation plan creates a complete FastAPI backend framework with:

1. **ConfigManager** - Template Pattern for configuration with hot reload
2. **Dual Logging** - MongoDB + file with rotation
3. **Database Connections** - MongoDB, Redis, Qdrant
4. **Health Endpoints** - Comprehensive health checks
5. **Middleware** - CORS, logging, error handling
6. **Tests** - Unit tests for core components

All files follow Python best practices with type hints, docstrings, and proper error handling.
