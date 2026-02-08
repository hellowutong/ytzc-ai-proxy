"""
RSS Models for AI Gateway
Handles RSS feeds, items, and reading status
Reference FOLO design for long-term memory vs timeliness
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class RSSItemStatus(str, Enum):
    """RSS item status"""
    UNREAD = "unread"
    READING = "reading"
    READ = "read"
    EXTRACTED = "extracted"  # Knowledge extracted
    ARCHIVED = "archived"  # Permanent storage


class RSSProject(BaseModel):
    """RSS project/channel configuration"""
    name: str = Field(..., description="Project name/identifier")
    url: str = Field(..., description="RSS feed URL")
    enabled: bool = Field(default=True, description="Whether to fetch")
    description: Optional[str] = Field(default=None, description="Project description")
    icon: Optional[str] = Field(default=None, description="Project icon URL")
    last_fetch_at: Optional[datetime] = Field(default=None, description="Last fetch timestamp")
    fetch_count: int = Field(default=0, description="Total fetch count")
    item_count: int = Field(default=0, description="Total items fetched")
    error_count: int = Field(default=0, description="Consecutive error count")
    last_error: Optional[str] = Field(default=None, description="Last error message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "tech-news",
                "url": "https://techcrunch.com/feed/",
                "enabled": True,
                "description": "Technology news",
                "fetch_count": 150,
                "item_count": 5000
            }
        }


class RSSItem(BaseModel):
    """RSS item/article"""
    id: Optional[str] = Field(default=None, alias="_id")
    project_name: str = Field(..., description="Belongs to which project")
    title: str = Field(..., description="Article title")
    link: str = Field(..., description="Original URL")
    description: Optional[str] = Field(default=None, description="Article summary/description")
    content: Optional[str] = Field(default=None, description="Full content (if available)")
    author: Optional[str] = Field(default=None, description="Author name")
    published_at: Optional[datetime] = Field(default=None, description="Original publish time")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    status: RSSItemStatus = Field(default=RSSItemStatus.UNREAD)
    is_permanent: bool = Field(default=False, description="Long-term memory flag")
    extracted: bool = Field(default=False, description="Knowledge extracted")
    extraction_doc_id: Optional[str] = Field(default=None, description="Linked knowledge document ID")
    read_duration: int = Field(default=0, description="Reading time in seconds")
    read_at: Optional[datetime] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    enclosure_url: Optional[str] = Field(default=None, description="Media attachment URL")
    enclosure_type: Optional[str] = Field(default=None, description="Media type")
    word_count: Optional[int] = Field(default=None)
    hash: Optional[str] = Field(default=None, description="Content hash for deduplication")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "project_name": "tech-news",
                "title": "New AI Breakthrough",
                "link": "https://example.com/article",
                "description": "Summary of the article",
                "status": "unread",
                "is_permanent": False
            }
        }


class RSSFeedEntry(BaseModel):
    """Raw RSS entry from feedparser"""
    title: str
    link: str
    description: Optional[str] = None
    published: Optional[datetime] = None
    author: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    enclosure_url: Optional[str] = None
    enclosure_type: Optional[str] = None


# Request/Response Models

class RSSProjectCreateRequest(BaseModel):
    """Create RSS project request"""
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., description="RSS feed URL")
    enabled: bool = Field(default=True)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None)


class RSSProjectUpdateRequest(BaseModel):
    """Update RSS project request"""
    url: Optional[str] = Field(default=None)
    enabled: Optional[bool] = Field(default=None)
    description: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)


class RSSProjectResponse(BaseModel):
    """RSS project response"""
    name: str
    url: str
    enabled: bool
    description: Optional[str]
    icon: Optional[str]
    last_fetch_at: Optional[datetime]
    fetch_count: int
    item_count: int
    error_count: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class RSSItemListRequest(BaseModel):
    """List RSS items request"""
    project_name: Optional[str] = Field(default=None)
    status: Optional[RSSItemStatus] = Field(default=None)
    is_permanent: Optional[bool] = Field(default=None)
    extracted: Optional[bool] = Field(default=None)
    search: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="fetched_at")
    sort_order: str = Field(default="desc")
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            return 'desc'
        return v


class RSSItemUpdateRequest(BaseModel):
    """Update RSS item request"""
    status: Optional[RSSItemStatus] = Field(default=None)
    is_permanent: Optional[bool] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    read_duration: Optional[int] = Field(default=None)


class RSSItemResponse(BaseModel):
    """RSS item response"""
    id: str = Field(alias="_id")
    project_name: str
    title: str
    link: str
    description: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    fetched_at: datetime
    status: RSSItemStatus
    is_permanent: bool
    extracted: bool
    extraction_doc_id: Optional[str]
    read_duration: int
    read_at: Optional[datetime]
    tags: List[str]
    categories: List[str]
    word_count: Optional[int]
    
    class Config:
        populate_by_name = True


class RSSItemDetailResponse(RSSItemResponse):
    """RSS item detail with content"""
    content: Optional[str]
    enclosure_url: Optional[str]
    enclosure_type: Optional[str]


class RSSFetchRequest(BaseModel):
    """Manual fetch request"""
    project_name: Optional[str] = Field(default=None, description="Specific project or all if None")


class RSSFetchResult(BaseModel):
    """Single project fetch result"""
    project_name: str
    success: bool
    new_items: int
    updated_items: int
    error: Optional[str] = None
    duration_ms: int


class RSSFetchResponse(BaseModel):
    """Fetch operation response"""
    success: bool
    results: List[RSSFetchResult]
    total_new: int
    total_updated: int
    duration_ms: int


class RSSExtractRequest(BaseModel):
    """Extract RSS item to knowledge base"""
    model: Optional[str] = Field(default=None, description="Virtual model to use for extraction")


class RSSExtractResponse(BaseModel):
    """Extract operation response"""
    success: bool
    document_id: Optional[str] = None
    chunks_count: Optional[int] = None
    message: str


class RSSStats(BaseModel):
    """RSS statistics"""
    total_projects: int
    active_projects: int
    total_items: int
    unread_items: int
    reading_items: int
    read_items: int
    extracted_items: int
    archived_items: int
    permanent_items: int
    temporary_items: int
    today_items: int
    week_items: int
    
    # Per-project stats
    projects: List[Dict[str, Any]]
    
    # Timeline data
    timeline: List[Dict[str, Any]]  # Items per day for last 30 days


class RSSReadRequest(BaseModel):
    """Mark as read request"""
    duration: Optional[int] = Field(default=None, description="Reading duration in seconds")


class RSSBatchRequest(BaseModel):
    """Batch operation request"""
    item_ids: List[str]
    operation: str = Field(..., description="read, archive, delete, extract, permanent")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        allowed = ['read', 'archive', 'delete', 'extract', 'permanent', 'unpermanent']
        if v not in allowed:
            raise ValueError(f"Operation must be one of {allowed}")
        return v


class RSSBatchResponse(BaseModel):
    """Batch operation response"""
    success: bool
    processed: int
    failed: int
    message: str


class RSSSearchRequest(BaseModel):
    """Search RSS items"""
    query: str = Field(..., min_length=1)
    project_name: Optional[str] = Field(default=None)
    status: Optional[RSSItemStatus] = Field(default=None)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class RSSSearchResponse(BaseModel):
    """Search response"""
    items: List[RSSItemResponse]
    total: int
    page: int
    page_size: int
