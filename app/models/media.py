"""
Media processing models for video, audio, and text files.

Features:
- Media file metadata and status tracking
- Transcription results and segments
- Media type enumerations
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    """Media file types."""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    IMAGE = "image"


class MediaStatus(str, Enum):
    """Media processing status."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    EXTRACTING = "extracting"
    PROCESSED = "processed"
    FAILED = "failed"


class TranscriptionSegment(BaseModel):
    """A single transcription segment."""
    id: str
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    speaker: Optional[str] = None


class TranscriptionResult(BaseModel):
    """Transcription result for audio/video."""
    text: str
    language: str = "zh"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    segments: List[TranscriptionSegment] = []
    duration: float = Field(..., description="Duration in seconds")
    word_count: int = 0
    processing_time_ms: int = 0


class MediaFile(BaseModel):
    """Media file record."""
    id: Optional[str] = None
    title: str
    media_type: MediaType
    
    # File info
    file_name: str
    file_path: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    duration: Optional[float] = None  # For video/audio in seconds
    
    # Source
    source_type: str = "upload"  # upload, url, download
    source_url: Optional[str] = None
    
    # Status
    status: MediaStatus = MediaStatus.PENDING
    status_message: Optional[str] = None
    
    # Transcription
    transcription: Optional[TranscriptionResult] = None
    transcription_model: Optional[str] = None
    
    # Relations
    knowledge_document_id: Optional[str] = None  # Linked knowledge document
    
    # Metadata
    tags: List[str] = []
    custom_metadata: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class MediaCreateRequest(BaseModel):
    """Request to create media record."""
    title: str
    media_type: MediaType
    source_url: Optional[str] = None
    tags: List[str] = []
    custom_metadata: Dict[str, Any] = {}


class MediaUpdateRequest(BaseModel):
    """Request to update media metadata."""
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class MediaListRequest(BaseModel):
    """Request to list media files."""
    media_type: Optional[MediaType] = None
    status: Optional[MediaStatus] = None
    search: Optional[str] = None
    skip: int = 0
    limit: int = 20


class MediaListResponse(BaseModel):
    """Response for media list."""
    total: int
    media_files: List[MediaFile]
    skip: int
    limit: int


class MediaUploadResponse(BaseModel):
    """Response for media upload."""
    success: bool
    media_id: str
    file_name: str
    file_size: int
    media_type: MediaType
    message: str
    status: MediaStatus


class TranscriptionRequest(BaseModel):
    """Request to transcribe media."""
    language: str = "zh"
    model: Optional[str] = None  # whisper model name
    split: Optional[int] = None  # Override config split setting


class TranscriptionResponse(BaseModel):
    """Response for transcription."""
    success: bool
    media_id: str
    transcription: Optional[TranscriptionResult]
    message: str


class MediaStats(BaseModel):
    """Media library statistics."""
    total_files: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    total_duration: float  # Total seconds
    transcribed_count: int
    pending_count: int
    failed_count: int


class DownloadUrlRequest(BaseModel):
    """Request to download media from URL."""
    url: str
    title: Optional[str] = None
    media_type: MediaType
    tags: List[str] = []
    auto_transcribe: bool = True


class DownloadUrlResponse(BaseModel):
    """Response for URL download."""
    success: bool
    media_id: str
    message: str
    status: MediaStatus
