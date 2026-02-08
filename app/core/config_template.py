"""
Configuration Template Pattern implementation.

This module defines the Template Pattern for configuration management:
- ConfigTemplate: Abstract base class defining the template interface
- VirtualModelsTemplate: Allows add/delete/modify operations
- FixedNodeTemplate: Only value changes allowed (keys fixed)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple
from core.exceptions import ConfigTemplateError, ConfigValidationError


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
    
    def __init__(self, path: str, allowed_keys: Optional[Set[str]] = None, 
                 value_validators: Optional[Dict[str, callable]] = None):
        """
        Initialize fixed node template.
        
        Args:
            path: Dot-notation path to this config section
            allowed_keys: Set of allowed keys (structure is fixed), None allows any keys
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
        if self.allowed_keys is not None and key not in self.allowed_keys:
            return False, f"Key '{key}' is not allowed in {self.path}. " \
                         f"Allowed keys: {self.allowed_keys}"
        
        if key in self.value_validators:
            return self.value_validators[key](value)
        
        return True, None


class FlexibleNodeTemplate(ConfigTemplate):
    """
    Template for flexible configuration nodes.
    
    Allows any structure within this section.
    Used for complex nested configurations like knowledge, rss, media.
    Only enforces that values cannot add/remove keys at this level.
    """
    
    def __init__(self, path: str, allowed_keys: Optional[Set[str]] = None):
        """
        Initialize flexible node template.
        
        Args:
            path: Dot-notation path to this config section
            allowed_keys: Set of allowed keys, None allows any keys
        """
        super().__init__(path, allowed_keys)
    
    def can_add_key(self, key: str) -> bool:
        """Cannot add keys at this level."""
        return False
    
    def can_delete_key(self, key: str) -> bool:
        """Cannot delete keys at this level."""
        return False
    
    def can_modify_structure(self) -> bool:
        """Structure can be modified within nested sections."""
        return True
    
    def validate_structure(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Flexible nodes allow any structure."""
        return True, None


class RootTemplate(ConfigTemplate):
    """
    Template for root configuration level.
    
    Defines which top-level sections exist and their constraints.
    """
    
    # Define fixed top-level keys - includes web_search with nested services
    TOP_LEVEL_KEYS = {
        "app", "storage", "web_search", "ai-gateway", "knowledge", "rss", "media", "text", "log"
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
            allowed_keys={"host", "port", "password"}
        ))
        
        # Web search configuration
        self.register(FixedNodeTemplate(
            path="web_search",
            allowed_keys={"searxng", "LibreX", "4get"}
        ))
        
        # AI Gateway configuration - contains all feature modules
        self.register(FlexibleNodeTemplate(
            path="ai-gateway",
            allowed_keys=None
        ))
        
        self.register(FixedNodeTemplate(
            path="ai-gateway.router",
            allowed_keys={"skill", "keywords", "force", "enable-force"}
        ))
        
        self.register(FixedNodeTemplate(
            path="ai-gateway.router.skill",
            allowed_keys={"enabled", "version", "custom"}
        ))
        
        self.register(FixedNodeTemplate(
            path="ai-gateway.router.skill.custom",
            allowed_keys={"enabled", "version"}
        ))
        
        self.register(FixedNodeTemplate(
            path="ai-gateway.router.keywords",
            allowed_keys={"enable", "rules"}
        ))
        
        # Knowledge configuration (can be at root or ai-gateway level)
        # Allow flexible structure for complex nested config
        self.register(FlexibleNodeTemplate(
            path="knowledge",
            allowed_keys=None  # Allow any keys
        ))
        
        self.register(FlexibleNodeTemplate(
            path="ai-gateway.knowledge",
            allowed_keys=None  # Allow any keys
        ))
        
        # RSS configuration (can be at root or ai-gateway level)
        self.register(FlexibleNodeTemplate(
            path="ai-gateway.rss",
            allowed_keys=None
        ))
        
        # Media configuration (can be at root or ai-gateway level)
        self.register(FlexibleNodeTemplate(
            path="ai-gateway.media",
            allowed_keys=None
        ))
        
        # Text configuration (can be at root or ai-gateway level)
        self.register(FlexibleNodeTemplate(
            path="ai-gateway.text",
            allowed_keys=None
        ))
        
        self.register(FixedNodeTemplate(
            path="knowledge.threshold",
            allowed_keys={"extraction", "retrieval"}
        ))
        
        # RSS configuration
        self.register(FixedNodeTemplate(
            path="rss",
            allowed_keys={"max_concurrent", "auto_fetch", "fetch_interval", "retention_days", "skill", "projects"}
        ))
        
        # Media configuration
        self.register(FixedNodeTemplate(
            path="media",
            allowed_keys={"video", "audio"}
        ))
        
        # Text configuration
        self.register(FixedNodeTemplate(
            path="text",
            allowed_keys={"skill", "upload", "download"}
        ))
        
        # Log configuration
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
