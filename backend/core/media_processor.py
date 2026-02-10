"""
媒体处理器 - 处理音视频文件的上传、转录和知识提取
"""

import os
import uuid
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import UploadFile
import redis.asyncio as redis


class MediaProcessor:
    """媒体处理器类"""
    
    def __init__(
        self,
        mongodb: AsyncIOMotorClient,
        redis_client: redis.Redis,
        whisper_service=None,
        knowledge_manager=None,
        upload_dir: str = "../upload"
    ):
        """
        初始化媒体处理器
        
        Args:
            mongodb: MongoDB客户端
            redis_client: Redis客户端
            whisper_service: Whisper服务实例
            knowledge_manager: 知识管理器实例
            upload_dir: 上传目录路径
        """
        self._mongodb = mongodb
        self._redis = redis_client
        self._whisper_service = whisper_service
        self._knowledge_manager = knowledge_manager
        self._upload_dir = Path(upload_dir)
        
        # 确保上传目录存在
        self._ensure_upload_dirs()
        
        # 数据库集合
        self._db = mongodb["ai_gateway"]
        self._collection = self._db["media_files"]
    
    def _ensure_upload_dirs(self):
        """确保上传目录结构存在"""
        for subdir in ["video", "audio", "textfile"]:
            (self._upload_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self,
        file: UploadFile,
        media_type: str,
        processor: str = "whisper",
        model: str = "base",
        language: str = "zh",
        auto_transcribe: bool = True
    ) -> Dict[str, Any]:
        """
        上传媒体文件
        
        Args:
            file: 上传的文件
            media_type: 媒体类型 (video/audio/text)
            processor: 转录处理器 (whisper)
            model: Whisper模型 (base/small/medium/large)
            language: 语言代码
            auto_transcribe: 是否自动转录
            
        Returns:
            媒体文件信息字典
        """
        # 生成唯一ID
        media_id = str(uuid.uuid4())
        
        # 确定文件扩展名
        original_filename = file.filename or "unknown"
        file_ext = Path(original_filename).suffix.lower()
        
        # 构建保存路径
        save_dir = self._upload_dir / media_type
        save_path = save_dir / f"{media_id}{file_ext}"
        
        # 保存文件
        content = await file.read()
        file_size = len(content)
        
        with open(save_path, "wb") as f:
            f.write(content)
        
        # 创建数据库记录
        media_doc = {
            "_id": media_id,
            "filename": original_filename,
            "type": media_type,
            "status": "pending" if auto_transcribe else "uploaded",
            "file_path": str(save_path),
            "file_size": file_size,
            "transcription": {
                "processor": processor,
                "model": model,
                "language": language,
                "text": None,
                "segments": [],
                "completed_at": None
            } if auto_transcribe else None,
            "knowledge_extracted": False,
            "knowledge_doc_ids": [],
            "upload_time": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self._collection.insert_one(media_doc)
        
        # 如果需要自动转录，提交到队列
        if auto_transcribe:
            await self.submit_transcription_task(media_id)
        
        return {
            "id": media_id,
            "filename": original_filename,
            "type": media_type,
            "status": media_doc["status"],
            "file_size": file_size,
            "upload_time": media_doc["upload_time"]
        }
    
    async def submit_transcription_task(self, media_id: str) -> bool:
        """
        提交转录任务到Redis队列
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            是否成功提交
        """
        try:
            # 将任务推入Redis队列
            await self._redis.lpush("queue:transcription", media_id)
            
            # 更新状态为pending
            await self._collection.update_one(
                {"_id": media_id},
                {
                    "$set": {
                        "status": "pending",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
        except Exception as e:
            print(f"提交转录任务失败: {e}")
            return False
    
    async def process_transcription(self, media_id: str) -> Dict[str, Any]:
        """
        处理转录任务（由工作进程调用）
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            转录结果
        """
        # 获取媒体文件信息
        media_doc = await self._collection.find_one({"_id": media_id})
        if not media_doc:
            raise ValueError(f"媒体文件不存在: {media_id}")
        
        # 更新状态为processing
        await self._collection.update_one(
            {"_id": media_id},
            {
                "$set": {
                    "status": "processing",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        try:
            # 调用Whisper服务进行转录
            if not self._whisper_service:
                raise RuntimeError("Whisper服务未配置")
            
            transcription_config = media_doc.get("transcription", {})
            result = await self._whisper_service.transcribe(
                file_path=media_doc["file_path"],
                model=transcription_config.get("model", "base"),
                language=transcription_config.get("language", "zh")
            )
            
            # 更新转录结果
            transcription_data = {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "completed_at": datetime.utcnow()
            }
            
            await self._collection.update_one(
                {"_id": media_id},
                {
                    "$set": {
                        "status": "completed",
                        "transcription": transcription_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # 如果配置了知识提取
            if self._knowledge_manager and result.get("text"):
                # 这里可以调用知识提取逻辑
                pass
            
            return {
                "media_id": media_id,
                "status": "completed",
                "text": transcription_data["text"],
                "segments_count": len(transcription_data["segments"])
            }
            
        except Exception as e:
            # 更新状态为failed
            await self._collection.update_one(
                {"_id": media_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            raise RuntimeError(f"转录失败: {e}")
    
    async def download_from_url(
        self,
        url: str,
        media_type: str,
        processor: str = "whisper",
        model: str = "base",
        language: str = "zh",
        auto_transcribe: bool = True
    ) -> Dict[str, Any]:
        """
        从URL下载媒体文件
        
        Args:
            url: 文件URL
            media_type: 媒体类型
            processor: 转录处理器
            model: Whisper模型
            language: 语言代码
            auto_transcribe: 是否自动转录
            
        Returns:
            媒体文件信息字典
        """
        # 生成唯一ID
        media_id = str(uuid.uuid4())
        
        # 从URL中提取文件名
        url_path = Path(url.split("?")[0])
        original_filename = url_path.name or "downloaded_file"
        file_ext = url_path.suffix.lower() or ".bin"
        
        # 构建保存路径
        save_dir = self._upload_dir / media_type
        save_path = save_dir / f"{media_id}{file_ext}"
        
        # 下载文件
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    raise RuntimeError(f"下载失败，HTTP状态码: {response.status}")
                
                content = await response.read()
                file_size = len(content)
                
                with open(save_path, "wb") as f:
                    f.write(content)
        
        # 创建数据库记录
        media_doc = {
            "_id": media_id,
            "filename": original_filename,
            "type": media_type,
            "source_url": url,
            "status": "pending" if auto_transcribe else "uploaded",
            "file_path": str(save_path),
            "file_size": file_size,
            "transcription": {
                "processor": processor,
                "model": model,
                "language": language,
                "text": None,
                "segments": [],
                "completed_at": None
            } if auto_transcribe else None,
            "knowledge_extracted": False,
            "knowledge_doc_ids": [],
            "upload_time": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self._collection.insert_one(media_doc)
        
        # 如果需要自动转录，提交到队列
        if auto_transcribe:
            await self.submit_transcription_task(media_id)
        
        return {
            "id": media_id,
            "filename": original_filename,
            "type": media_type,
            "source_url": url,
            "status": media_doc["status"],
            "file_size": file_size,
            "upload_time": media_doc["upload_time"]
        }
    
    async def get_media_status(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        获取媒体文件状态
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            媒体文件信息，不存在则返回None
        """
        media_doc = await self._collection.find_one({"_id": media_id})
        if not media_doc:
            return None
        
        return {
            "id": media_doc["_id"],
            "filename": media_doc["filename"],
            "type": media_doc["type"],
            "status": media_doc["status"],
            "file_size": media_doc.get("file_size", 0),
            "transcription": media_doc.get("transcription"),
            "knowledge_extracted": media_doc.get("knowledge_extracted", False),
            "upload_time": media_doc["upload_time"],
            "updated_at": media_doc["updated_at"]
        }
    
    async def list_media_files(
        self,
        media_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        列出媒体文件
        
        Args:
            media_type: 媒体类型筛选
            status: 状态筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含文件列表和总数的字典
        """
        query = {}
        if media_type:
            query["type"] = media_type
        if status:
            query["status"] = status
        
        cursor = self._collection.find(query).sort("upload_time", -1).skip(offset).limit(limit)
        files = []
        
        async for doc in cursor:
            files.append({
                "id": doc["_id"],
                "filename": doc["filename"],
                "type": doc["type"],
                "status": doc["status"],
                "file_size": doc.get("file_size", 0),
                "upload_time": doc["upload_time"]
            })
        
        total = await self._collection.count_documents(query)
        
        return {
            "files": files,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def delete_media_file(self, media_id: str) -> bool:
        """
        删除媒体文件
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            是否成功删除
        """
        media_doc = await self._collection.find_one({"_id": media_id})
        if not media_doc:
            return False
        
        # 删除物理文件
        file_path = Path(media_doc.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        result = await self._collection.delete_one({"_id": media_id})
        
        return result.deleted_count > 0
