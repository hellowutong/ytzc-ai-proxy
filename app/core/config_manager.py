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

from core.config_template import (
    ConfigTemplate,
    FixedNodeTemplate,
    VirtualModelsTemplate,
    template_registry,
)
from core.exceptions import ConfigValidationError, ConfigTemplateError
from core.logger import get_logger

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
