"""
Tests for Dual Logger.
"""

import pytest
import tempfile
from pathlib import Path

from models.log import LogEntry, SystemLog, OperationLog, LogLevel


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
