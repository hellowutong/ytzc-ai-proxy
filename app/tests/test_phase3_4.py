/"""
Test suite for Media Processing module.

Tests cover:
- Media file CRUD operations
- File upload/download
- URL download
- Transcription endpoints
- Statistics
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from core.config_manager import ConfigManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for testing."""
    with patch("app.api.v1.endpoints.media.get_config") as mock_get_config:
        def side_effect(key, default=None):
            config_map = {
                "ai-gateway.media.video.upload.max_size_mb": 100,
                "ai-gateway.media.audio.upload.max_size_mb": 100,
                "ai-gateway.media.text.upload.max_size_mb": 100,
                "ai-gateway.media.video.transcription": {
                    "processor": "whisper",
                    "default_model": "base",
                    "language": "zh",
                    "enabled": True,
                },
                "ai-gateway.media.audio.transcription": {
                    "processor": "whisper",
                    "default_model": "base",
                    "language": "zh",
                    "enabled": True,
                },
                "ai-gateway.media.video.download": {
                    "enabled": True,
                    "max_concurrent": 3,
                    "timeout_seconds": 300,
                },
                "ai-gateway.media.audio.download": {
                    "enabled": True,
                    "max_concurrent": 3,
                    "timeout_seconds": 300,
                },
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = side_effect
        yield mock_get_config


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB for testing."""
    with patch("app.api.v1.endpoints.media.get_mongodb_client") as mock:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.db = mock_db
        mock.return_value = mock_client
        yield mock_db


@pytest.fixture
def sample_media_file():
    """Create a sample media file for testing."""
    return {
        "_id": "test_media_id",
        "title": "Test Video",
        "media_type": "video",
        "file_name": "test.mp4",
        "file_path": "/uploads/video/test.mp4",
        "file_size": 1024000,
        "mime_type": "video/mp4",
        "duration": 120.5,
        "source_type": "upload",
        "status": "uploaded",
        "tags": ["test", "sample"],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


# ============================================================================
# Media List Tests
# ============================================================================

def test_list_media_files_success(client, mock_mongodb, mock_config_manager):
    """Test listing media files."""
    # Mock database response
    mock_mongodb.media_files.count_documents.return_value = 2
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__aiter__.return_value = [
        {
            "_id": "media1",
            "title": "Video 1",
            "media_type": "video",
            "file_name": "video1.mp4",
            "file_size": 1000000,
            "status": "uploaded",
            "tags": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        {
            "_id": "media2",
            "title": "Audio 1",
            "media_type": "audio",
            "file_name": "audio1.mp3",
            "file_size": 500000,
            "status": "transcribed",
            "tags": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
    ]
    mock_mongodb.media_files.find.return_value = mock_cursor
    
    response = client.get("/proxy/admin/media/files")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["media_files"]) == 2
    assert data["media_files"][0]["title"] == "Video 1"


def test_list_media_files_with_filter(client, mock_mongodb, mock_config_manager):
    """Test listing media files with type filter."""
    mock_mongodb.media_files.count_documents.return_value = 1
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__aiter__.return_value = [
        {
            "_id": "media1",
            "title": "Video 1",
            "media_type": "video",
            "file_name": "video1.mp4",
            "file_size": 1000000,
            "status": "uploaded",
            "tags": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
    ]
    mock_mongodb.media_files.find.return_value = mock_cursor
    
    response = client.get("/proxy/admin/media/files?media_type=video")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


# ============================================================================
# Media Upload Tests
# ============================================================================

@patch("app.api.v1.endpoints.media.UPLOAD_DIR", Path("/tmp/test_uploads"))
def test_upload_media_file_success(client, mock_mongodb, mock_config_manager, tmp_path):
    """Test uploading a media file."""
    # Create a temporary file
    test_file = tmp_path / "test.mp4"
    test_file.write_bytes(b"fake video content")
    
    # Mock insert result
    mock_result = MagicMock()
    mock_result.inserted_id = "new_media_id"
    mock_mongodb.media_files.insert_one.return_value = mock_result
    
    with patch("app.api.v1.endpoints.media.save_media_file") as mock_save:
        mock_save.return_value = ("/uploads/video/new_media_id.mp4", 1000)
        
        with open(test_file, "rb") as f:
            response = client.post(
                "/proxy/admin/media/upload",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"title": "Test Upload", "auto_transcribe": "false"},
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["media_id"] == "new_media_id"
    assert data["file_name"] == "test.mp4"


def test_upload_media_file_too_large(client, mock_mongodb, mock_config_manager, tmp_path):
    """Test uploading a file that exceeds size limit."""
    # Create a large temporary file
    test_file = tmp_path / "large.mp4"
    test_file.write_bytes(b"x" * (101 * 1024 * 1024))  # 101 MB
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/proxy/admin/media/upload",
            files={"file": ("large.mp4", f, "video/mp4")},
        )
    
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


# ============================================================================
# Media Detail Tests
# ============================================================================

def test_get_media_file_success(client, mock_mongodb, sample_media_file):
    """Test getting a specific media file."""
    mock_mongodb.media_files.find_one.return_value = sample_media_file
    
    response = client.get("/proxy/admin/media/files/test_media_id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_media_id"
    assert data["title"] == "Test Video"
    assert data["media_type"] == "video"


def test_get_media_file_not_found(client, mock_mongodb):
    """Test getting a non-existent media file."""
    mock_mongodb.media_files.find_one.return_value = None
    
    response = client.get("/proxy/admin/media/files/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# Media Update Tests
# ============================================================================

def test_update_media_file_success(client, mock_mongodb, sample_media_file):
    """Test updating media metadata."""
    mock_mongodb.media_files.find_one.side_effect = [
        sample_media_file,  # First call for existence check
        {**sample_media_file, "title": "Updated Title", "tags": ["new_tag"]},  # Second call for return
    ]
    
    response = client.put(
        "/proxy/admin/media/files/test_media_id",
        json={"title": "Updated Title", "tags": ["new_tag"]},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


# ============================================================================
# Media Delete Tests
# ============================================================================

@patch("os.path.exists")
@patch("os.remove")
def test_delete_media_file_success(mock_remove, mock_exists, client, mock_mongodb, sample_media_file):
    """Test deleting a media file."""
    mock_exists.return_value = True
    mock_mongodb.media_files.find_one.return_value = sample_media_file
    
    response = client.delete("/proxy/admin/media/files/test_media_id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    mock_remove.assert_called_once_with("/uploads/video/test.mp4")


# ============================================================================
# URL Download Tests
# ============================================================================

@patch("app.api.v1.endpoints.media.download_file_from_url")
def test_download_from_url_success(mock_download, client, mock_mongodb, mock_config_manager):
    """Test downloading media from URL."""
    mock_download.return_value = ("/uploads/video/url_video.mp4", 5000000)
    
    mock_result = MagicMock()
    mock_result.inserted_id = "url_media_id"
    mock_mongodb.media_files.insert_one.return_value = mock_result
    
    response = client.post(
        "/proxy/admin/media/download-url",
        json={
            "url": "https://example.com/video.mp4",
            "media_type": "video",
            "title": "Downloaded Video",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["media_id"] == "url_media_id"


def test_download_from_url_disabled(client, mock_config_manager):
    """Test downloading when URL download is disabled."""
    with patch("app.api.v1.endpoints.media.get_config") as mock_get_config:
        def side_effect(key, default=None):
            if "download.enabled" in key:
                return False
            return default
        mock_get_config.side_effect = side_effect
        
        response = client.post(
            "/proxy/admin/media/download-url",
            json={
                "url": "https://example.com/video.mp4",
                "media_type": "video",
            },
        )
    
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


# ============================================================================
# Transcription Tests
# ============================================================================

def test_transcribe_media_success(client, mock_mongodb, sample_media_file):
    """Test starting transcription for a media file."""
    sample_media_file["media_type"] = "video"
    mock_mongodb.media_files.find_one.return_value = sample_media_file
    
    response = client.post(
        "/proxy/admin/media/files/test_media_id/transcribe",
        json={"language": "zh"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "started" in data["message"].lower() or "启动" in data["message"]


def test_transcribe_media_not_transcribable(client, mock_mongodb):
    """Test transcribing a non-transcribable file (text)."""
    mock_mongodb.media_files.find_one.return_value = {
        "_id": "text_id",
        "media_type": "text",
        "title": "Text File",
    }
    
    response = client.post(
        "/proxy/admin/media/files/text_id/transcribe",
        json={"language": "zh"},
    )
    
    assert response.status_code == 400
    assert "only video and audio" in response.json()["detail"].lower()


# ============================================================================
# Statistics Tests
# ============================================================================

def test_get_media_stats(client, mock_mongodb):
    """Test getting media statistics."""
    mock_mongodb.media_files.count_documents.side_effect = [
        100,  # total
        30,   # video
        40,   # audio
        30,   # text
        50,   # transcribed
        10,   # pending
        5,    # failed
    ]
    
    # Mock aggregation for duration
    mock_agg_cursor = MagicMock()
    mock_agg_cursor.to_list.return_value = [{"total": 3600}]
    mock_mongodb.media_files.aggregate.return_value = mock_agg_cursor
    
    response = client.get("/proxy/admin/media/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 100
    assert data["by_type"]["video"] == 30
    assert data["by_type"]["audio"] == 40
    assert data["by_type"]["text"] == 30
    assert data["transcribed_count"] == 50


# ============================================================================
# File Download Tests
# ============================================================================

@patch("os.path.exists")
def test_download_media_file_success(mock_exists, client, mock_mongodb, sample_media_file):
    """Test downloading the original media file."""
    mock_exists.return_value = True
    mock_mongodb.media_files.find_one.return_value = sample_media_file
    
    response = client.get("/proxy/admin/media/files/test_media_id/download")
    
    # Should return a file response
    assert response.status_code == 200


def test_download_media_file_not_found(client, mock_mongodb, sample_media_file):
    """Test downloading a file that doesn't exist on disk."""
    mock_mongodb.media_files.find_one.return_value = sample_media_file
    
    response = client.get("/proxy/admin/media/files/test_media_id/download")
    
    assert response.status_code == 404


# ============================================================================
# Integration Tests
# ============================================================================

def test_media_lifecycle(client, mock_mongodb, mock_config_manager, tmp_path):
    """Test complete media lifecycle: create, update, transcribe, delete."""
    # 1. Upload file
    test_file = tmp_path / "lifecycle.mp4"
    test_file.write_bytes(b"fake video content")
    
    mock_result = MagicMock()
    mock_result.inserted_id = "lifecycle_id"
    mock_mongodb.media_files.insert_one.return_value = mock_result
    mock_mongodb.media_files.update_one.return_value = MagicMock()
    
    with patch("app.api.v1.endpoints.media.save_media_file") as mock_save:
        mock_save.return_value = ("/uploads/video/lifecycle_id.mp4", 1000)
        
        with open(test_file, "rb") as f:
            response = client.post(
                "/proxy/admin/media/upload",
                files={"file": ("lifecycle.mp4", f, "video/mp4")},
                data={"title": "Lifecycle Test", "auto_transcribe": "false"},
            )
    
    assert response.status_code == 200
    media_id = response.json()["media_id"]
    
    # 2. Get file
    mock_mongodb.media_files.find_one.return_value = {
        "_id": media_id,
        "title": "Lifecycle Test",
        "media_type": "video",
        "file_name": "lifecycle.mp4",
        "file_size": 1000,
        "status": "uploaded",
        "tags": [],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    
    response = client.get(f"/proxy/admin/media/files/{media_id}")
    assert response.status_code == 200
    
    # 3. Update file
    mock_mongodb.media_files.find_one.side_effect = [
        {"_id": media_id, "title": "Old Title"},
        {"_id": media_id, "title": "Updated Title", "tags": ["updated"]},
    ]
    
    response = client.put(
        f"/proxy/admin/media/files/{media_id}",
        json={"title": "Updated Title", "tags": ["updated"]},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    
    # 4. Start transcription
    mock_mongodb.media_files.find_one.return_value = {
        "_id": media_id,
        "media_type": "video",
        "status": "uploaded",
    }
    
    response = client.post(
        f"/proxy/admin/media/files/{media_id}/transcribe",
        json={"language": "zh"},
    )
    assert response.status_code == 200
    
    # 5. Delete file
    with patch("os.path.exists") as mock_exists, patch("os.remove") as mock_remove:
        mock_exists.return_value = True
        mock_mongodb.media_files.find_one.return_value = {
            "_id": media_id,
            "file_path": "/uploads/video/lifecycle_id.mp4",
        }
        
        response = client.delete(f"/proxy/admin/media/files/{media_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
