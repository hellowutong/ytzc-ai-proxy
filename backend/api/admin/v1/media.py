"""
媒体处理队列API
"""

import json
import logging
from datetime import datetime
from typing import Optional, Literal, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel

from api.dependencies import get_media_processor
from core.media_processor import MediaProcessor

logger = logging.getLogger(__name__)

router = APIRouter()


class MediaFile(BaseModel):
    id: str
    filename: str
    type: Literal["video", "audio", "text"]
    size: int
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int
    created_at: str


class UploadConfig(BaseModel):
    processor: str = "whisper"
    model: str = "base"
    language: str = "zh"
    auto_transcribe: bool = True


class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio", "text"]
    config: UploadConfig = UploadConfig()


def format_media_file(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format MongoDB document to API response format"""
    upload_time = doc.get("upload_time")
    if isinstance(upload_time, datetime):
        upload_time = upload_time.isoformat()
    
    # Determine progress based on status
    status = doc.get("status", "pending")
    progress = 0
    if status == "completed":
        progress = 100
    elif status == "processing":
        # Check if there's transcription progress
        transcription = doc.get("transcription")
        if transcription and transcription.get("text"):
            progress = 100
    elif status in ["pending", "uploaded"]:
        progress = 0
    
    return {
        "id": doc.get("_id", ""),
        "filename": doc.get("filename", ""),
        "type": doc.get("type", "video"),
        "size": doc.get("file_size", 0),
        "status": status,
        "progress": progress,
        "created_at": upload_time or datetime.utcnow().isoformat()
    }


@router.get("/media")
async def get_media_files(
    type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    media_processor: MediaProcessor = Depends(get_media_processor)
):
    """获取媒体文件列表"""
    try:
        # Calculate offset from page number
        offset = (page - 1) * page_size
        
        # Call MediaProcessor
        result = await media_processor.list_media_files(
            media_type=type,
            status=status,
            limit=page_size,
            offset=offset
        )
        
        # Format response to match frontend requirements
        items = [format_media_file(doc) for doc in result.get("files", [])]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": items,
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        logger.error(f"获取媒体文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取媒体文件列表失败: {str(e)}")


@router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    type: str = Form(...),
    config: str = Form("{}"),
    media_processor: MediaProcessor = Depends(get_media_processor)
):
    """上传媒体文件"""
    try:
        # Parse config JSON
        try:
            config_obj = json.loads(config) if config else {}
        except json.JSONDecodeError:
            config_obj = {}
        
        processor = config_obj.get("processor", "whisper")
        model = config_obj.get("model", "base")
        language = config_obj.get("language", "zh")
        auto_transcribe = config_obj.get("auto_transcribe", True)
        
        # Validate media type
        if type not in ["video", "audio", "text"]:
            raise HTTPException(status_code=400, detail=f"不支持的媒体类型: {type}")
        
        # Call MediaProcessor
        result = await media_processor.upload_file(
            file=file,
            media_type=type,
            processor=processor,
            model=model,
            language=language,
            auto_transcribe=auto_transcribe
        )
        
        # Format response
        upload_time = result.get("upload_time")
        if isinstance(upload_time, datetime):
            upload_time = upload_time.isoformat()
        
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "id": result.get("id"),
                "filename": result.get("filename"),
                "type": result.get("type"),
                "size": result.get("file_size"),
                "status": result.get("status"),
                "progress": 0,
                "created_at": upload_time or datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传媒体文件失败: {str(e)}")


@router.post("/media/download")
async def download_from_url(
    body: DownloadRequest,
    media_processor: MediaProcessor = Depends(get_media_processor)
):
    """从URL下载媒体"""
    try:
        # Validate URL
        if not body.url:
            raise HTTPException(status_code=400, detail="URL不能为空")
        
        # Call MediaProcessor
        result = await media_processor.download_from_url(
            url=body.url,
            media_type=body.type,
            processor=body.config.processor,
            model=body.config.model,
            language=body.config.language,
            auto_transcribe=body.config.auto_transcribe
        )
        
        # Format response
        upload_time = result.get("upload_time")
        if isinstance(upload_time, datetime):
            upload_time = upload_time.isoformat()
        
        return {
            "code": 200,
            "message": "下载任务已提交",
            "data": {
                "id": result.get("id"),
                "filename": result.get("filename"),
                "type": result.get("type"),
                "size": result.get("file_size"),
                "status": result.get("status"),
                "progress": 0,
                "created_at": upload_time or datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载媒体文件失败: {str(e)}")


@router.delete("/media/{media_id}")
async def delete_media(
    media_id: str,
    media_processor: MediaProcessor = Depends(get_media_processor)
):
    """删除媒体文件"""
    try:
        success = await media_processor.delete_media_file(media_id)
        
        if success:
            return {
                "code": 200,
                "message": "删除成功",
                "data": None
            }
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除媒体文件失败: {str(e)}")


@router.post("/media/{media_id}/reprocess")
async def reprocess_media(
    media_id: str,
    media_processor: MediaProcessor = Depends(get_media_processor)
):
    """重新处理媒体文件"""
    try:
        # First check if media exists
        media_doc = await media_processor.get_media_status(media_id)
        if not media_doc:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # Submit transcription task
        success = await media_processor.submit_transcription_task(media_id)
        
        if success:
            return {
                "code": 200,
                "message": "重新处理任务已提交",
                "data": None
            }
        else:
            raise HTTPException(status_code=500, detail="提交任务失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新处理媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新处理媒体文件失败: {str(e)}")
