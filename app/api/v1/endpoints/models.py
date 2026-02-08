"""
Models API endpoints for listing available virtual models.

This module provides:
- GET /proxy/api/v1/models - List all available virtual models
- GET /proxy/api/v1/models/{model} - Get specific model information

OpenAI-compatible endpoint format.
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from core.config_manager import get_config_manager
from core.logger import get_logger
from models.chat import ModelListResponse, ModelInfo

logger = get_logger("models")

router = APIRouter(prefix="", tags=["models"])


def build_model_info(name: str, config: Dict[str, Any]) -> ModelInfo:
    """
    Build ModelInfo from virtual model configuration.
    
    Args:
        name: The virtual model name
        config: The virtual model configuration
        
    Returns:
        ModelInfo object
    """
    current = config.get("current", "small")
    current_model_config = config.get(current, {})
    current_model = current_model_config.get("model", "unknown")
    
    # Get small and big model names
    small_config = config.get("small", {})
    big_config = config.get("big", {})
    
    small_model = small_config.get("model", "")
    big_model = big_config.get("model", "")
    
    return ModelInfo(
        id=name,
        object="model",
        created=0,
        owned_by="ai-gateway"
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    List all available virtual models.
    
    Returns a list of all configured virtual models that can be used
    for chat completions. Note: The actual model used for generation
    may differ based on the virtual model's current configuration.
    
    Authentication:
    - This endpoint is public (no proxy_key required for listing)
    
    Returns:
        List of available models with their identifiers
    """
    try:
        config_manager = get_config_manager()
        virtual_models = config_manager.get_virtual_models()
        
        models = []
        for name, config in virtual_models.items():
            # Only include enabled models
            if config.get("use", True):
                model_info = build_model_info(name, config)
                models.append(model_info)
        
        return ModelListResponse(
            object="list",
            data=models
        )
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """
    Get information about a specific virtual model.
    
    Args:
        model_id: The virtual model identifier
        
    Returns:
        Detailed information about the specified model
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.get_virtual_model(model_id)
        
        if config is None:
            raise HTTPException(
                status_code=404,
                detail=f"Virtual model '{model_id}' not found"
            )
        
        # Build response
        current = config.get("current", "small")
        current_model_config = config.get(current, {})
        
        small_config = config.get("small", {})
        big_config = config.get("big", {})
        
        return {
            "id": model_id,
            "object": "model",
            "created": 0,
            "owned_by": "ai-gateway",
            "permission": [],
            "root": model_id,
            "config": {
                "enabled": config.get("use", True),
                "current": current,
                "force_current": config.get("force-current", False),
                "small_model": {
                    "id": small_config.get("model", ""),
                    "base_url": small_config.get("base_url", "")
                },
                "big_model": {
                    "id": big_config.get("model", ""),
                    "base_url": big_config.get("base_url", "")
                },
                "knowledge": config.get("knowledge", {}),
                "web_search": config.get("web_search", {})
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model '{model_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")
