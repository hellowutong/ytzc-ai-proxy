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


class TimestampMixin:
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
