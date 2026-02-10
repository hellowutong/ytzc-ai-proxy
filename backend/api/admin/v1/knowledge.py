"""
知识库管理API
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel

from api.dependencies import get_knowledge_manager, get_config_manager, get_embedding_service
from core.knowledge_manager import KnowledgeManager
from core.config import ConfigManager
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


class KnowledgeDoc(BaseModel):
    id: str
    filename: str
    type: str
    source: str
    vectorized: bool
    created_at: str


class VectorConfig(BaseModel):
    embedding_model: str
    base_url: str
    api_key: str
    cron_expression: str = "*/30 * * * *"
    cron_enabled: bool = False


class TestVectorRequest(BaseModel):
    model: str
    base_url: str
    api_key: str = ""


def format_document(doc) -> Dict[str, Any]:
    """Format Document dataclass or dict to API response format"""
    if hasattr(doc, 'upload_time'):
        # It's a Document dataclass
        upload_time = doc.upload_time
    else:
        # It's a dict
        upload_time = doc.get("upload_time")
    
    if isinstance(upload_time, datetime):
        upload_time = upload_time.isoformat()
    
    return {
        "id": doc.id if hasattr(doc, 'id') else doc.get("_id", ""),
        "filename": doc.filename if hasattr(doc, 'filename') else doc.get("filename", ""),
        "type": doc.file_type if hasattr(doc, 'file_type') else doc.get("type", ""),
        "source": doc.source if hasattr(doc, 'source') else doc.get("source", ""),
        "vectorized": doc.vectorized if hasattr(doc, 'vectorized') else doc.get("vectorized", False),
        "created_at": upload_time or datetime.utcnow().isoformat()
    }


# Config keys for vector settings
VECTOR_CONFIG_KEYS = {
    "embedding_model": "ai-gateway.knowledge.embedding_model",
    "base_url": "ai-gateway.knowledge.embedding_base_url",
    "api_key": "ai-gateway.knowledge.embedding_api_key",
    "cron_expression": "ai-gateway.knowledge.cron_expression",
    "cron_enabled": "ai-gateway.knowledge.cron_enabled"
}


@router.get("/knowledge/docs")
async def get_docs(
    page: int = 1,
    page_size: int = 20,
    type: Optional[str] = None,
    source: Optional[str] = None,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """获取文档列表"""
    try:
        # Calculate offset from page number
        offset = (page - 1) * page_size
        
        # Map frontend 'type' filter to KnowledgeManager's file_type parameter
        file_type = type
        
        # Call KnowledgeManager
        documents, total = await knowledge_manager.list_documents(
            source=source,
            limit=page_size,
            offset=offset
        )
        
        # Filter by type if specified (KnowledgeManager doesn't have file_type filter)
        items = [format_document(doc) for doc in documents]
        if type:
            items = [d for d in items if d["type"] == type]
            total = len(items)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.post("/knowledge/docs/upload")
async def upload_doc(
    file: UploadFile = File(...),
    model: str = Form(...),
    shared: bool = Form(False),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """上传文档"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Call KnowledgeManager
        doc = await knowledge_manager.upload_document(
            file_content=file_content,
            filename=file.filename or "unknown",
            virtual_model=model,
            is_shared=shared
        )
        
        return {
            "code": 200,
            "message": "文档上传成功",
            "data": format_document(doc)
        }
    except Exception as e:
        logger.error(f"上传文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")


@router.delete("/knowledge/docs/{doc_id}")
async def delete_doc(
    doc_id: str,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """删除文档"""
    try:
        success = await knowledge_manager.delete_document(doc_id)
        
        if success:
            return {
                "code": 200,
                "message": "文档删除成功",
                "data": None
            }
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/knowledge/docs/{doc_id}/revectorize")
async def revectorize_doc(
    doc_id: str,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager)
):
    """重新向量化文档"""
    try:
        # First check if document exists
        doc = await knowledge_manager.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # Submit vectorization task
        success = await knowledge_manager.vectorize_document(doc_id)
        
        if success:
            return {
                "code": 200,
                "message": "向量化任务已提交",
                "data": None
            }
        else:
            raise HTTPException(status_code=500, detail="向量化任务提交失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新向量化文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新向量化文档失败: {str(e)}")


@router.get("/knowledge/config")
async def get_vector_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取向量配置"""
    try:
        config_data = {}
        for frontend_key, config_key in VECTOR_CONFIG_KEYS.items():
            config_data[frontend_key] = config_manager.get(config_key, "")
        
        # Set defaults for missing keys
        if not config_data.get("cron_expression"):
            config_data["cron_expression"] = "*/30 * * * *"
        if config_data.get("cron_enabled") is None:
            config_data["cron_enabled"] = False
        
        return {
            "code": 200,
            "message": "success",
            "data": config_data
        }
    except Exception as e:
        logger.error(f"获取向量配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取向量配置失败: {str(e)}")


@router.put("/knowledge/config")
async def update_vector_config(
    config: VectorConfig,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """更新向量配置"""
    try:
        config_dict = config.model_dump()
        
        # Save each config key
        for frontend_key, config_key in VECTOR_CONFIG_KEYS.items():
            if frontend_key in config_dict:
                config_manager.set(config_key, config_dict[frontend_key])
        
        # Persist config
        config_manager.save_config()
        
        return {
            "code": 200,
            "message": "配置保存成功",
            "data": config_dict
        }
    except Exception as e:
        logger.error(f"更新向量配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新向量配置失败: {str(e)}")


@router.post("/knowledge/test-vector")
async def test_vector_connection(
    body: TestVectorRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """测试向量服务连接"""
    try:
        # Try to get an embedding to test the connection
        test_text = "测试连接"
        
        # Create a temporary service config with provided values for testing
        # Note: This is a simplified test - in production, you'd want to
        # create a temporary service instance with the provided config
        
        # For now, just test with the current service
        try:
            result = await embedding_service.get_embedding(test_text)
            
            if result and result.data:
                return {
                    "code": 200,
                    "message": "向量服务连接成功",
                    "data": {
                        "model": result.model,
                        "dimension": len(result.data[0].embedding) if result.data else 0
                    }
                }
            else:
                raise HTTPException(status_code=500, detail="无法获取嵌入向量")
        except Exception as e:
            logger.error(f"向量服务连接测试失败: {e}")
            raise HTTPException(status_code=500, detail=f"向量服务连接失败: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试向量连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试向量连接失败: {str(e)}")
