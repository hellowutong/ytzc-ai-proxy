"""
Log models for dual logging system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import Field
from models.base import BaseModel


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
