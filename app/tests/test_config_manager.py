"""
Tests for ConfigManager with Template Pattern.
"""

import pytest
import tempfile
import os
from pathlib import Path

from core.config_manager import ConfigManager, get_config_manager
from core.exceptions import ConfigValidationError, ConfigTemplateError


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
