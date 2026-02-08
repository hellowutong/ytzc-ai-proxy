"""
Pydantic models for Chat API.

Provides request and response models for OpenAI-compatible chat completions API.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from models.base import BaseModel as AppBaseModel


# =============================================================================
# Request Models
# =============================================================================

class ChatMessage(AppBaseModel):
    """A chat message in the conversation."""
    
    role: Literal["system", "user", "assistant", "function"] = Field(
        ..., description="The role of the message sender"
    )
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(None, description="The name of the sender")


class ChatFunctionCall(AppBaseModel):
    """A function call in a chat message."""
    
    name: str = Field(..., description="The name of the function to call")
    arguments: str = Field(..., description="The arguments to pass to the function")


class ChatFunctionDefinition(AppBaseModel):
    """Definition of a callable function."""
    
    name: str = Field(..., description="The name of the function")
    description: Optional[str] = Field(None, description="A description of what the function does")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="The parameters the function accepts (JSON Schema)"
    )


class ChatCompletionRequest(AppBaseModel):
    """Request model for chat completions."""
    
    model: str = Field(..., description="The virtual model ID to use")
    messages: List[ChatMessage] = Field(..., description="The messages to process")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0, description="Temperature for sampling")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    n: Optional[int] = Field(1, ge=1, le=10, description="Number of completions to generate")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: Optional[Dict[str, int]] = Field(None, description="Logit bias for specific tokens")
    user: Optional[str] = Field(None, description="User identifier for tracking")
    functions: Optional[List[ChatFunctionDefinition]] = Field(
        None, description="Available functions for the model to call"
    )
    function_call: Optional[Literal["none", "auto"]] = Field(
        None, description="How to handle function calls"
    )


# =============================================================================
# Response Models
# =============================================================================

class ChatCompletionChoice(AppBaseModel):
    """A single completion choice in the response."""
    
    index: int = Field(..., description="The index of the choice")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Optional[Literal["stop", "length", "function_call", "content_filter"]] = Field(
        None, description="Why the completion stopped"
    )
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities if requested")


class ChatCompletionUsage(AppBaseModel):
    """Token usage statistics for a completion."""
    
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens")


class ChatCompletionResponse(AppBaseModel):
    """Response model for non-streaming chat completions."""
    
    id: str = Field(..., description="Unique identifier for the completion")
    object: Literal["chat.completion"] = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="The actual model used")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: ChatCompletionUsage = Field(..., description="Token usage statistics")
    system_fingerprint: Optional[str] = Field(
        None, description="Fingerprint of the model configuration"
    )


# =============================================================================
# Streaming Response Models
# =============================================================================

class ChoiceDelta(AppBaseModel):
    """Delta content for streaming responses."""
    
    role: Optional[str] = Field(None, description="Role (for first chunk only)")
    content: Optional[str] = Field(None, description="Content delta")
    function_call: Optional[ChatFunctionCall] = Field(
        None, description="Function call information"
    )


class StreamingChoice(AppBaseModel):
    """A single choice in a streaming response."""
    
    index: int = Field(..., description="The index of the choice")
    delta: ChoiceDelta = Field(..., description="The delta content")
    finish_reason: Optional[Literal["stop", "length", "function_call", "content_filter"]] = Field(
        None, description="Why the completion stopped"
    )
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities if requested")


class ChatCompletionChunk(AppBaseModel):
    """Response chunk for streaming chat completions."""
    
    id: str = Field(..., description="Unique identifier for the completion")
    object: Literal["chat.completion.chunk"] = Field(
        "chat.completion.chunk", description="Object type"
    )
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="The actual model used")
    choices: List[StreamingChoice] = Field(..., description="List of choice deltas")


# =============================================================================
# Models API Models
# =============================================================================

class ModelInfo(AppBaseModel):
    """Information about an available model."""
    
    id: str = Field(..., description="The model identifier")
    object: Literal["model"] = Field("model", description="Object type")
    created: int = Field(0, description="Creation timestamp (always 0 for virtual models)")
    owned_by: str = Field("ai-gateway", description="Who owns the model")


class ModelListResponse(AppBaseModel):
    """Response for listing available models."""
    
    object: Literal["list"] = Field("list", description="Object type")
    data: List[ModelInfo] = Field(..., description="List of available models")


# =============================================================================
# Error Response Models
# =============================================================================

class ErrorDetail(AppBaseModel):
    """Details about an error."""
    
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    param: Optional[str] = Field(None, description="Parameter that caused the error")
    code: Optional[str] = Field(None, description="Error code")


class ChatErrorResponse(AppBaseModel):
    """Error response for chat API."""
    
    object: Literal["error"] = Field("error", description="Object type")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    param: Optional[str] = Field(None, description="Parameter that caused the error")
    code: Optional[str] = Field(None, description="Error code")
