"""
Virtual Models API endpoints for full CRUD operations.

This module provides complete CRUD operations for virtual models,
which is the only configuration section that supports full structural modifications.
All other config sections are read-only or value-only modifications.

Endpoints:
- GET /proxy/admin/virtual-models - List all virtual models
- POST /proxy/admin/virtual-models - Create a new virtual model
- GET /proxy/admin/virtual-models/{model_name} - Get a specific virtual model
- PUT /proxy/admin/virtual-models/{model_name} - Update a virtual model
- DELETE /proxy/admin/virtual-models/{model_name} - Delete a virtual model
- POST /proxy/admin/virtual-models/{model_name}/enable - Enable/disable a virtual model
- POST /proxy/admin/virtual-models/{model_name}/switch-model - Switch between small/big models
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, validator
import httpx

from core.config_manager import get_config_manager
from core.exceptions import ConfigValidationError
from models.base import ResponseBase

router = APIRouter(prefix="/virtual-models", tags=["virtual-models"])


# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================

class ModelConfig(BaseModel):
    """Configuration for a specific model (small or big)."""
    model: str = Field(..., description="Model identifier/name")
    api_key: Optional[str] = Field(None, description="API key for the model")
    base_url: str = Field(..., description="Base URL for the model API")
    embedding_model: Optional[str] = Field(None, description="Embedding model name (optional)")


class SkillConfig(BaseModel):
    """Skill configuration."""
    enabled: bool = True
    version: str = "v1"


class CustomSkillConfig(BaseModel):
    """Custom skill configuration."""
    enabled: bool = False
    version: str = "v2"


class VirtualModelSkillConfig(BaseModel):
    """Complete skill configuration for a virtual model."""
    enabled: bool = True
    version: str = "v1"
    custom: CustomSkillConfig = Field(default_factory=CustomSkillConfig)


class KnowledgeConfig(BaseModel):
    """Knowledge base configuration for a virtual model."""
    enabled: bool = True
    shared: bool = True
    skill: VirtualModelSkillConfig = Field(default_factory=VirtualModelSkillConfig)


class WebSearchTarget(BaseModel):
    """Web search target configuration."""
    pass  # Can be a string or a dict with searxng key


class WebSearchConfig(BaseModel):
    """Web search configuration for a virtual model."""
    enabled: bool = True
    skill: VirtualModelSkillConfig = Field(default_factory=VirtualModelSkillConfig)
    target: List[Any] = Field(default_factory=list)


class VirtualModelCreate(BaseModel):
    """Request model for creating a virtual model."""
    proxy_key: str = Field(..., description="Virtual model API key for clients")
    base_url: str = Field(..., description="Base URL for client calls")
    current: str = Field(default="small", description="Current model: 'small' or 'big'")
    force_current: bool = Field(default=False, description="Force use of current model")
    use: bool = Field(default=True, description="Enable this virtual model")
    small: ModelConfig = Field(..., description="Small model configuration")
    big: ModelConfig = Field(..., description="Big model configuration")
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)

    @validator('current')
    def validate_current(cls, v):
        if v not in ['small', 'big']:
            raise ValueError('current must be either "small" or "big"')
        return v


class VirtualModelUpdate(BaseModel):
    """Request model for updating a virtual model."""
    proxy_key: Optional[str] = None
    base_url: Optional[str] = None
    current: Optional[str] = None
    force_current: Optional[bool] = None
    use: Optional[bool] = None
    small: Optional[ModelConfig] = None
    big: Optional[ModelConfig] = None
    knowledge: Optional[KnowledgeConfig] = None
    web_search: Optional[WebSearchConfig] = None

    @validator('current')
    def validate_current(cls, v):
        if v is not None and v not in ['small', 'big']:
            raise ValueError('current must be either "small" or "big"')
        return v


class VirtualModelCreateRequest(BaseModel):
    """Combined request model for creating a virtual model."""
    model_name: str = Field(..., description="Unique name for the virtual model")
    config: VirtualModelCreate = Field(..., description="Virtual model configuration")


class VirtualModelResponse(BaseModel):
    """Response model for a virtual model."""
    name: str
    config: Dict[str, Any]
    enabled: bool
    current_model: str


class VirtualModelListResponse(ResponseBase):
    """Response for listing virtual models."""
    data: Dict[str, Any]


class VirtualModelDetailResponse(ResponseBase):
    """Response for a single virtual model."""
    data: Dict[str, Any]


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("", response_model=VirtualModelListResponse)
async def list_virtual_models():
    """
    List all virtual models with summary information.
    
    Returns a list of all virtual models with their basic status.
    """
    try:
        config_manager = get_config_manager()
        models = config_manager.get_virtual_models()
        
        # Build summary for each model
        model_list = []
        for name, config in models.items():
            model_list.append({
                "name": name,
                "enabled": config.get("use", True),
                "current": config.get("current", "small"),
                "force_current": config.get("force-current", False),
                "base_url": config.get("base_url", ""),
                "small_model": config.get("small", {}).get("model", ""),
                "big_model": config.get("big", {}).get("model", ""),
                "knowledge_enabled": config.get("knowledge", {}).get("enabled", False),
                "web_search_enabled": config.get("web_search", {}).get("enabled", False)
            })
        
        return VirtualModelListResponse(
            success=True,
            message=f"Retrieved {len(model_list)} virtual models",
            data={
                "models": model_list,
                "total": len(model_list),
                "enabled": sum(1 for m in model_list if m["enabled"])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list virtual models: {str(e)}")


@router.post("", response_model=VirtualModelDetailResponse)
async def create_virtual_model(request: VirtualModelCreateRequest):
    """
    Create a new virtual model.
    
    The virtual model name must be unique. This endpoint validates the configuration
    and saves it to config.yml under ai-gateway.virtual_models.{model_name}
    """
    try:
        config_manager = get_config_manager()
        
        # Check if model already exists
        existing = config_manager.get(f"ai-gateway.virtual_models.{request.model_name}")
        if existing is not None:
            raise HTTPException(
                status_code=400, 
                detail=f"Virtual model '{request.model_name}' already exists"
            )
        
        # Convert pydantic model to dict
        config_dict = request.config.model_dump()
        
        # Use add_key method which respects template rules
        success, error = config_manager.add_key(
            path="ai-gateway.virtual_models",
            key=request.model_name,
            value=config_dict
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create virtual model '{request.model_name}'. Check template constraints."
            )
        
        # Reload and return the created model
        config_manager.reload()
        created_config = config_manager.get(f"ai-gateway.virtual_models.{request.model_name}")
        
        return VirtualModelDetailResponse(
            success=True,
            message=f"Virtual model '{request.model_name}' created successfully",
            data={
                "name": request.model_name,
                "config": created_config
            }
        )
        
    except HTTPException:
        raise
    except ConfigValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create virtual model: {str(e)}")


@router.get("/{model_name}", response_model=VirtualModelDetailResponse)
async def get_virtual_model(model_name: str):
    """
    Get detailed configuration of a specific virtual model.
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        
        if config is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        return VirtualModelDetailResponse(
            success=True,
            message=f"Virtual model '{model_name}' retrieved",
            data={
                "name": model_name,
                "config": config
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get virtual model: {str(e)}")


@router.put("/{model_name}", response_model=VirtualModelDetailResponse)
async def update_virtual_model(
    model_name: str,
    update_data: VirtualModelUpdate
):
    """
    Update an existing virtual model.
    
    Only provided fields will be updated. Unchanged fields retain their current values.
    """
    try:
        config_manager = get_config_manager()
        
        # Check if model exists
        existing = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        # Filter out None values
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Merge with existing config
        merged_config = {**existing, **update_dict}
        
        # Update the config using set method
        success, error = config_manager.set(
            key=f"ai-gateway.virtual_models.{model_name}",
            value=merged_config,
            validate=True
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update virtual model '{model_name}'"
            )
        
        # Reload and return updated config
        config_manager.reload()
        updated_config = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        
        return VirtualModelDetailResponse(
            success=True,
            message=f"Virtual model '{model_name}' updated successfully",
            data={
                "name": model_name,
                "config": updated_config
            }
        )
        
    except HTTPException:
        raise
    except ConfigValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update virtual model: {str(e)}")


@router.delete("/{model_name}", response_model=ResponseBase)
async def delete_virtual_model(model_name: str):
    """
    Delete a virtual model.
    
    This permanently removes the virtual model from config.yml.
    """
    try:
        config_manager = get_config_manager()
        
        # Check if model exists
        existing = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        # Delete the model using delete_key
        success, error = config_manager.delete_key(
            path="ai-gateway.virtual_models",
            key=model_name
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete virtual model '{model_name}'"
            )
        
        return ResponseBase(
            success=True,
            message=f"Virtual model '{model_name}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete virtual model: {str(e)}")


@router.post("/{model_name}/enable", response_model=ResponseBase)
async def toggle_virtual_model(
    model_name: str,
    enabled: bool = Body(..., embed=True)
):
    """
    Enable or disable a virtual model.
    
    Disabled models cannot be used for chat routing.
    """
    try:
        config_manager = get_config_manager()
        
        # Check if model exists
        existing = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        # Update the use field
        existing["use"] = enabled
        
        success, error = config_manager.set(
            key=f"ai-gateway.virtual_models.{model_name}",
            value=existing,
            validate=True
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update virtual model '{model_name}'"
            )
        
        return ResponseBase(
            success=True,
            message=f"Virtual model '{model_name}' {'enabled' if enabled else 'disabled'}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle virtual model: {str(e)}")


@router.post("/{model_name}/switch-model", response_model=ResponseBase)
async def switch_current_model(
    model_name: str,
    target: str = Body(..., embed=True, description="Target model: 'small' or 'big'")
):
    """
    Switch the current model for a virtual model.
    
    Changes which model (small or big) is currently active.
    """
    if target not in ["small", "big"]:
        raise HTTPException(status_code=400, detail="Target must be 'small' or 'big'")
    
    try:
        config_manager = get_config_manager()
        
        # Check if model exists
        existing = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        # Update the current field
        existing["current"] = target
        
        success, error = config_manager.set(
            key=f"ai-gateway.virtual_models.{model_name}",
            value=existing,
            validate=True
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to switch model for '{model_name}'"
            )
        
        return ResponseBase(
            success=True,
            message=f"Virtual model '{model_name}' switched to {target} model"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")


@router.get("/{model_name}/stats", response_model=ResponseBase)
async def get_virtual_model_stats(model_name: str):
    """
    Get usage statistics for a virtual model.
    
    Returns aggregated metrics from logs (total requests, errors, etc.)
    """
    try:
        config_manager = get_config_manager()
        
        # Check if model exists
        config = config_manager.get(f"ai-gateway.virtual_models.{model_name}")
        if config is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_name}' not found"
            )
        
        # Get stats from MongoDB logs
        from db.mongodb import get_database
        db = get_database()
        
        # Count total requests in last 24 hours
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=24)
        
        total_requests = await db.logs.count_documents({
            "virtual_model": model_name,
            "created_at": {"$gte": since}
        })
        
        error_count = await db.logs.count_documents({
            "virtual_model": model_name,
            "level": "ERROR",
            "created_at": {"$gte": since}
        })
        
        return ResponseBase(
            success=True,
            message=f"Statistics for virtual model '{model_name}'",
            data={
                "model_name": model_name,
                "last_24h": {
                    "total_requests": total_requests,
                    "errors": error_count,
                    "success_rate": round((total_requests - error_count) / total_requests * 100, 2) if total_requests > 0 else 100
                },
                "config": {
                    "enabled": config.get("use", True),
                    "current": config.get("current", "small"),
                    "knowledge": config.get("knowledge", {}).get("enabled", False),
                    "web_search": config.get("web_search", {}).get("enabled", False)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model stats: {str(e)}")


class TestConnectionRequest(BaseModel):
    """Request model for testing model connection."""
    model: str = Field(..., description="Model name/identifier")
    base_url: str = Field(..., description="Base URL for the model API")
    api_key: Optional[str] = Field(None, description="API key (optional)")


class TestConnectionResponse(ResponseBase):
    """Response for connection test."""
    success: bool = True
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_model_connection(request: TestConnectionRequest):
    """
    Test connection to an upstream model API.

    Sends a simple request to verify connectivity and authentication.
    """
    try:
        # Build the completions URL
        base_url = request.base_url.rstrip('/')
        url = f"{base_url}/chat/completions"

        headers = {}
        if request.api_key:
            headers["Authorization"] = f"Bearer {request.api_key}"

        # Simple test payload
        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return TestConnectionResponse(
                success=True,
                message="Connection successful",
                data={
                    "status_code": response.status_code,
                    "connected": True,
                    "model": result.get("model", request.model)
                }
            )
        elif response.status_code == 401:
            return TestConnectionResponse(
                success=False,
                message="Authentication failed - invalid API key",
                data={
                    "status_code": response.status_code,
                    "connected": False,
                    "error": "Unauthorized"
                }
            )
        elif response.status_code == 404:
            return TestConnectionResponse(
                success=False,
                message="Model not found - check model name",
                data={
                    "status_code": response.status_code,
                    "connected": False,
                    "error": "Not Found"
                }
            )
        else:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", response.text)
            except:
                error_detail = response.text

            return TestConnectionResponse(
                success=False,
                message=f"Connection failed: {response.status_code}",
                data={
                    "status_code": response.status_code,
                    "connected": False,
                    "error": error_detail
                }
            )

    except httpx.TimeoutException:
        return TestConnectionResponse(
            success=False,
            message="Connection timed out - check base URL",
            data={
                "connected": False,
                "error": "Timeout"
            }
        )
    except httpx.ConnectError as e:
        return TestConnectionResponse(
            success=False,
            message=f"Connection failed - {str(e)}",
            data={
                "connected": False,
                "error": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
