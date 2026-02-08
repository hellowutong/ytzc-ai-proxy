"""
Knowledge base models for document management and extraction.

Features:
- Document metadata
- Extraction results
- Knowledge chunks for vector storage
- Query results
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator

from models.base import BaseModel, TimestampMixin


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"  # Just uploaded
    EXTRACTING = "extracting"  # Text extraction in progress
    EXTRACTED = "extracted"  # Text extraction complete
    PROCESSING = "processing"  # Knowledge extraction in progress
    PROCESSED = "processed"  # Fully processed
    FAILED = "failed"  # Processing failed


class DocumentType(str, Enum):
    """Document content type."""
    TEXT = "text"  # Plain text, markdown, etc.
    PDF = "pdf"  # PDF files
    DOC = "doc"  # Word documents
    IMAGE = "image"  # Images with OCR
    VIDEO = "video"  # Video transcriptions
    AUDIO = "audio"  # Audio transcriptions
    RSS = "rss"  # RSS feed content
    WEB = "web"  # Web page content


class KnowledgeChunk(BaseModel):
    """Knowledge chunk for vector storage."""
    
    id: Optional[str] = None
    content: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Parent document ID")
    model_id: Optional[str] = Field(None, description="Associated virtual model")
    topic: Optional[str] = Field(None, description="Classified topic")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = Field(None, description="Similarity score for queries")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel, TimestampMixin):
    """Document metadata model."""
    
    id: Optional[str] = Field(None, alias="_id")
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, description="Extracted text content")
    content_type: DocumentType = Field(default=DocumentType.TEXT)
    file_path: Optional[str] = Field(None, description="Original file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    
    # Processing status
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    status_message: Optional[str] = Field(None, description="Status details or error message")
    
    # Associations
    model_id: Optional[str] = Field(None, description="Associated virtual model")
    shared: bool = Field(default=False, description="Whether shared across models")
    topics: List[str] = Field(default_factory=list, description="Classified topics")
    
    # Extraction metadata
    extraction_confidence: Optional[float] = Field(None, description="Extraction quality score")
    chunk_count: int = Field(default=0, description="Number of knowledge chunks")
    word_count: Optional[int] = Field(None, description="Word count")
    
    # Source info
    source_url: Optional[str] = Field(None, description="Original URL if downloaded")
    source_type: Optional[str] = Field(None, description="Source type (upload/rss/web)")
    
    # User metadata
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreateRequest(BaseModel):
    """Request to create a document record."""
    
    title: str = Field(..., min_length=1, max_length=500)
    content_type: DocumentType = Field(default=DocumentType.TEXT)
    model_id: Optional[str] = Field(None, description="Associate with specific model")
    shared: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentUpdateRequest(BaseModel):
    """Request to update document metadata."""
    
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    model_id: Optional[str] = None
    shared: Optional[bool] = None
    tags: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class DocumentListRequest(BaseModel):
    """Request to list documents with filters."""
    
    model_id: Optional[str] = None
    status: Optional[DocumentStatus] = None
    content_type: Optional[DocumentType] = None
    shared: Optional[bool] = None
    topic: Optional[str] = None
    search: Optional[str] = None  # Text search in title/content
    tags: Optional[List[str]] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class DocumentListResponse(BaseModel):
    """Response for document list."""
    
    total: int
    documents: List[Document]
    skip: int
    limit: int


class KnowledgeQueryRequest(BaseModel):
    """Request to query knowledge base."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    model_id: Optional[str] = Field(None, description="Filter by model")
    topic: Optional[str] = Field(None, description="Filter by topic")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    threshold: Optional[float] = Field(None, ge=0, le=1, description="Similarity threshold")
    
    @field_validator('threshold')
    def validate_threshold(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Threshold must be between 0 and 1')
        return v


class KnowledgeQueryResponse(BaseModel):
    """Response for knowledge query."""
    
    query: str
    results: List[KnowledgeChunk]
    total_found: int
    threshold_used: float


class ExtractionRequest(BaseModel):
    """Request to extract knowledge from document."""
    
    document_id: str
    model_id: Optional[str] = None  # Target model for association
    threshold: Optional[float] = Field(None, ge=0, le=1)
    auto_classify: bool = Field(default=True, description="Auto-classify topics")


class ExtractionResult(BaseModel):
    """Result of knowledge extraction."""
    
    document_id: str
    success: bool
    chunks_created: int
    topics_detected: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    message: str
    processing_time_ms: Optional[int] = None


class DocumentStats(BaseModel):
    """Statistics for documents and knowledge."""
    
    total_documents: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_model: Dict[str, int]
    total_chunks: int
    total_words: int
    avg_extraction_confidence: Optional[float] = None


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    
    success: bool
    document_id: Optional[str] = None
    file_name: str
    file_size: int
    content_type: DocumentType
    message: str
    status: DocumentStatus
