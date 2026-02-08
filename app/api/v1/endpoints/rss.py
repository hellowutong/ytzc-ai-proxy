"""
RSS API Endpoints
Handles RSS feed management, fetching, reading, and knowledge extraction
Reference FOLO design for long-term memory vs timeliness
"""

import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.config_manager import get_config_manager
from core.exceptions import NotFoundException, ValidationException
from core.logger import DualLogger as Logger
from db.mongodb import get_database
from models.rss import (
    RSSBatchRequest,
    RSSBatchResponse,
    RSSExtractRequest,
    RSSExtractResponse,
    RSSFeedEntry,
    RSSFetchRequest,
    RSSFetchResponse,
    RSSFetchResult,
    RSSItem,
    RSSItemDetailResponse,
    RSSItemListRequest,
    RSSItemResponse,
    RSSItemStatus,
    RSSItemUpdateRequest,
    RSSProject,
    RSSProjectCreateRequest,
    RSSProjectResponse,
    RSSProjectUpdateRequest,
    RSSReadRequest,
    RSSSearchRequest,
    RSSSearchResponse,
    RSSStats,
)

router = APIRouter()
logger = Logger("rss")


# Helper functions

def normalize_url(url: str) -> str:
    """Normalize URL for comparison"""
    return url.strip().rstrip('/').lower()


def generate_item_hash(title: str, link: str, published: Optional[datetime] = None) -> str:
    """Generate unique hash for RSS item"""
    content = f"{title}:{link}:{published.isoformat() if published else ''}"
    return hashlib.md5(content.encode()).hexdigest()


def parse_feed_entry(entry: Dict[str, Any]) -> RSSFeedEntry:
    """Parse feedparser entry to RSSFeedEntry"""
    # Extract published date
    published = None
    if 'published_parsed' in entry and entry['published_parsed']:
        try:
            published = datetime(*entry['published_parsed'][:6])
        except:
            pass
    elif 'updated_parsed' in entry and entry['updated_parsed']:
        try:
            published = datetime(*entry['updated_parsed'][:6])
        except:
            pass
    
    # Extract content
    content = None
    if 'content' in entry and entry['content']:
        content = entry['content'][0].get('value', '')
    elif 'summary_detail' in entry and entry['summary_detail']:
        content = entry['summary_detail'].get('value', '')
    elif 'summary' in entry:
        content = entry['summary']
    
    # Extract tags
    tags = []
    if 'tags' in entry and entry['tags']:
        tags = [tag.get('term', '') for tag in entry['tags'] if tag.get('term')]
    
    # Extract enclosure
    enclosure_url = None
    enclosure_type = None
    if 'enclosures' in entry and entry['enclosures']:
        enc = entry['enclosures'][0]
        enclosure_url = enc.get('href')
        enclosure_type = enc.get('type')
    elif 'media_content' in entry and entry['media_content']:
        enc = entry['media_content'][0]
        enclosure_url = enc.get('url')
        enclosure_type = enc.get('type')
    
    return RSSFeedEntry(
        title=entry.get('title', 'Untitled'),
        link=entry.get('link', ''),
        description=entry.get('summary', None),
        published=published,
        author=entry.get('author', None),
        content=content,
        tags=tags,
        enclosure_url=enclosure_url,
        enclosure_type=enclosure_type
    )


async def fetch_single_feed(
    project: RSSProject,
    db: AsyncIOMotorDatabase
) -> RSSFetchResult:
    """Fetch a single RSS feed"""
    start_time = time.time()
    new_items = 0
    updated_items = 0
    error_msg = None
    
    try:
        # Import feedparser here to avoid startup overhead
        import feedparser
        
        # Fetch feed
        feed = feedparser.parse(project.url)
        
        if feed.bozo and hasattr(feed, 'bozo_exception'):
            error_msg = str(feed.bozo_exception)
        
        items_collection = db.rss_items
        
        for entry in feed.entries:
            try:
                parsed = parse_feed_entry(entry)
                
                # Generate hash for deduplication
                item_hash = generate_item_hash(
                    parsed.title, 
                    parsed.link, 
                    parsed.published
                )
                
                # Check if item exists
                existing = await items_collection.find_one({
                    "project_name": project.name,
                    "$or": [
                        {"hash": item_hash},
                        {"link": parsed.link}
                    ]
                })
                
                # Calculate word count
                word_count = None
                if parsed.content:
                    word_count = len(parsed.content.split())
                elif parsed.description:
                    word_count = len(parsed.description.split())
                
                item_data = {
                    "project_name": project.name,
                    "title": parsed.title,
                    "link": parsed.link,
                    "description": parsed.description,
                    "content": parsed.content,
                    "author": parsed.author,
                    "published_at": parsed.published,
                    "fetched_at": datetime.utcnow(),
                    "status": RSSItemStatus.UNREAD.value,
                    "is_permanent": config_manager.config.get("ai-gateway", {}).get("rss", {}).get("default_permanent", False),
                    "extracted": False,
                    "tags": parsed.tags,
                    "enclosure_url": parsed.enclosure_url,
                    "enclosure_type": parsed.enclosure_type,
                    "word_count": word_count,
                    "hash": item_hash
                }
                
                if existing:
                    # Update existing item
                    await items_collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {
                            "title": parsed.title,
                            "description": parsed.description,
                            "content": parsed.content,
                            "fetched_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    updated_items += 1
                else:
                    # Insert new item
                    await items_collection.insert_one(item_data)
                    new_items += 1
                    
            except Exception as e:
                logger.warning(f"Failed to process entry in {project.name}: {e}")
                continue
        
        # Update project stats
        total_items = await items_collection.count_documents({"project_name": project.name})
        await db.rss_projects.update_one(
            {"name": project.name},
            {"$set": {
                "last_fetch_at": datetime.utcnow(),
                "fetch_count": project.fetch_count + 1,
                "item_count": total_items,
                "error_count": 0 if not error_msg else project.error_count + 1,
                "last_error": error_msg,
                "updated_at": datetime.utcnow()
            }}
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Fetched {project.name}: {new_items} new, {updated_items} updated",
            extra={
                "project": project.name,
                "new_items": new_items,
                "updated_items": updated_items,
                "duration_ms": duration_ms
            }
        )
        
        return RSSFetchResult(
            project_name=project.name,
            success=True,
            new_items=new_items,
            updated_items=updated_items,
            error=error_msg,
            duration_ms=duration_ms
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
        # Update project error stats
        await db.rss_projects.update_one(
            {"name": project.name},
            {"$set": {
                "error_count": project.error_count + 1,
                "last_error": error_msg,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.error(
            f"Failed to fetch {project.name}: {e}",
            extra={"project": project.name, "error": error_msg}
        )
        
        return RSSFetchResult(
            project_name=project.name,
            success=False,
            new_items=0,
            updated_items=0,
            error=error_msg,
            duration_ms=duration_ms
        )


async def fetch_feeds_background(
    project_name: Optional[str] = None
):
    """Background task to fetch RSS feeds"""
    try:
        from db.mongodb import get_database
        db = get_database()
        
        # Get enabled projects
        query = {"enabled": True}
        if project_name:
            query["name"] = project_name
        
        cursor = db.rss_projects.find(query)
        projects = [RSSProject(**doc) async for doc in cursor]
        
        if not projects:
            logger.info("No enabled RSS projects to fetch")
            return
        
        # Limit concurrent fetches
        max_concurrent = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_limit(project: RSSProject):
            async with semaphore:
                return await fetch_single_feed(project, db)
        
        # Fetch all feeds concurrently
        tasks = [fetch_with_limit(p) for p in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_new = sum(r.new_items for r in results if isinstance(r, RSSFetchResult))
        total_updated = sum(r.updated_items for r in results if isinstance(r, RSSFetchResult))
        
        logger.info(
            f"Background RSS fetch completed: {total_new} new, {total_updated} updated",
            extra={"total_new": total_new, "total_updated": total_updated}
        )
        
    except Exception as e:
        logger.error(f"Background RSS fetch failed: {e}")


# API Endpoints

@router.get("/rss/projects", response_model=List[RSSProjectResponse])
async def list_rss_projects(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all RSS projects from config and DB"""
    try:
        # Get projects from config
        config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
        config_names = {p["name"] for p in config_projects}
        
        # Get projects from DB
        db_projects = {}
        async for doc in db.rss_projects.find():
            db_projects[doc["name"]] = doc
        
        # Merge and return
        results = []
        for cp in config_projects:
            name = cp["name"]
            db_data = db_projects.get(name, {})
            
            project_data = {
                "name": name,
                "url": cp.get("url", db_data.get("url", "")),
                "enabled": cp.get("enabled", db_data.get("enabled", True)),
                "description": db_data.get("description"),
                "icon": db_data.get("icon"),
                "last_fetch_at": db_data.get("last_fetch_at"),
                "fetch_count": db_data.get("fetch_count", 0),
                "item_count": db_data.get("item_count", 0),
                "error_count": db_data.get("error_count", 0),
                "last_error": db_data.get("last_error"),
                "created_at": db_data.get("created_at", datetime.utcnow()),
                "updated_at": db_data.get("updated_at", datetime.utcnow())
            }
            results.append(RSSProjectResponse(**project_data))
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to list RSS projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/projects", response_model=RSSProjectResponse)
async def create_rss_project(
    request: RSSProjectCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create new RSS project
    NOTE: This creates runtime data only. To add to config.yml, edit the file manually.
    """
    try:
        # Check if exists
        existing = await db.rss_projects.find_one({"name": request.name})
        if existing:
            raise ValidationException(f"Project '{request.name}' already exists")
        
        # Create project
        project = RSSProject(
            name=request.name,
            url=request.url,
            enabled=request.enabled,
            description=request.description,
            icon=request.icon
        )
        
        await db.rss_projects.insert_one(project.model_dump())
        
        logger.info(f"Created RSS project: {request.name}")
        
        return RSSProjectResponse(**project.model_dump())
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Failed to create RSS project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss/projects/{name}", response_model=RSSProjectResponse)
async def get_rss_project(
    name: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get RSS project details"""
    try:
        # Get from config
        config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
        config_project = next((p for p in config_projects if p["name"] == name), None)
        
        if not config_project:
            raise NotFoundException(f"Project '{name}' not found in config")
        
        # Get from DB
        db_project = await db.rss_projects.find_one({"name": name}) or {}
        
        project_data = {
            "name": name,
            "url": config_project.get("url", db_project.get("url", "")),
            "enabled": config_project.get("enabled", db_project.get("enabled", True)),
            "description": db_project.get("description"),
            "icon": db_project.get("icon"),
            "last_fetch_at": db_project.get("last_fetch_at"),
            "fetch_count": db_project.get("fetch_count", 0),
            "item_count": db_project.get("item_count", 0),
            "error_count": db_project.get("error_count", 0),
            "last_error": db_project.get("last_error"),
            "created_at": db_project.get("created_at", datetime.utcnow()),
            "updated_at": db_project.get("updated_at", datetime.utcnow())
        }
        
        return RSSProjectResponse(**project_data)
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    except Exception as e:
        logger.error(f"Failed to get RSS project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rss/projects/{name}", response_model=RSSProjectResponse)
async def update_rss_project(
    name: str,
    request: RSSProjectUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update RSS project metadata
    NOTE: URL/enabled changes require editing config.yml
    """
    try:
        project = await db.rss_projects.find_one({"name": name})
        if not project:
            # Create if not exists
            config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
            config_project = next((p for p in config_projects if p["name"] == name), None)
            
            if not config_project:
                raise NotFoundException(f"Project '{name}' not found")
            
            new_project = RSSProject(
                name=name,
                url=config_project.get("url", ""),
                enabled=config_project.get("enabled", True)
            )
            await db.rss_projects.insert_one(new_project.model_dump())
            project = new_project.model_dump()
        
        # Update fields
        updates = {}
        if request.description is not None:
            updates["description"] = request.description
        if request.icon is not None:
            updates["icon"] = request.icon
        
        if updates:
            updates["updated_at"] = datetime.utcnow()
            await db.rss_projects.update_one(
                {"name": name},
                {"$set": updates}
            )
            project.update(updates)
        
        # Get config data
        config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
        config_project = next((p for p in config_projects if p["name"] == name), {})
        
        project_data = {
            "name": name,
            "url": config_project.get("url", project.get("url", "")),
            "enabled": config_project.get("enabled", project.get("enabled", True)),
            "description": project.get("description"),
            "icon": project.get("icon"),
            "last_fetch_at": project.get("last_fetch_at"),
            "fetch_count": project.get("fetch_count", 0),
            "item_count": project.get("item_count", 0),
            "error_count": project.get("error_count", 0),
            "last_error": project.get("last_error"),
            "created_at": project.get("created_at", datetime.utcnow()),
            "updated_at": project.get("updated_at", datetime.utcnow())
        }
        
        return RSSProjectResponse(**project_data)
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    except Exception as e:
        logger.error(f"Failed to update RSS project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/fetch", response_model=RSSFetchResponse)
async def fetch_rss_feeds(
    request: RSSFetchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Manually trigger RSS fetch"""
    try:
        start_time = time.time()
        
        # Get enabled projects
        query = {"enabled": True}
        if request.project_name:
            query["name"] = request.project_name
        
        cursor = db.rss_projects.find(query)
        projects = [RSSProject(**doc) async for doc in cursor]
        
        if not projects and request.project_name:
            # Check config
            config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
            config_project = next((p for p in config_projects if p["name"] == request.project_name), None)
            
            if config_project and config_project.get("enabled", True):
                # Create DB entry and fetch
                new_project = RSSProject(
                    name=config_project["name"],
                    url=config_project["url"],
                    enabled=True
                )
                await db.rss_projects.insert_one(new_project.model_dump())
                projects = [new_project]
        
        if not projects:
            raise ValidationException("No enabled RSS projects found")
        
        # Fetch feeds concurrently
        max_concurrent = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_limit(project: RSSProject):
            async with semaphore:
                return await fetch_single_feed(project, db)
        
        tasks = [fetch_with_limit(p) for p in projects]
        results = await asyncio.gather(*tasks)
        
        total_new = sum(r.new_items for r in results)
        total_updated = sum(r.updated_items for r in results)
        duration_ms = int((time.time() - start_time) * 1000)
        
        success = any(r.success for r in results)
        
        logger.info(
            f"Manual RSS fetch completed: {total_new} new, {total_updated} updated",
            extra={"total_new": total_new, "total_updated": total_updated}
        )
        
        return RSSFetchResponse(
            success=success,
            results=list(results),
            total_new=total_new,
            total_updated=total_updated,
            duration_ms=duration_ms
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch RSS feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss/items", response_model=List[RSSItemResponse])
async def list_rss_items(
    project_name: Optional[str] = None,
    status: Optional[str] = None,
    is_permanent: Optional[bool] = None,
    extracted: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="fetched_at"),
    sort_order: str = Query(default="desc"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List RSS items with filters"""
    try:
        # Build query
        query = {}
        
        if project_name:
            query["project_name"] = project_name
        if status:
            query["status"] = status
        if is_permanent is not None:
            query["is_permanent"] = is_permanent
        if extracted is not None:
            query["extracted"] = extracted
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]
        
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        sort_field = sort_by if sort_by in ["fetched_at", "published_at", "title", "status"] else "fetched_at"
        
        # Query items
        cursor = db.rss_items.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(RSSItemResponse(**doc))
        
        return items
        
    except Exception as e:
        logger.error(f"Failed to list RSS items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss/items/{item_id}", response_model=RSSItemDetailResponse)
async def get_rss_item(
    item_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get RSS item details"""
    try:
        from bson import ObjectId
        
        item = await db.rss_items.find_one({"_id": ObjectId(item_id)})
        if not item:
            raise NotFoundException(f"Item '{item_id}' not found")
        
        item["_id"] = str(item["_id"])
        return RSSItemDetailResponse(**item)
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    except Exception as e:
        logger.error(f"Failed to get RSS item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rss/items/{item_id}", response_model=RSSItemResponse)
async def update_rss_item(
    item_id: str,
    request: RSSItemUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update RSS item"""
    try:
        from bson import ObjectId
        
        item = await db.rss_items.find_one({"_id": ObjectId(item_id)})
        if not item:
            raise NotFoundException(f"Item '{item_id}' not found")
        
        updates = {}
        if request.status is not None:
            updates["status"] = request.status.value
            if request.status == RSSItemStatus.READ and not item.get("read_at"):
                updates["read_at"] = datetime.utcnow()
        if request.is_permanent is not None:
            updates["is_permanent"] = request.is_permanent
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.read_duration is not None:
            updates["read_duration"] = request.read_duration
        
        if updates:
            updates["updated_at"] = datetime.utcnow()
            await db.rss_items.update_one(
                {"_id": ObjectId(item_id)},
                {"$set": updates}
            )
            item.update(updates)
        
        item["_id"] = str(item["_id"])
        return RSSItemResponse(**item)
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    except Exception as e:
        logger.error(f"Failed to update RSS item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/items/{item_id}/read", response_model=RSSItemResponse)
async def mark_as_read(
    item_id: str,
    request: RSSReadRequest = RSSReadRequest(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark RSS item as read"""
    try:
        from bson import ObjectId
        
        updates = {
            "status": RSSItemStatus.READ.value,
            "read_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if request.duration:
            updates["read_duration"] = request.duration
        
        result = await db.rss_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise NotFoundException(f"Item '{item_id}' not found")
        
        item = await db.rss_items.find_one({"_id": ObjectId(item_id)})
        item["_id"] = str(item["_id"])
        
        return RSSItemResponse(**item)
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    except Exception as e:
        logger.error(f"Failed to mark item as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/items/{item_id}/extract", response_model=RSSExtractResponse)
async def extract_to_knowledge(
    item_id: str,
    request: RSSExtractRequest = RSSExtractRequest(),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Extract RSS item to knowledge base"""
    try:
        from bson import ObjectId
        from api.v1.endpoints.knowledge import process_extraction_background
        
        item = await db.rss_items.find_one({"_id": ObjectId(item_id)})
        if not item:
            raise NotFoundException(f"Item '{item_id}' not found")
        
        if item.get("extracted") and item.get("extraction_doc_id"):
            return RSSExtractResponse(
                success=True,
                document_id=item["extraction_doc_id"],
                message="Already extracted"
            )
        
        # Get content for extraction
        content = item.get("content") or item.get("description", "")
        if not content:
            raise ValidationException("Item has no content to extract")
        
        # Create knowledge document
        from models.knowledge import Document, DocumentType, DocumentStatus
        
        doc_id = str(ObjectId())
        document = Document(
            id=doc_id,
            title=item["title"],
            content=content,
            doc_type=DocumentType.TEXT,
            source=item["link"],
            metadata={
                "rss_item_id": item_id,
                "rss_project": item["project_name"],
                "author": item.get("author"),
                "published_at": item.get("published_at").isoformat() if item.get("published_at") else None
            },
            status=DocumentStatus.PENDING,
            chunk_count=0,
            error_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert document
        doc_dict = document.model_dump(by_alias=True, exclude={"id"})
        doc_dict["_id"] = ObjectId(doc_id)
        await db.documents.insert_one(doc_dict)
        
        # Update RSS item
        await db.rss_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {
                "extracted": True,
                "extraction_doc_id": doc_id,
                "status": RSSItemStatus.EXTRACTED.value,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Trigger extraction
        try:
            await process_extraction_background(str(doc_id))
            
            # Get updated document
            updated_doc = await db.documents.find_one({"_id": ObjectId(doc_id)})
            
            return RSSExtractResponse(
                success=True,
                document_id=doc_id,
                chunks_count=updated_doc.get("chunk_count", 0) if updated_doc else 0,
                message="Extraction completed"
            )
            
        except Exception as e:
            logger.warning(f"Extraction triggered but may have failed: {e}")
            return RSSExtractResponse(
                success=True,
                document_id=doc_id,
                message="Extraction queued"
            )
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to extract RSS item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/batch", response_model=RSSBatchResponse)
async def batch_operation(
    request: RSSBatchRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Batch operation on RSS items"""
    try:
        from bson import ObjectId
        
        processed = 0
        failed = 0
        
        for item_id in request.item_ids:
            try:
                item = await db.rss_items.find_one({"_id": ObjectId(item_id)})
                if not item:
                    failed += 1
                    continue
                
                if request.operation == "read":
                    await db.rss_items.update_one(
                        {"_id": ObjectId(item_id)},
                        {"$set": {
                            "status": RSSItemStatus.READ.value,
                            "read_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }}
                    )
                
                elif request.operation == "archive":
                    await db.rss_items.update_one(
                        {"_id": ObjectId(item_id)},
                        {"$set": {
                            "status": RSSItemStatus.ARCHIVED.value,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                
                elif request.operation == "delete":
                    await db.rss_items.delete_one({"_id": ObjectId(item_id)})
                
                elif request.operation == "permanent":
                    await db.rss_items.update_one(
                        {"_id": ObjectId(item_id)},
                        {"$set": {
                            "is_permanent": True,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                
                elif request.operation == "unpermanent":
                    await db.rss_items.update_one(
                        {"_id": ObjectId(item_id)},
                        {"$set": {
                            "is_permanent": False,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                
                processed += 1
                
            except Exception as e:
                logger.warning(f"Batch operation failed for {item_id}: {e}")
                failed += 1
        
        return RSSBatchResponse(
            success=True,
            processed=processed,
            failed=failed,
            message=f"Processed {processed} items, {failed} failed"
        )
        
    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss/stats", response_model=RSSStats)
async def get_rss_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get RSS statistics"""
    try:
        # Get project stats
        config_projects = config_manager.config.get("ai-gateway", {}).get("rss", {}).get("projects", [])
        total_projects = len(config_projects)
        active_projects = sum(1 for p in config_projects if p.get("enabled", True))
        
        # Get item counts
        total_items = await db.rss_items.count_documents({})
        unread_items = await db.rss_items.count_documents({"status": RSSItemStatus.UNREAD.value})
        reading_items = await db.rss_items.count_documents({"status": RSSItemStatus.READING.value})
        read_items = await db.rss_items.count_documents({"status": RSSItemStatus.READ.value})
        extracted_items = await db.rss_items.count_documents({"status": RSSItemStatus.EXTRACTED.value})
        archived_items = await db.rss_items.count_documents({"status": RSSItemStatus.ARCHIVED.value})
        permanent_items = await db.rss_items.count_documents({"is_permanent": True})
        temporary_items = total_items - permanent_items
        
        # Today and week counts
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        today_items = await db.rss_items.count_documents({"fetched_at": {"$gte": today}})
        week_items = await db.rss_items.count_documents({"fetched_at": {"$gte": week_ago}})
        
        # Per-project stats
        project_stats = []
        for project in config_projects:
            name = project["name"]
            project_item_count = await db.rss_items.count_documents({"project_name": name})
            project_unread = await db.rss_items.count_documents({
                "project_name": name,
                "status": RSSItemStatus.UNREAD.value
            })
            
            db_project = await db.rss_projects.find_one({"name": name}) or {}
            
            project_stats.append({
                "name": name,
                "enabled": project.get("enabled", True),
                "item_count": project_item_count,
                "unread_count": project_unread,
                "last_fetch_at": db_project.get("last_fetch_at"),
                "error_count": db_project.get("error_count", 0)
            })
        
        # Timeline (last 30 days)
        timeline = []
        for i in range(30):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = await db.rss_items.count_documents({
                "fetched_at": {"$gte": day_start, "$lt": day_end}
            })
            timeline.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count
            })
        timeline.reverse()
        
        return RSSStats(
            total_projects=total_projects,
            active_projects=active_projects,
            total_items=total_items,
            unread_items=unread_items,
            reading_items=reading_items,
            read_items=read_items,
            extracted_items=extracted_items,
            archived_items=archived_items,
            permanent_items=permanent_items,
            temporary_items=temporary_items,
            today_items=today_items,
            week_items=week_items,
            projects=project_stats,
            timeline=timeline
        )
        
    except Exception as e:
        logger.error(f"Failed to get RSS stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/search", response_model=RSSSearchResponse)
async def search_rss_items(
    request: RSSSearchRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search RSS items"""
    try:
        # Build query
        query = {
            "$or": [
                {"title": {"$regex": request.query, "$options": "i"}},
                {"description": {"$regex": request.query, "$options": "i"}},
                {"content": {"$regex": request.query, "$options": "i"}},
                {"tags": {"$in": [request.query]}}
            ]
        }
        
        if request.project_name:
            query["project_name"] = request.project_name
        if request.status:
            query["status"] = request.status.value
        
        # Count total
        total = await db.rss_items.count_documents(query)
        
        # Get items
        skip = (request.page - 1) * request.page_size
        cursor = db.rss_items.find(query).sort("fetched_at", -1).skip(skip).limit(request.page_size)
        
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(RSSItemResponse(**doc))
        
        return RSSSearchResponse(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to search RSS items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rss/items/{item_id}")
async def delete_rss_item(
    item_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete RSS item"""
    try:
        from bson import ObjectId
        
        result = await db.rss_items.delete_one({"_id": ObjectId(item_id)})
        
        if result.deleted_count == 0:
            raise NotFoundException(f"Item '{item_id}' not found")
        
        logger.info(f"Deleted RSS item: {item_id}")
        
        return {"success": True, "message": "Item deleted"}
        
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    except Exception as e:
        logger.error(f"Failed to delete RSS item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/cleanup")
async def cleanup_old_items(
    days: int = Query(default=30, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Clean up old temporary RSS items"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old non-permanent items
        result = await db.rss_items.delete_many({
            "is_permanent": False,
            "fetched_at": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        
        logger.info(f"Cleaned up {deleted_count} old RSS items")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} items older than {days} days"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup RSS items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
