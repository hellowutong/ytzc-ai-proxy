"""
Media processing API endpoints for video, audio, and text files.

Features:
- Media file upload/download
- URL download
- Whisper transcription
- Integration with knowledge extraction
"""

import asyncio
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from core.config_manager import get_config
from core.logger import get_logger
from db.mongodb import get_mongodb_client
from models.media import (
    DownloadUrlRequest,
    DownloadUrlResponse,
    MediaCreateRequest,
    MediaFile,
    MediaListRequest,
    MediaListResponse,
    MediaStats,
    MediaStatus,
    MediaType,
    MediaUpdateRequest,
    MediaUploadResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionResult,
    TranscriptionSegment,
)

router = APIRouter(prefix="/media", tags=["Media Processing"])
logger = get_logger("media_api")

# Upload directories
UPLOAD_BASE = Path("./uploads")
VIDEO_DIR = UPLOAD_BASE / "video"
AUDIO_DIR = UPLOAD_BASE / "audio"
TEXT_DIR = UPLOAD_BASE / "text"

for dir_path in [VIDEO_DIR, AUDIO_DIR, TEXT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# File extension mappings
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".wma"}
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".doc", ".docx", ".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}

CONTENT_TYPE_MAP = {
    **{ext: MediaType.VIDEO for ext in VIDEO_EXTENSIONS},
    **{ext: MediaType.AUDIO for ext in AUDIO_EXTENSIONS},
    **{ext: MediaType.TEXT for ext in TEXT_EXTENSIONS},
    **{ext: MediaType.IMAGE for ext in IMAGE_EXTENSIONS},
}


def get_media_type(filename: str) -> MediaType:
    """Determine media type from file extension."""
    ext = Path(filename).suffix.lower()
    return CONTENT_TYPE_MAP.get(ext, MediaType.TEXT)


def get_upload_dir(media_type: MediaType) -> Path:
    """Get upload directory for media type."""
    if media_type == MediaType.VIDEO:
        return VIDEO_DIR
    elif media_type == MediaType.AUDIO:
        return AUDIO_DIR
    else:
        return TEXT_DIR


def get_allowed_extensions(media_type: MediaType) -> set:
    """Get allowed file extensions for media type."""
    if media_type == MediaType.VIDEO:
        return VIDEO_EXTENSIONS
    elif media_type == MediaType.AUDIO:
        return AUDIO_EXTENSIONS
    elif media_type == MediaType.TEXT:
        return TEXT_EXTENSIONS
    elif media_type == MediaType.IMAGE:
        return IMAGE_EXTENSIONS
    return set()


async def save_media_file(upload_file: UploadFile, media_id: str, media_type: MediaType) -> tuple[str, int]:
    """Save uploaded media file and return path and size."""
    upload_dir = get_upload_dir(media_type)
    file_ext = Path(upload_file.filename or "unknown").suffix
    file_path = upload_dir / f"{media_id}{file_ext}"
    
    content = await upload_file.read()
    file_size = len(content)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return str(file_path), file_size


async def get_video_duration(file_path: str) -> Optional[float]:
    """Get video/audio duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
            logger.warning(f"Failed to get duration: {e}")
    return None


async def split_media_file(file_path: str, split_count: int) -> List[str]:
    """
    Split media file into multiple parts using ffmpeg.
    
    Args:
        file_path: Path to the media file
        split_count: Number of parts to split into
    
    Returns:
        List of paths to split files
    """
    if split_count <= 1:
        return [file_path]
    
    try:
        # Get file duration
        duration = await get_video_duration(file_path)
        if not duration or duration <= 0:
            logger.warning(f"Could not determine duration for {file_path}")
            return [file_path]
        
        # Calculate segment duration
        segment_duration = duration / split_count
        
        # Prepare output files
        input_ext = Path(file_path).suffix
        base_path = file_path.replace(input_ext, "")
        output_files = []
        
        # Split using ffmpeg
        for i in range(split_count):
            start_time = i * segment_duration
            output_file = f"{base_path}_part{i + 1}{input_ext}"
            
            # Use ffmpeg to extract segment
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-i", file_path,
                "-ss", str(start_time),
                "-t", str(segment_duration),
                "-c", "copy",  # Copy codec (fast, no re-encoding)
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout per segment
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                output_files.append(output_file)
                logger.info(f"Created segment {i + 1}/{split_count}: {output_file}")
            else:
                logger.error(f"Failed to create segment {i + 1}: {result.stderr}")
                # Clean up created segments on failure
                for f in output_files:
                    if os.path.exists(f):
                        os.remove(f)
                return [file_path]  # Fallback to original
        
        logger.info(f"Split {file_path} into {len(output_files)} segments")
        return output_files
        
    except Exception as e:
        logger.error(f"File splitting failed: {e}")
        return [file_path]  # Fallback to original


async def download_file_from_url(
    url: str,
    media_id: str,
    media_type: MediaType,
    timeout: int = 300,
) -> tuple[str, int]:
    """Download file from URL and save to upload directory."""
    upload_dir = get_upload_dir(media_type)
    
    # Determine file extension from URL
    parsed = urlparse(url)
    path = parsed.path
    file_ext = Path(path).suffix or ".bin"
    file_path = upload_dir / f"{media_id}{file_ext}"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        content = response.content
        file_size = len(content)
        
        with open(file_path, "wb") as f:
            f.write(content)
    
    return str(file_path), file_size


async def transcribe_with_whisper(
    file_path: str,
    language: str = "zh",
    model: str = "base",
    split: int = 1,
) -> TranscriptionResult:
    """
    Transcribe audio/video using Whisper.
    
    For large files, splits into segments and transcribes each.
    """
    start_time = time.time()
    
    try:
        # Check if whisper is available
        import whisper
        
        # Load model (cached after first load)
        logger.info(f"Loading Whisper model: {model}")
        whisper_model = whisper.load_model(model)
        
        # Get file size for splitting decision
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # If splitting is enabled and file is large
        if split > 1 and file_size_mb > 50:
            logger.info(f"Large file detected ({file_size_mb:.1f}MB), splitting into {split} parts")
            # Split the file and transcribe each part
            split_files = await split_media_file(file_path, split)
            
            if len(split_files) > 1:
                # Transcribe each segment and combine results
                all_segments = []
                total_duration = 0
                
                for idx, split_file in enumerate(split_files):
                    logger.info(f"Transcribing segment {idx + 1}/{len(split_files)}: {split_file}")
                    segment_result = whisper_model.transcribe(
                        split_file,
                        language=language if language != "auto" else None,
                        verbose=False,
                    )
                    
                    # Adjust segment timestamps
                    for seg in segment_result.get("segments", []):
                        seg["start"] += total_duration
                        seg["end"] += total_duration
                        all_segments.append(seg)
                    
                    # Get duration of this segment
                    if segment_result.get("segments"):
                        total_duration = all_segments[-1]["end"]
                
                # Combine into final result
                result = {
                    "text": " ".join(seg.get("text", "").strip() for seg in all_segments),
                    "segments": all_segments,
                    "avg_logprob": sum(seg.get("avg_logprob", 0) for seg in all_segments) / len(all_segments) if all_segments else 0
                }
            else:
                # Fallback to single file transcription
                result = whisper_model.transcribe(
                    file_path,
                    language=language if language != "auto" else None,
                    verbose=False,
                )
        else:
            # Transcribe single file
            logger.info(f"Transcribing: {file_path}")
            result = whisper_model.transcribe(
                file_path,
                language=language if language != "auto" else None,
                verbose=False,
            )
        
        # Convert segments
        segments = []
        for idx, seg in enumerate(result.get("segments", [])):
            segment = TranscriptionSegment(
                id=f"seg_{idx}",
                start=seg.get("start", 0),
                end=seg.get("end", 0),
                text=seg.get("text", "").strip(),
                confidence=seg.get("avg_logprob", 0),
            )
            segments.append(segment)
        
        # Calculate duration
        duration = 0
        if segments:
            duration = segments[-1].end
        
        text = result.get("text", "").strip()
        word_count = len(text.split()) if text else 0
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Transcription complete: {len(segments)} segments, {word_count} words")
        
        return TranscriptionResult(
            text=text,
            language=language,
            confidence=result.get("avg_logprob", 0),
            segments=segments,
            duration=duration,
            word_count=word_count,
            processing_time_ms=processing_time_ms,
        )
    
    except ImportError:
        logger.error("Whisper not installed. Install with: pip install openai-whisper")
        raise HTTPException(
            status_code=500,
            detail="Whisper not installed. Install with: pip install openai-whisper"
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


async def process_transcription_background(
    media_id: str,
    request: TranscriptionRequest,
):
    """Background task to transcribe media and optionally extract to knowledge."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        # Get media file
        media = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not media:
            logger.error(f"Media not found: {media_id}")
            return
        
        file_path = media.get("file_path")
        if not file_path or not os.path.exists(file_path):
            await db.media_files.update_one(
                {"_id": ObjectId(media_id)},
                {
                    "$set": {
                        "status": MediaStatus.FAILED.value,
                        "status_message": "File not found",
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
            return
        
        # Update status
        await db.media_files.update_one(
            {"_id": ObjectId(media_id)},
            {
                "$set": {
                    "status": MediaStatus.TRANSCRIBING.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        # Get transcription config
        media_type = MediaType(media.get("media_type", "audio"))
        if media_type == MediaType.VIDEO:
            config_path = "ai-gateway.media.video.transcription"
        else:
            config_path = "ai-gateway.media.audio.transcription"
        
        transcription_config = get_config(config_path, {})
        
        # Use request params or defaults from config
        language = request.language or transcription_config.get("language", "zh")
        model = request.model or transcription_config.get("default_model", "base")
        split = request.split or transcription_config.get("split", 1)
        
        # Transcribe
        transcription = await transcribe_with_whisper(file_path, language, model, split)
        
        # Update media with transcription
        await db.media_files.update_one(
            {"_id": ObjectId(media_id)},
            {
                "$set": {
                    "transcription": transcription.model_dump(),
                    "transcription_model": model,
                    "status": MediaStatus.TRANSCRIBED.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        # Auto-extract to knowledge if enabled
        auto_extract = transcription_config.get("enabled", True)
        if auto_extract and transcription.text:
            await extract_to_knowledge(media_id, transcription.text)
        
        logger.info(f"Transcription complete for media: {media_id}")
    
    except Exception as e:
        logger.error(f"Background transcription failed: {e}")
        try:
            from bson.objectid import ObjectId
            db = get_mongodb_client().db
            await db.media_files.update_one(
                {"_id": ObjectId(media_id)},
                {
                    "$set": {
                        "status": MediaStatus.FAILED.value,
                        "status_message": str(e),
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
        except:
            pass


async def extract_to_knowledge(media_id: str, text: str):
    """Extract transcribed text to knowledge base."""
    try:
        from bson.objectid import ObjectId
        from models.knowledge import Document, DocumentStatus, DocumentType
        
        db = get_mongodb_client().db
        
        # Get media
        media = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not media:
            return
        
        # Create knowledge document
        doc = Document(
            title=f"[Transcription] {media.get('title', 'Untitled')}",
            content_type=DocumentType.TEXT,
            content=text,
            file_size=len(text.encode("utf-8")),
            source_type="media_transcription",
            source_url=media.get("source_url"),
            status=DocumentStatus.EXTRACTED,
            word_count=len(text.split()),
        )
        
        result = await db.documents.insert_one(doc.model_dump(exclude={"id"}, by_alias=True))
        doc_id = str(result.inserted_id)
        
        # Update media with knowledge link
        await db.media_files.update_one(
            {"_id": ObjectId(media_id)},
            {
                "$set": {
                    "knowledge_document_id": doc_id,
                    "status": MediaStatus.PROCESSED.value,
                    "processed_at": datetime.utcnow(),
                }
            }
        )
        
        logger.info(f"Extracted media {media_id} to knowledge document {doc_id}")
    
    except Exception as e:
        logger.error(f"Failed to extract to knowledge: {e}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/files", response_model=MediaListResponse)
async def list_media_files(
    media_type: Optional[MediaType] = Query(None, description="Filter by media type"),
    status: Optional[MediaStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List media files with filters and pagination."""
    try:
        db = get_mongodb_client().db
        
        # Build query
        query = {}
        if media_type:
            query["media_type"] = media_type.value
        if status:
            query["status"] = status.value
        if search:
            query["title"] = {"$regex": search, "$options": "i"}
        
        # Get total count
        total = await db.media_files.count_documents(query)
        
        # Get media files
        cursor = db.media_files.find(query).skip(skip).limit(limit).sort("created_at", -1)
        media_files = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            media_files.append(MediaFile(**doc))
        
        return MediaListResponse(
            total=total,
            media_files=media_files,
            skip=skip,
            limit=limit,
        )
    
    except Exception as e:
        logger.error(f"Failed to list media files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list media files: {str(e)}")


@router.post("/files", response_model=MediaFile)
async def create_media_record(request: MediaCreateRequest):
    """Create a new media record (without file upload)."""
    try:
        db = get_mongodb_client().db
        
        media = MediaFile(
            title=request.title,
            media_type=request.media_type,
            source_type="url" if request.source_url else "manual",
            source_url=request.source_url,
            tags=request.tags,
            custom_metadata=request.custom_metadata,
            status=MediaStatus.PENDING,
        )
        
        result = await db.media_files.insert_one(media.model_dump(exclude={"id"}, by_alias=True))
        media.id = str(result.inserted_id)
        
        logger.info(f"Created media record: {media.id}")
        return media
    
    except Exception as e:
        logger.error(f"Failed to create media record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create media record: {str(e)}")


@router.get("/files/{media_id}", response_model=MediaFile)
async def get_media_file(media_id: str):
    """Get a specific media file by ID."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        doc = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        doc["_id"] = str(doc["_id"])
        return MediaFile(**doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get media file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get media file: {str(e)}")


@router.put("/files/{media_id}", response_model=MediaFile)
async def update_media_file(media_id: str, request: MediaUpdateRequest):
    """Update media file metadata."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        # Check if exists
        existing = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Build update data
        update_data = {}
        for field, value in request.model_dump(exclude_none=True).items():
            update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.media_files.update_one(
            {"_id": ObjectId(media_id)},
            {"$set": update_data}
        )
        
        # Return updated
        doc = await db.media_files.find_one({"_id": ObjectId(media_id)})
        doc["_id"] = str(doc["_id"])
        
        logger.info(f"Updated media file: {media_id}")
        return MediaFile(**doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update media file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update media file: {str(e)}")


@router.delete("/files/{media_id}")
async def delete_media_file(media_id: str):
    """Delete a media file and its associated data."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        # Get media to find file path
        media = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not media:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Delete file if exists
        file_path = media.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from MongoDB
        await db.media_files.delete_one({"_id": ObjectId(media_id)})
        
        logger.info(f"Deleted media file: {media_id}")
        return {"success": True, "message": "Media file deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete media file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete media file: {str(e)}")


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_file(
    file: UploadFile = File(..., description="Media file to upload"),
    media_type: Optional[MediaType] = Form(None, description="Media type (auto-detected if not provided)"),
    title: Optional[str] = Form(None, description="Custom title"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    auto_transcribe: bool = Form(True, description="Auto-transcribe after upload"),
):
    """Upload a media file."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Determine media type
        detected_type = get_media_type(file.filename)
        if media_type:
            detected_type = media_type
        
        # Check allowed extensions
        ext = Path(file.filename).suffix.lower()
        allowed = get_allowed_extensions(detected_type)
        if allowed and ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(allowed)}"
            )
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)
        
        max_size_mb = get_config(f"ai-gateway.media.{detected_type.value}.upload.max_size_mb", 100)
        if file_size > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {max_size_mb}MB"
            )
        
        # Create media record
        doc_title = title or file.filename
        doc_tags = [t.strip() for t in tags.split(",")] if tags else []
        
        media = MediaFile(
            title=doc_title,
            media_type=detected_type,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type,
            tags=doc_tags,
            source_type="upload",
            status=MediaStatus.UPLOADED,
        )
        
        db = get_mongodb_client().db
        result = await db.media_files.insert_one(media.model_dump(exclude={"id"}, by_alias=True))
        media.id = str(result.inserted_id)
        
        # Save file
        file_path, _ = await save_media_file(file, media.id, detected_type)
        
        # Get duration for video/audio
        duration = None
        if detected_type in [MediaType.VIDEO, MediaType.AUDIO]:
            duration = await get_video_duration(file_path)
        
        # Update with file path and duration
        await db.media_files.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "file_path": file_path,
                    "duration": duration,
                }
            }
        )
        
        logger.info(f"Uploaded media: {file.filename} -> {media.id}")
        
        return MediaUploadResponse(
            success=True,
            media_id=media.id,
            file_name=file.filename,
            file_size=file_size,
            media_type=detected_type,
            message="File uploaded successfully",
            status=MediaStatus.UPLOADED if not auto_transcribe else MediaStatus.PENDING,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload media: {str(e)}")


@router.post("/download-url", response_model=DownloadUrlResponse)
async def download_from_url(
    request: DownloadUrlRequest,
    background_tasks: BackgroundTasks,
):
    """Download media from URL."""
    try:
        # Check if download is enabled
        config_path = f"ai-gateway.media.{request.media_type.value}.download"
        download_config = get_config(config_path, {})
        
        if not download_config.get("enabled", True):
            raise HTTPException(status_code=400, detail="URL download is disabled")
        
        # Create media record
        parsed = urlparse(request.url)
        file_name = Path(parsed.path).name or "downloaded_file"
        
        media = MediaFile(
            title=request.title or file_name,
            media_type=request.media_type,
            file_name=file_name,
            source_type="download",
            source_url=request.url,
            tags=request.tags,
            status=MediaStatus.DOWNLOADING,
        )
        
        db = get_mongodb_client().db
        result = await db.media_files.insert_one(media.model_dump(exclude={"id"}, by_alias=True))
        media.id = str(result.inserted_id)
        
        # Download in background
        background_tasks.add_task(
            download_and_process,
            media.id,
            request.url,
            request.media_type,
            request.auto_transcribe,
        )
        
        logger.info(f"Started download from URL: {request.url}")
        
        return DownloadUrlResponse(
            success=True,
            media_id=media.id,
            message="Download started",
            status=MediaStatus.DOWNLOADING,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start download: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start download: {str(e)}")


async def download_and_process(
    media_id: str,
    url: str,
    media_type: MediaType,
    auto_transcribe: bool,
):
    """Background task to download and process media."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        # Get timeout from config
        config_path = f"ai-gateway.media.{media_type.value}.download"
        download_config = get_config(config_path, {})
        timeout = download_config.get("timeout_seconds", 300)
        
        # Download
        file_path, file_size = await download_file_from_url(url, media_id, media_type, timeout)
        
        # Get duration
        duration = None
        if media_type in [MediaType.VIDEO, MediaType.AUDIO]:
            duration = await get_video_duration(file_path)
        
        # Update record
        await db.media_files.update_one(
            {"_id": ObjectId(media_id)},
            {
                "$set": {
                    "file_path": file_path,
                    "file_size": file_size,
                    "duration": duration,
                    "status": MediaStatus.UPLOADED.value,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        logger.info(f"Downloaded media: {media_id} from {url}")
        
        # Auto-transcribe if enabled
        if auto_transcribe and media_type in [MediaType.VIDEO, MediaType.AUDIO]:
            from models.media import TranscriptionRequest
            await process_transcription_background(
                media_id,
                TranscriptionRequest(),
            )
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        try:
            from bson.objectid import ObjectId
            db = get_mongodb_client().db
            await db.media_files.update_one(
                {"_id": ObjectId(media_id)},
                {
                    "$set": {
                        "status": MediaStatus.FAILED.value,
                        "status_message": str(e),
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
        except:
            pass


@router.post("/files/{media_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_media(
    media_id: str,
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
):
    """Start transcription for a media file."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        # Get media
        media = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not media:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Check if transcribable
        media_type = MediaType(media.get("media_type", "audio"))
        if media_type not in [MediaType.VIDEO, MediaType.AUDIO]:
            raise HTTPException(status_code=400, detail="Only video and audio files can be transcribed")
        
        # Start transcription in background
        background_tasks.add_task(process_transcription_background, media_id, request)
        
        logger.info(f"Started transcription for media: {media_id}")
        
        return TranscriptionResponse(
            success=True,
            media_id=media_id,
            transcription=None,
            message="Transcription started in background",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")


@router.get("/files/{media_id}/download")
async def download_media_file(media_id: str):
    """Download the original media file."""
    try:
        from bson.objectid import ObjectId
        db = get_mongodb_client().db
        
        media = await db.media_files.find_one({"_id": ObjectId(media_id)})
        if not media:
            raise HTTPException(status_code=404, detail="Media file not found")
        
        file_path = media.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=file_path,
            filename=media.get("file_name", "download"),
            media_type=media.get("mime_type", "application/octet-stream"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download media: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/stats", response_model=MediaStats)
async def get_media_stats():
    """Get media library statistics."""
    try:
        db = get_mongodb_client().db
        
        # Total files
        total = await db.media_files.count_documents({})
        
        # By type
        by_type = {}
        for mtype in MediaType:
            count = await db.media_files.count_documents({"media_type": mtype.value})
            by_type[mtype.value] = count
        
        # By status
        by_status = {}
        for status in MediaStatus:
            count = await db.media_files.count_documents({"status": status.value})
            by_status[status.value] = count
        
        # Total duration
        pipeline = [
            {"$match": {"duration": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "total": {"$sum": "$duration"}}}
        ]
        duration_result = await db.media_files.aggregate(pipeline).to_list(1)
        total_duration = duration_result[0]["total"] if duration_result else 0
        
        # Counts
        transcribed_count = await db.media_files.count_documents({
            "transcription": {"$exists": True}
        })
        pending_count = await db.media_files.count_documents({"status": MediaStatus.PENDING.value})
        failed_count = await db.media_files.count_documents({"status": MediaStatus.FAILED.value})
        
        return MediaStats(
            total_files=total,
            by_type=by_type,
            by_status=by_status,
            total_duration=total_duration,
            transcribed_count=transcribed_count,
            pending_count=pending_count,
            failed_count=failed_count,
        )
    
    except Exception as e:
        logger.error(f"Failed to get media stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
