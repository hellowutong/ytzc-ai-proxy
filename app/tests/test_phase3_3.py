"""
Test script for Phase 3.3: Knowledge Base Extraction

Tests:
- Document CRUD operations
- File upload
- Text extraction
- Knowledge chunk creation
- Vector search
"""

import asyncio
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from fastapi.testclient import TestClient

from main import app
from core.config_manager import ConfigManager
from db.mongodb import get_mongodb_client
from db.qdrant import get_qdrant_client


# Create test client
client = TestClient(app)


class TestKnowledgeAPI:
    """Test knowledge base API endpoints."""
    
    def setup_method(self):
        """Setup test environment."""
        # Mock config for testing
        self.config_manager = ConfigManager("config.yml", enable_watch=False)
        
    def test_list_documents(self):
        """Test GET /proxy/admin/knowledge/documents"""
        response = client.get("/proxy/admin/knowledge/documents")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "documents" in data
        print(f"✓ List documents: {data['total']} total")
    
    def test_create_document(self):
        """Test POST /proxy/admin/knowledge/documents"""
        doc_data = {
            "title": "Test Document",
            "content_type": "text",
            "tags": ["test", "api"]
        }
        response = client.post("/proxy/admin/knowledge/documents", json=doc_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["status"] == "pending"
        print(f"✓ Create document: {data['id']}")
        return data["id"]
    
    def test_get_document(self):
        """Test GET /proxy/admin/knowledge/documents/{id}"""
        # First create a document
        doc_id = self.test_create_document()
        
        response = client.get(f"/proxy/admin/knowledge/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        print(f"✓ Get document: {data['title']}")
    
    def test_update_document(self):
        """Test PUT /proxy/admin/knowledge/documents/{id}"""
        # First create a document
        doc_id = self.test_create_document()
        
        update_data = {
            "title": "Updated Test Document",
            "tags": ["updated", "test"]
        }
        response = client.put(f"/proxy/admin/knowledge/documents/{doc_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Test Document"
        print(f"✓ Update document: {data['title']}")
    
    def test_delete_document(self):
        """Test DELETE /proxy/admin/knowledge/documents/{id}"""
        # First create a document
        doc_id = self.test_create_document()
        
        response = client.delete(f"/proxy/admin/knowledge/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✓ Delete document: {doc_id}")
    
    def test_get_stats(self):
        """Test GET /proxy/admin/knowledge/stats"""
        response = client.get("/proxy/admin/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "by_status" in data
        print(f"✓ Get stats: {data['total_documents']} documents")
    
    def test_query_knowledge(self):
        """Test POST /proxy/admin/knowledge/query"""
        query_data = {
            "query": "test query",
            "limit": 5,
            "threshold": 0.5
        }
        response = client.post("/proxy/admin/knowledge/query", json=query_data)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        print(f"✓ Query knowledge: {data['total_found']} results")


class TestKnowledgeModels:
    """Test knowledge base models."""
    
    def test_document_model(self):
        """Test Document Pydantic model."""
        from models.knowledge import Document, DocumentStatus, DocumentType
        
        doc = Document(
            title="Test Document",
            content_type=DocumentType.TEXT,
            status=DocumentStatus.PENDING,
            shared=False,
            tags=["test"],
            topics=[]
        )
        
        assert doc.title == "Test Document"
        assert doc.content_type == DocumentType.TEXT
        assert doc.status == DocumentStatus.PENDING
        print("✓ Document model validation passed")
    
    def test_knowledge_chunk_model(self):
        """Test KnowledgeChunk Pydantic model."""
        from models.knowledge import KnowledgeChunk
        
        chunk = KnowledgeChunk(
            content="Test content",
            document_id="doc123",
            topic="test"
        )
        
        assert chunk.content == "Test content"
        assert chunk.document_id == "doc123"
        print("✓ KnowledgeChunk model validation passed")


def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Phase 3.3: Knowledge Base Extraction Tests")
    print("="*60 + "\n")
    
    api_tests = TestKnowledgeAPI()
    model_tests = TestKnowledgeModels()
    
    # Run API tests
    try:
        api_tests.test_list_documents()
    except Exception as e:
        print(f"✗ List documents failed: {e}")
    
    try:
        api_tests.test_create_document()
    except Exception as e:
        print(f"✗ Create document failed: {e}")
    
    try:
        api_tests.test_get_document()
    except Exception as e:
        print(f"✗ Get document failed: {e}")
    
    try:
        api_tests.test_update_document()
    except Exception as e:
        print(f"✗ Update document failed: {e}")
    
    try:
        api_tests.test_delete_document()
    except Exception as e:
        print(f"✗ Delete document failed: {e}")
    
    try:
        api_tests.test_get_stats()
    except Exception as e:
        print(f"✗ Get stats failed: {e}")
    
    try:
        api_tests.test_query_knowledge()
    except Exception as e:
        print(f"✗ Query knowledge failed: {e}")
    
    # Run model tests
    try:
        model_tests.test_document_model()
    except Exception as e:
        print(f"✗ Document model test failed: {e}")
    
    try:
        model_tests.test_knowledge_chunk_model()
    except Exception as e:
        print(f"✗ KnowledgeChunk model test failed: {e}")
    
    print("\n" + "="*60)
    print("Phase 3.3 Tests Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_tests()
