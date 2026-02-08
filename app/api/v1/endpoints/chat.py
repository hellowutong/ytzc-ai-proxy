"""
Chat API endpoints for OpenAI-compatible chat completions.

This module provides:
- POST /proxy/api/v1/chat/completions - Main chat completion endpoint
- GET /proxy/api/v1/models - List available virtual models
- GET /proxy/api/v1/models/{model} - Get specific model info

Routes requests to appropriate upstream AI models based on virtual model configuration.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse

from core.config_manager import get_config_manager
from core.logger import get_logger
from models.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatMessage,
    ChatCompletionUsage,
    ChatCompletionChoice,
    StreamingChoice,
    ChoiceDelta,
    ModelListResponse,
    ModelInfo,
    ChatErrorResponse,
)

logger = get_logger("chat")

router = APIRouter(prefix="/chat", tags=["chat"])


def find_virtual_model_by_proxy_key(proxy_key: str) -> Optional[Dict[str, Any]]:
    """
    Find a virtual model configuration by its proxy_key.
    
    Args:
        proxy_key: The proxy key to search for
        
    Returns:
        Tuple of (model_name, config) or None if not found
    """
    config_manager = get_config_manager()
    virtual_models = config_manager.get_virtual_models()
    
    for name, config in virtual_models.items():
        if config.get("proxy_key") == proxy_key:
            return name, config
    
    return None


def get_target_model_config(virtual_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the target model configuration based on virtual model settings.
    
    Args:
        virtual_config: The virtual model configuration
        
    Returns:
        The actual model configuration (small or big based on current setting)
    """
    current = virtual_config.get("current", "small")
    target_config = virtual_config.get(current, {})
    
    if not target_config:
        # Fallback to small if current is not available
        target_config = virtual_config.get("small", {})
    
    return target_config


def build_upstream_request(
    request: ChatCompletionRequest,
    target_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build the upstream API request payload.
    
    Args:
        request: The original chat completion request
        target_config: The target model configuration
        
    Returns:
        Request payload for upstream API
    """
    # Build messages list
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Build request payload
    payload: Dict[str, Any] = {
        "model": target_config.get("model"),
        "messages": messages,
    }
    
    # Add optional parameters if provided
    if request.stream is not None:
        payload["stream"] = request.stream
    
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    
    if request.n is not None and request.n != 1:
        payload["n"] = request.n
    
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens
    
    if request.presence_penalty is not None:
        payload["presence_penalty"] = request.presence_penalty
    
    if request.frequency_penalty is not None:
        payload["frequency_penalty"] = request.frequency_penalty
    
    if request.logit_bias is not None:
        payload["logit_bias"] = request.logit_bias
    
    if request.user is not None:
        payload["user"] = request.user
    
    return payload


async def forward_to_upstream(
    request: ChatCompletionRequest,
    virtual_model_name: str,
    virtual_config: Dict[str, Any],
    target_config: Dict[str, Any],
    proxy_key: str
) -> Dict[str, Any]:
    """
    Forward request to upstream API and get response.
    
    Args:
        request: The chat completion request
        virtual_model_name: The virtual model name
        virtual_config: The virtual model configuration
        target_config: The target model configuration
        proxy_key: The proxy key for authentication
        
    Returns:
        The upstream API response as a dictionary
    """
    upstream_base_url = target_config.get("base_url")
    upstream_api_key = target_config.get("api_key")
    
    if not upstream_base_url:
        raise HTTPException(
            status_code=500,
            detail=f"Upstream base_url not configured for virtual model '{virtual_model_name}'"
        )
    
    # Build upstream request payload
    payload = build_upstream_request(request, target_config)
    
    # Build headers
    headers = {
        "Content-Type": "application/json",
    }
    
    if upstream_api_key:
        headers["Authorization"] = f"Bearer {upstream_api_key}"
    
    # Log the request
    logger.info(
        f"Forwarding chat request to {virtual_model_name}/{target_config.get('model')} "
        f"(upstream: {upstream_base_url})"
    )
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{upstream_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"Upstream API returned status {response.status_code}: {error_detail}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upstream API error: {error_detail}"
                )
            
            return response.json()
    
    except httpx.TimeoutException:
        logger.error(f"Timeout when calling upstream API for '{virtual_model_name}'")
        raise HTTPException(status_code=504, detail="Upstream API timeout")
    
    except httpx.ConnectError as e:
        logger.error(f"Connection error when calling upstream API for '{virtual_model_name}': {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to upstream API: {str(e)}"
        )


async def stream_from_upstream(
    request: ChatCompletionRequest,
    virtual_model_name: str,
    virtual_config: Dict[str, Any],
    target_config: Dict[str, Any],
    proxy_key: str
):
    """
    Stream response from upstream API and yield SSE chunks.
    
    Args:
        request: The chat completion request
        virtual_model_name: The virtual model name
        virtual_config: The virtual model configuration
        target_config: The target model configuration
        proxy_key: The proxy key for authentication
    """
    upstream_base_url = target_config.get("base_url")
    upstream_api_key = target_config.get("api_key")
    
    if not upstream_base_url:
        raise HTTPException(
            status_code=500,
            detail=f"Upstream base_url not configured for virtual model '{virtual_model_name}'"
        )
    
    # Build upstream request payload
    payload = build_upstream_request(request, target_config)
    
    # Build headers
    headers = {
        "Content-Type": "application/json",
    }
    
    if upstream_api_key:
        headers["Authorization"] = f"Bearer {upstream_api_key}"
    
    logger.info(
        f"Streaming chat request to {virtual_model_name}/{target_config.get('model')} "
        f"(upstream: {upstream_base_url})"
    )
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{upstream_base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                
                if response.status_code != 200:
                    error_detail = await response.aread()
                    logger.error(
                        f"Upstream API returned status {response.status_code}: {error_detail}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Upstream API error: {error_detail.decode()}"
                    )
                
                # Stream the response
                async for chunk in response.aiter_bytes():
                    if chunk:
                        # Forward the chunk directly, but we need to parse it to transform model name
                        try:
                            chunk_text = chunk.decode("utf-8")
                            # Parse and reconstruct with virtual model name
                            if chunk_text.startswith("data: "):
                                data_content = chunk_text[6:].strip()
                                if data_content == "[DONE]":
                                    yield f"data: [DONE]\n\n"
                                else:
                                    data = json.loads(data_content)
                                    # Transform model name to virtual model name
                                    if "model" in data:
                                        original_model = data["model"]
                                        data["model"] = virtual_model_name
                                        yield f"data: {json.dumps(data)}\n\n"
                                    else:
                                        yield chunk_text
                            else:
                                yield chunk.decode("utf-8")
                        except json.JSONDecodeError:
                            # Forward raw chunk if parsing fails
                            yield chunk.decode("utf-8")
    
    except httpx.TimeoutException:
        logger.error(f"Timeout when streaming from upstream API for '{virtual_model_name}'")
        yield f'data: {{"error": "Upstream API timeout"}}\n\n'
    
    except httpx.ConnectError as e:
        logger.error(f"Connection error when streaming from upstream API for '{virtual_model_name}': {e}")
        yield f'data: {{"error": "Unable to connect to upstream API"}}\n\n'


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Create a chat completion.
    
    This endpoint accepts OpenAI-compatible chat completion requests and routes them
    to the appropriate upstream AI model based on the virtual model configuration.
    
    Authentication:
    - Bearer token should be the proxy_key from the virtual model configuration
    
    Args:
        request: The chat completion request
        authorization: Authorization header (Bearer proxy_key)
        
    Returns:
        Chat completion response (streaming or non-streaming)
    """
    # Extract proxy key from authorization header
    proxy_key = None
    if authorization and authorization.startswith("Bearer "):
        proxy_key = authorization[7:]
    elif authorization:
        proxy_key = authorization
    
    if not proxy_key:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header. Provide 'Authorization: Bearer <proxy_key>'"
        )
    
    # Find the virtual model by proxy_key
    result = find_virtual_model_by_proxy_key(proxy_key)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid proxy_key. No virtual model found with this key."
        )
    
    virtual_model_name, virtual_config = result
    
    # Check if virtual model is enabled
    if not virtual_config.get("use", True):
        raise HTTPException(
            status_code=403,
            detail=f"Virtual model '{virtual_model_name}' is disabled."
        )
    
    # Get target model configuration
    target_config = get_target_model_config(virtual_config)
    
    if not target_config:
        raise HTTPException(
            status_code=500,
            detail=f"No model configuration found for virtual model '{virtual_model_name}'"
        )
    
    actual_model_name = target_config.get("model", virtual_model_name)
    
    # Handle streaming
    if request.stream:
        return StreamingResponse(
            stream_from_upstream(
                request=request,
                virtual_model_name=virtual_model_name,
                virtual_config=virtual_config,
                target_config=target_config,
                proxy_key=proxy_key
            ),
            media_type="text/event-stream"
        )
    
    # Non-streaming request
    try:
        upstream_response = await forward_to_upstream(
            request=request,
            virtual_model_name=virtual_model_name,
            virtual_config=virtual_config,
            target_config=target_config,
            proxy_key=proxy_key
        )
        
        # Transform the response to use virtual model name
        response_id = upstream_response.get("id", f"chatcmpl-{uuid.uuid4().hex[:8]}")
        created = upstream_response.get("created", int(__import__("time").time()))
        
        # Build the response
        choices = []
        for choice in upstream_response.get("choices", []):
            message = choice.get("message", {})
            choices.append({
                "index": choice.get("index", 0),
                "message": {
                    "role": message.get("role", "assistant"),
                    "content": message.get("content", "")
                },
                "finish_reason": choice.get("finish_reason", "stop"),
                "logprobs": choice.get("logprobs")
            })
        
        usage = upstream_response.get("usage", {})
        if usage:
            chat_usage = ChatCompletionUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0)
            )
        else:
            # Fallback if usage not provided
            chat_usage = ChatCompletionUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
        
        return ChatCompletionResponse(
            id=response_id,
            object="chat.completion",
            created=created,
            model=virtual_model_name,  # Return virtual model name, not actual
            choices=[
                ChatCompletionChoice(
                    index=c["index"],
                    message=ChatMessage(
                        role=c["message"]["role"],
                        content=c["message"]["content"]
                    ),
                    finish_reason=c.get("finish_reason"),
                    logprobs=c.get("logprobs")
                )
                for c in choices
            ],
            usage=chat_usage,
            system_fingerprint=upstream_response.get("system_fingerprint")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat completion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/completions")
async def get_completion_info():
    """
    Get information about the chat completions endpoint.
    
    Returns endpoint information and available options.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "chat/completions",
                "object": "endpoint",
                "created": int(__import__("time").time()),
                "method": "POST",
                "url": "/proxy/api/v1/chat/completions",
                "streaming": True,
                "authentication": "Bearer proxy_key"
            }
        ]
    }
