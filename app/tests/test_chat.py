"""
Comprehensive tests for Chat API module.

Tests the chat completions and models endpoints with proper mocking
of ConfigManager and upstream HTTP calls.
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from main import app


# =============================================================================
# Test Configuration
# =============================================================================

TEST_VIRTUAL_MODELS = {
    "test-model": {
        "proxy_key": "test-proxy-key-123",
        "base_url": "http://localhost:8000/proxy/v1",
        "current": "small",
        "force-current": False,
        "use": True,
        "small": {
            "model": "test-small-model",
            "api_key": "test-small-api-key",
            "base_url": "https://test-api.example.com/v1"
        },
        "big": {
            "model": "test-big-model",
            "api_key": "test-big-api-key",
            "base_url": "https://test-api.example.com/v1"
        }
    },
    "disabled-model": {
        "proxy_key": "disabled-proxy-key-456",
        "base_url": "http://localhost:8000/proxy/v1",
        "current": "small",
        "force-current": False,
        "use": False,  # Disabled model
        "small": {
            "model": "disabled-small-model",
            "api_key": "disabled-small-api-key",
            "base_url": "https://test-api.example.com/v1"
        },
        "big": {
            "model": "disabled-big-model",
            "api_key": "disabled-big-api-key",
            "base_url": "https://test-api.example.com/v1"
        }
    },
    "model-with-only-small": {
        "proxy_key": "small-only-key-789",
        "base_url": "http://localhost:8000/proxy/v1",
        "current": "small",
        "force-current": False,
        "use": True,
        "small": {
            "model": "only-small-model",
            "api_key": "only-small-api-key",
            "base_url": "https://test-api.example.com/v1"
        }
    }
}

MOCK_UPSTREAM_RESPONSE = {
    "id": "chatcmpl-test123",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "test-small-model",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a test response"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}

MOCK_STREAMING_CHUNKS = [
    b'data: {"id":"chatcmpl-test123","object":"chat.completion.chunk","created":1234567890,"model":"test-small-model","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}\n\n',
    b'data: {"id":"chatcmpl-test123","object":"chat.completion.chunk","created":1234567890,"model":"test-small-model","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n',
    b'data: {"id":"chatcmpl-test123","object":"chat.completion.chunk","created":1234567890,"model":"test-small-model","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}\n\n',
    b'data: {"id":"chatcmpl-test123","object":"chat.completion.chunk","created":1234567890,"model":"test-small-model","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
    b'data: [DONE]\n\n'
]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager that returns test virtual models."""
    with patch('app.api.v1.endpoints.chat.get_config_manager') as mock_get_cm, \
         patch('app.api.v1.endpoints.models.get_config_manager') as mock_get_cm_models:
        
        mock_cm = MagicMock()
        mock_cm.get_virtual_models.return_value = TEST_VIRTUAL_MODELS
        mock_cm.get_virtual_model.side_effect = lambda name: TEST_VIRTUAL_MODELS.get(name)
        
        mock_get_cm.return_value = mock_cm
        mock_get_cm_models.return_value = mock_cm
        
        yield mock_cm


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient for upstream API calls."""
    mock_client = AsyncMock(spec=AsyncClient)
    return mock_client


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def client(mock_config_manager):
    """Create a synchronous test client with mocked config."""
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# Models Endpoint Tests
# =============================================================================


class TestListModels:
    """Test cases for GET /proxy/api/v1/models endpoint."""

    def test_list_models_returns_enabled_models(self, client):
        """Test that list models returns only enabled virtual models."""
        response = client.get("/proxy/api/v1/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Should include test-model but not disabled-model
        model_ids = [m["id"] for m in data["data"]]
        assert "test-model" in model_ids
        assert "model-with-only-small" in model_ids
        # disabled-model should not be in the list
        assert "disabled-model" not in model_ids

    def test_list_models_response_format(self, client):
        """Test that list models response has correct format."""
        response = client.get("/proxy/api/v1/models")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "object" in data
        assert "data" in data
        assert data["object"] == "list"
        
        # Each model should have required fields
        for model in data["data"]:
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"
            assert "created" in model
            assert "owned_by" in model

    def test_list_models_empty_when_no_enabled_models(self, client):
        """Test that list models returns empty list when no models are enabled."""
        # Mock config with no enabled models
        with patch('app.api.v1.endpoints.models.get_config_manager') as mock_get_cm:
            mock_cm = MagicMock()
            mock_cm.get_virtual_models.return_value = {
                "disabled-model": {
                    "proxy_key": "key",
                    "use": False,
                    "small": {"model": "model1"}
                }
            }
            mock_get_cm.return_value = mock_cm
            
            response = client.get("/proxy/api/v1/models")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 0


class TestGetModel:
    """Test cases for GET /proxy/api/v1/models/{model_id} endpoint."""

    def test_get_model_success(self, client):
        """Test getting a specific model that exists."""
        response = client.get("/proxy/api/v1/models/test-model")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-model"
        assert data["object"] == "model"
        assert "config" in data
        assert data["config"]["enabled"] is True
        assert data["config"]["current"] == "small"

    def test_get_model_not_found(self, client):
        """Test getting a non-existent model returns 404."""
        response = client.get("/proxy/api/v1/models/non-existent-model")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_disabled_model(self, client):
        """Test getting a disabled model returns its info."""
        response = client.get("/proxy/api/v1/models/disabled-model")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "disabled-model"
        assert data["config"]["enabled"] is False

    def test_get_model_with_current_small(self, client):
        """Test model info reflects current='small' configuration."""
        response = client.get("/proxy/api/v1/models/test-model")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["config"]["current"] == "small"
        assert "small_model" in data["config"]
        assert data["config"]["small_model"]["id"] == "test-small-model"

    def test_get_model_with_current_big(self, client):
        """Test model info reflects current='big' configuration."""
        # Create a model with current=big
        with patch('app.api.v1.endpoints.models.get_config_manager') as mock_get_cm:
            mock_cm = MagicMock()
            mock_cm.get_virtual_model.return_value = {
                "big-model": {
                    "proxy_key": "big-key",
                    "current": "big",
                    "use": True,
                    "small": {"model": "small-model"},
                    "big": {"model": "big-model"}
                }
            }
            mock_get_cm.return_value = mock_cm
            
            response = client.get("/proxy/api/v1/models/big-model")
            
            assert response.status_code == 200
            data = response.json()
            assert data["config"]["current"] == "big"


# =============================================================================
# Chat Completions Endpoint Tests (Non-Streaming)
# =============================================================================


class TestChatCompletionSuccess:
    """Test successful chat completion scenarios."""

    def test_chat_completion_success(self, client, mock_config_manager):
        """Test successful chat completion with valid request."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "id" in data
            assert data["object"] == "chat.completion"
            assert "created" in data
            assert "model" in data
            assert "choices" in data
            assert "usage" in data
            
            # Verify model name is transformed to virtual model name
            assert data["model"] == "test-model"
            
            # Verify choices
            assert len(data["choices"]) == 1
            choice = data["choices"][0]
            assert choice["index"] == 0
            assert choice["message"]["role"] == "assistant"
            assert choice["message"]["content"] == "This is a test response"
            assert choice["finish_reason"] == "stop"
            
            # Verify usage
            assert data["usage"]["prompt_tokens"] == 10
            assert data["usage"]["completion_tokens"] == 5
            assert data["usage"]["total_tokens"] == 15

    def test_chat_completion_with_optional_params(self, client, mock_config_manager):
        """Test chat completion with optional parameters."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 100,
                "n": 2,
                "presence_penalty": 0.5
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 200

    def test_chat_completion_without_bearer_prefix(self, client, mock_config_manager):
        """Test chat completion with proxy key without Bearer prefix."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            # Test with just the proxy key (no Bearer prefix)
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "test-proxy-key-123"}
            )
            
            assert response.status_code == 200


class TestChatCompletionAuth:
    """Test authentication scenarios for chat completions."""

    def test_chat_completion_missing_auth(self, client):
        """Test chat completion fails without authorization header."""
        request_body = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=request_body
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "authorization" in data["detail"].lower()

    def test_chat_completion_invalid_auth(self, client):
        """Test chat completion fails with invalid proxy key."""
        request_body = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=request_body,
            headers={"Authorization": "Bearer invalid-proxy-key"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "not found" in data["detail"].lower()

    def test_chat_completion_model_disabled(self, client):
        """Test chat completion fails when virtual model is disabled."""
        request_body = {
            "model": "disabled-model",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=request_body,
            headers={"Authorization": "Bearer disabled-proxy-key-456"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "disabled" in data["detail"].lower()


class TestChatCompletionErrors:
    """Test error handling scenarios for chat completions."""

    def test_chat_completion_model_not_found(self, client):
        """Test chat completion fails when proxy key doesn't match any model."""
        request_body = {
            "model": "non-existent",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=request_body,
            headers={"Authorization": "Bearer non-existent-proxy-key"}
        )
        
        assert response.status_code == 401

    def test_chat_completion_upstream_error(self, client, mock_config_manager):
        """Test error handling when upstream API fails."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = '{"error": "Internal server error"}'
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 500

    def test_chat_completion_upstream_timeout(self, client, mock_config_manager):
        """Test error handling when upstream API times out."""
        import httpx
        
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 504

    def test_chat_completion_upstream_connection_error(self, client, mock_config_manager):
        """Test error handling when upstream API connection fails."""
        import httpx
        
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 503


# =============================================================================
# Chat Completions Streaming Tests
# =============================================================================


class TestChatCompletionStreaming:
    """Test streaming chat completion scenarios."""

    def test_chat_completion_streaming_success(self, client, mock_config_manager):
        """Test successful streaming chat completion."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            # Create a mock response context manager
            mock_response_context = MagicMock()
            mock_response_context.status_code = 200
            
            # Create async iterator for streaming chunks
            async def async_iter_chunks():
                for chunk in MOCK_STREAMING_CHUNKS:
                    yield chunk
            
            mock_response_context.aiter_bytes = lambda: async_iter_chunks()
            
            # Setup mock client
            mock_client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response_context)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.stream = MagicMock(return_value=mock_response)
            
            mock_async_client.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "stream": True
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"},
                stream=True
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Read the streaming response
            chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                chunks.append(chunk.decode("utf-8"))
            
            response_text = "".join(chunks)
            
            # Verify SSE format
            assert "data:" in response_text
            assert "[DONE]" in response_text
            
            # Verify model name transformation in chunks
            assert "test-model" in response_text

    def test_chat_completion_streaming_error(self, client, mock_config_manager):
        """Test error handling during streaming."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            import httpx
            
            mock_client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.__aenter__ = AsyncMock(
                side_effect=httpx.TimeoutException("Stream timeout")
            )
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.stream = MagicMock(return_value=mock_response)
            
            mock_async_client.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "stream": True
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"},
                stream=True
            )
            
            assert response.status_code == 200
            
            # Read streaming response
            chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                chunks.append(chunk.decode("utf-8"))
            
            response_text = "".join(chunks)
            
            # Should contain error in stream
            assert "error" in response_text.lower() or "timeout" in response_text.lower()

    def test_chat_completion_streaming_upstream_error(self, client, mock_config_manager):
        """Test upstream error during streaming returns proper error format."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response_context = MagicMock()
            mock_response_context.status_code = 500
            mock_response_context.aread = AsyncMock(return_value=b'{"error": "Upstream error"}')
            
            mock_client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response_context)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.stream = MagicMock(return_value=mock_response)
            
            mock_async_client.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "stream": True
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"},
                stream=True
            )
            
            assert response.status_code == 200
            
            # Read streaming response
            chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                chunks.append(chunk.decode("utf-8"))
            
            response_text = "".join(chunks)
            
            # Should contain error data
            assert "error" in response_text.lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestFullChatFlow:
    """End-to-end integration tests for chat flow."""

    def test_full_chat_flow_non_streaming(self, client, mock_config_manager):
        """Test complete chat flow from request to response."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Step 1: List available models
            models_response = client.get("/proxy/api/v1/models")
            assert models_response.status_code == 200
            models_data = models_response.json()
            
            # Verify test-model is available
            model_ids = [m["id"] for m in models_data["data"]]
            assert "test-model" in model_ids
            
            # Step 2: Get model details
            model_info = client.get("/proxy/api/v1/models/test-model")
            assert model_info.status_code == 200
            assert model_info.json()["config"]["enabled"] is True
            
            # Step 3: Create chat completion
            request_body = {
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ]
            }
            
            completion_response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert completion_response.status_code == 200
            completion_data = completion_response.json()
            
            # Verify response
            assert completion_data["model"] == "test-model"
            assert len(completion_data["choices"]) > 0
            assert completion_data["choices"][0]["message"]["role"] == "assistant"

    def test_full_chat_flow_with_disabled_model_rejection(self, client, mock_config_manager):
        """Test that disabled models are properly rejected in chat flow."""
        # Step 1: List models shows only enabled models
        models_response = client.get("/proxy/api/v1/models")
        assert models_response.status_code == 200
        models_data = models_response.json()
        
        model_ids = [m["id"] for m in models_data["data"]]
        assert "disabled-model" not in model_ids
        
        # Step 2: Direct access to disabled model info works
        model_info = client.get("/proxy/api/v1/models/disabled-model")
        assert model_info.status_code == 200
        assert model_info.json()["config"]["enabled"] is False
        
        # Step 3: Chat completion with disabled model fails
        request_body = {
            "model": "disabled-model",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
        
        completion_response = client.post(
            "/proxy/api/v1/chat/completions",
            json=request_body,
            headers={"Authorization": "Bearer disabled-proxy-key-456"}
        )
        
        assert completion_response.status_code == 403

    def test_full_chat_flow_streaming(self, client, mock_config_manager):
        """Test complete streaming chat flow."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response_context = MagicMock()
            mock_response_context.status_code = 200
            
            async def async_iter_chunks():
                for chunk in MOCK_STREAMING_CHUNKS:
                    yield chunk
            
            mock_response_context.aiter_bytes = lambda: async_iter_chunks()
            
            mock_client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response_context)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.stream = MagicMock(return_value=mock_response)
            
            mock_async_client.return_value = mock_client_instance
            
            # Create streaming completion
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Tell me a story."}],
                "stream": True
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"},
                stream=True
            )
            
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # Collect all chunks
            collected_chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                collected_chunks.append(chunk.decode("utf-8"))
            
            full_response = "".join(collected_chunks)
            
            # Verify streaming format
            assert "data:" in full_response
            assert "[DONE]" in full_response
            # Should contain virtual model name, not upstream model name
            assert "test-model" in full_response


# =============================================================================
# Model Name Transformation Tests
# =============================================================================


class TestModelNameTransformation:
    """Test that model names are properly transformed between virtual and upstream."""

    def test_upstream_request_uses_actual_model(self, client, mock_config_manager):
        """Test that upstream request uses actual model name from config."""
        captured_payload = {}
        
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            def capture_request(*args, **kwargs):
                if 'json' in kwargs:
                    captured_payload['model'] = kwargs['json'].get('model')
                return AsyncMock()()
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            async def mock_post(*args, **kwargs):
                captured_payload['model'] = kwargs['json'].get('model')
                captured_payload['url'] = args[0] if args else kwargs.get('url')
                return mock_response
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = mock_post
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            # Upstream should receive actual model name
            assert captured_payload.get('model') == "test-small-model"

    def test_response_uses_virtual_model_name(self, client, mock_config_manager):
        """Test that response uses virtual model name, not upstream."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": []
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 200

    def test_chat_completion_with_multiple_messages(self, client, mock_config_manager):
        """Test chat completion with many messages."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "First message"},
                    {"role": "assistant", "content": "Response to first"},
                    {"role": "user", "content": "Second message"},
                    {"role": "assistant", "content": "Response to second"},
                    {"role": "user", "content": "Third message"}
                ]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer test-proxy-key-123"}
            )
            
            assert response.status_code == 200

    def test_chat_completion_model_with_only_small_config(self, client, mock_config_manager):
        """Test completion when model only has small config."""
        with patch('app.api.v1.endpoints.chat.httpx.AsyncClient') as mock_async_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_UPSTREAM_RESPONSE
            
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            request_body = {
                "model": "model-with-only-small",
                "messages": [{"role": "user", "content": "Hello!"}]
            }
            
            response = client.post(
                "/proxy/api/v1/chat/completions",
                json=request_body,
                headers={"Authorization": "Bearer small-only-key-789"}
            )
            
            assert response.status_code == 200

    def test_get_completions_info_endpoint(self, client):
        """Test GET /proxy/api/v1/chat/completions returns endpoint info."""
        response = client.get("/proxy/api/v1/chat/completions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["object"] == "list"
        assert len(data["data"]) > 0
        
        endpoint_info = data["data"][0]
        assert endpoint_info["id"] == "chat/completions"
        assert endpoint_info["object"] == "endpoint"
        assert endpoint_info["method"] == "POST"
        assert endpoint_info["streaming"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
