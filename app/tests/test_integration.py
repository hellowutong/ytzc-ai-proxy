"""
Phase 4.1: Comprehensive Integration Test Suite
Tests end-to-end workflows and module interactions
"""
import asyncio
import pytest
import httpx
from datetime import datetime, timedelta
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from main import app
from core.config_manager import ConfigManager
from db.mongodb import MongoDB
from db.redis import RedisClient
from db.qdrant import QdrantClient


class TestIntegrationConfigFlow:
    """Test configuration flows and hot-reload"""
    
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)
    
    def test_config_hot_reload_preserves_virtual_models(self, client, monkeypatch):
        """Test that hot reload doesn't lose virtual model changes"""
        # Create a virtual model
        new_model = {
            "model_name": "test-hot-reload-model",
            "small": {"name": "gpt-3.5-turbo", "proxy_key": "sk-test"},
            "big": {"name": "gpt-4", "proxy_key": "sk-test"},
            "small2big": {"enable": True, "token_threshold": 3000},
            "enable": True
        }
        
        response = client.post("/proxy/admin/virtual-models", json=new_model)
        assert response.status_code == 201
        
        # Simulate config reload by triggering health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Verify model still exists
        response = client.get(f"/proxy/admin/virtual-models/{new_model['model_name']}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["model_name"] == new_model["model_name"]
    
    def test_config_readonly_sections_cannot_modify_structure(self, client):
        """Test that non-virtual_models sections reject structural changes"""
        # Try to add new section to app config
        invalid_update = {
            "app": {
                "new_field": "test_value"
            }
        }
        
        response = client.post("/proxy/admin/config/update", json=invalid_update)
        assert response.status_code == 422
        assert "cannot add or remove keys" in response.json()["detail"]
    
    def test_config_value_updates_allowed(self, client):
        """Test that value updates are allowed"""
        # Get current app version
        response = client.get("/proxy/admin/config/app")
        assert response.status_code == 200
        original_version = response.json()["data"]["app"]["version"]
        
        # Update app version
        update = {
            "app": {
                "version": "9.9.9-test"
            }
        }
        
        response = client.post("/proxy/admin/config/update", json=update)
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/proxy/admin/config/app")
        assert response.status_code == 200
        new_version = response.json()["data"]["app"]["version"]
        assert new_version == "9.9.9-test"


class TestIntegrationVirtualModelToChat:
    """Test end-to-end flow: Virtual Model → Chat"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_upstream(self):
        """Mock upstream LLM API"""
        with patch("app.api.v1.endpoints.chat.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1700000000,
                "model": "upstream-model",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Test response"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
            mock_response.raise_for_status = Mock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance
            yield mock_client
    
    def test_full_flow_create_model_and_chat(self, client, mock_upstream):
        """Test complete flow: create virtual model, chat with it"""
        # Step 1: Create virtual model
        model_data = {
            "model_name": "test-chat-model",
            "small": {"name": "gpt-3.5-turbo", "proxy_key": "sk-test-key-123"},
            "big": {"name": "gpt-4", "proxy_key": "sk-test-key-456"},
            "small2big": {"enable": True, "token_threshold": 3000},
            "enable": True
        }
        
        response = client.post("/proxy/admin/virtual-models", json=model_data)
        assert response.status_code == 201
        model_id = response.json()["data"]["model_name"]
        
        # Step 2: Verify model appears in models list
        response = client.get("/proxy/api/v1/models")
        assert response.status_code == 200
        models = response.json()["data"]
        assert any(m["id"] == model_id for m in models)
        
        # Step 3: Chat with the model
        chat_request = {
            "model": model_id,
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=chat_request,
            headers={"Authorization": "Bearer sk-test-key-123"}
        )
        assert response.status_code == 200
        
        # Step 4: Verify model name in response is transformed back
        data = response.json()
        assert data["model"] == model_id
    
    def test_chat_with_disabled_model_fails(self, client, mock_upstream):
        """Test that chatting with disabled model fails"""
        # Create and then disable model
        model_data = {
            "model_name": "test-disabled-model",
            "small": {"name": "gpt-3.5-turbo", "proxy_key": "sk-test"},
            "big": {"name": "gpt-4", "proxy_key": "sk-test"},
            "small2big": {"enable": True, "token_threshold": 3000},
            "enable": True
        }
        
        client.post("/proxy/admin/virtual-models", json=model_data)
        
        # Disable the model
        client.post(f"/proxy/admin/virtual-models/{model_data['model_name']}/enable?enable=false")
        
        # Try to chat
        chat_request = {
            "model": model_data["model_name"],
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = client.post(
            "/proxy/api/v1/chat/completions",
            json=chat_request,
            headers={"Authorization": "Bearer sk-test"}
        )
        assert response.status_code == 400
        assert "disabled" in response.json()["detail"]


class TestIntegrationKnowledgeFlow:
    """Test end-to-end knowledge base workflows"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_upload_document_extract_query_flow(self, client):
        """Test: Upload → Extract → Query flow"""
        # Step 1: Upload document
        import io
        test_content = b"This is a test document for knowledge extraction. It contains information about AI and machine learning."
        
        files = {
            "file": ("test_doc.txt", io.BytesIO(test_content), "text/plain")
        }
        data = {
            "title": "Test Document",
            "source": "Integration Test"
        }
        
        response = client.post("/proxy/admin/knowledge/documents/upload", files=files, data=data)
        assert response.status_code == 200
        doc_id = response.json()["data"]["id"]
        
        # Step 2: Extract text
        response = client.post(f"/proxy/admin/knowledge/documents/{doc_id}/extract")
        assert response.status_code == 200
        
        # Step 3: Query knowledge base
        query_data = {
            "query": "AI and machine learning",
            "model_name": "test-model",
            "top_k": 5
        }
        
        response = client.post("/proxy/admin/knowledge/query", json=query_data)
        assert response.status_code == 200
        results = response.json()["data"]
        assert "results" in results
    
    def test_document_lifecycle(self, client):
        """Test document creation, update, deletion"""
        # Create document
        doc_data = {
            "title": "Lifecycle Test Doc",
            "content": "Original content",
            "source": "test",
            "type": "text"
        }
        
        response = client.post("/proxy/admin/knowledge/documents", json=doc_data)
        assert response.status_code == 200
        doc_id = response.json()["data"]["id"]
        
        # Update document
        update_data = {
            "title": "Updated Title",
            "content": "Updated content"
        }
        
        response = client.put(f"/proxy/admin/knowledge/documents/{doc_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = client.get(f"/proxy/admin/knowledge/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "Updated Title"
        
        # Delete document
        response = client.delete(f"/proxy/admin/knowledge/documents/{doc_id}")
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(f"/proxy/admin/knowledge/documents/{doc_id}")
        assert response.status_code == 404


class TestIntegrationMediaFlow:
    """Test end-to-end media processing workflows"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_media_upload_and_management(self, client):
        """Test media upload, update, delete flow"""
        import io
        
        # Upload media file
        test_audio = b"RIFF\x26\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00"
        files = {
            "file": ("test_audio.wav", io.BytesIO(test_audio), "audio/wav")
        }
        data = {
            "title": "Test Audio",
            "type": "audio"
        }
        
        response = client.post("/proxy/admin/media/upload", files=files, data=data)
        assert response.status_code == 200
        media_id = response.json()["data"]["id"]
        
        # Update metadata
        update_data = {
            "title": "Updated Audio Title",
            "description": "Test description"
        }
        
        response = client.put(f"/proxy/admin/media/files/{media_id}", json=update_data)
        assert response.status_code == 200
        
        # Delete media
        response = client.delete(f"/proxy/admin/media/files/{media_id}")
        assert response.status_code == 200
    
    def test_media_type_filtering(self, client):
        """Test media filtering by type"""
        # Query video files
        response = client.get("/proxy/admin/media/files?type=video")
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(m["type"] == "video" for m in data.get("items", []))
        
        # Query audio files
        response = client.get("/proxy/admin/media/files?type=audio")
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(m["type"] == "audio" for m in data.get("items", []))


class TestIntegrationRSSFlow:
    """Test end-to-end RSS workflows"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_rss_fetch_and_item_management(self, client):
        """Test RSS fetch, item operations, extraction"""
        # Get projects list
        response = client.get("/proxy/admin/rss/projects")
        assert response.status_code == 200
        projects = response.json()["data"]
        assert len(projects) > 0
        
        # Manual fetch (this will use mocked feedparser)
        fetch_data = {
            "project_name": projects[0]["name"]
        }
        
        with patch("app.api.v1.endpoints.rss.feedparser.parse") as mock_parse:
            mock_feed = Mock()
            mock_feed.entries = [
                Mock(
                    title="Test Article",
                    link="https://example.com/article1",
                    published_parsed=(2024, 1, 1, 0, 0, 0, 0, 0, 0),
                    summary="Test summary",
                    content=[{"value": "<p>Full content</p>"}]
                )
            ]
            mock_parse.return_value = mock_feed
            
            response = client.post("/proxy/admin/rss/fetch", json=fetch_data)
            assert response.status_code == 200
            fetch_result = response.json()["data"]
            assert fetch_result["success"] == 1
    
    def test_rss_item_batch_operations(self, client):
        """Test RSS item batch operations"""
        # Get items
        response = client.get("/proxy/admin/rss/items?limit=10")
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        
        if items:
            item_ids = [items[0]["id"]]
            
            # Batch mark as read
            batch_data = {
                "operation": "read",
                "ids": item_ids
            }
            
            response = client.post("/proxy/admin/rss/batch", json=batch_data)
            assert response.status_code == 200


class TestIntegrationDashboardAndStats:
    """Test dashboard and statistics integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_dashboard_integration(self, client):
        """Test dashboard returns integrated data"""
        response = client.get("/proxy/admin/dashboard")
        assert response.status_code == 200
        
        data = response.json()["data"]
        
        # Verify all sections exist
        assert "overview" in data
        assert "statistics" in data
        assert "service_health" in data
        assert "models_summary" in data
        
        # Verify structure
        assert "knowledge" in data["statistics"]
        assert "media" in data["statistics"]
        assert "rss" in data["statistics"]
    
    def test_all_stats_endpoints(self, client):
        """Test all statistics endpoints return valid data"""
        endpoints = [
            "/proxy/admin/knowledge/stats",
            "/proxy/admin/media/stats",
            "/proxy/admin/rss/stats"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "data" in data


class TestIntegrationLogsFlow:
    """Test logging integration across modules"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_logs_api_returns_data(self, client):
        """Test that logs API returns data"""
        # Query request logs
        response = client.get("/proxy/admin/logs/requests?limit=10")
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert "logs" in data
        assert "total" in data
        
        # Query system logs
        response = client.get("/proxy/admin/logs/system?limit=10")
        assert response.status_code == 200
    
    def test_logs_filtering(self, client):
        """Test logs filtering by level and time"""
        # Filter by level
        response = client.get("/proxy/admin/logs/system?level=ERROR")
        assert response.status_code == 200
        
        # Filter by time range
        from_time = (datetime.now() - timedelta(hours=1)).isoformat()
        to_time = datetime.now().isoformat()
        
        response = client.get(
            f"/proxy/admin/logs/system?from_time={from_time}&to_time={to_time}"
        )
        assert response.status_code == 200


class TestIntegrationErrorHandling:
    """Test error handling across all endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_not_found_handling(self, client):
        """Test 404 handling"""
        response = client.get("/proxy/admin/virtual-models/non-existent-model")
        assert response.status_code == 404
        
        response = client.get("/proxy/admin/knowledge/documents/non-existent-id")
        assert response.status_code == 404
    
    def test_validation_errors(self, client):
        """Test validation error responses"""
        # Invalid virtual model data
        invalid_model = {
            "model_name": "test",
            # Missing required fields
        }
        
        response = client.post("/proxy/admin/virtual-models", json=invalid_model)
        assert response.status_code == 422
        
        # Invalid chat request
        invalid_chat = {
            "messages": "not-an-array"  # Should be array
        }
        
        response = client.post("/proxy/api/v1/chat/completions", json=invalid_chat)
        assert response.status_code == 422


class TestIntegrationServiceHealth:
    """Test service health and connectivity"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_dashboard_health_status(self, client):
        """Test dashboard health status for all services"""
        response = client.get("/proxy/admin/dashboard")
        assert response.status_code == 200
        
        services = response.json()["data"]["service_health"]
        assert "mongodb" in services
        assert "redis" in services
        assert "qdrant" in services


@pytest.mark.asyncio
class TestIntegrationAsyncOperations:
    """Test async operations and concurrent access"""
    
    async def test_concurrent_model_creation(self, client):
        """Test concurrent model creation doesn't cause race conditions"""
        models = []
        
        async def create_model(i):
            model_data = {
                "model_name": f"concurrent-test-{i}",
                "small": {"name": "gpt-3.5-turbo", "proxy_key": "sk-test"},
                "big": {"name": "gpt-4", "proxy_key": "sk-test"},
                "small2big": {"enable": True, "token_threshold": 3000},
                "enable": True
            }
            response = client.post("/proxy/admin/virtual-models", json=model_data)
            return response.status_code == 201
        
        # Create 5 models concurrently
        results = await asyncio.gather(*[create_model(i) for i in range(5)])
        
        # All should succeed
        assert all(results)
        
        # Cleanup
        for i in range(5):
            client.delete(f"/proxy/admin/virtual-models/concurrent-test-{i}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
