"""
Embedding服务 - 支持BAAI/bge-m3等模型
"""

import logging
from typing import Dict, Any, List, Optional, Union
import httpx

from models.base import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingData,
    Usage,
    EmbeddingConfig,
    ModelProvider,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding服务 - 统一封装多种模型提供商的Embedding API"""

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.config.api_key:
            if self.config.provider in [ModelProvider.OPENAI, ModelProvider.SILICONFLOW]:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        return headers

    async def get_embedding(self, text: Union[str, List[str]], 
                           model: Optional[str] = None) -> EmbeddingResponse:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本或文本列表
            model: 模型名称（默认使用配置中的模型）
            
        Returns:
            EmbeddingResponse: 嵌入响应
        """
        if isinstance(text, str):
            text_input = [text]
        else:
            text_input = text

        url = f"{self.config.base_url}/embeddings"
        body = {
            "input": text_input,
            "model": model or self.config.model,
            "encoding_format": "float"
        }

        try:
            logger.debug(f"调用Embedding API: {self.config.provider.value}, model: {body['model']}")
            response = await self.client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

            # 解析响应
            embeddings = []
            for idx, item in enumerate(data.get("data", [])):
                embeddings.append(EmbeddingData(
                    object="embedding",
                    embedding=item.get("embedding", []),
                    index=item.get("index", idx)
                ))

            usage_data = data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=0,
                total_tokens=usage_data.get("total_tokens", usage_data.get("prompt_tokens", 0))
            )

            return EmbeddingResponse(
                object="list",
                data=embeddings,
                model=data.get("model", body["model"]),
                usage=usage
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Embedding API HTTP错误: {e.response.status_code}, {e.response.text}")
            raise EmbeddingError(f"API调用失败: {e.response.status_code}", 
                                status_code=e.response.status_code)
        except httpx.RequestError as e:
            logger.error(f"Embedding API请求错误: {e}")
            raise EmbeddingError(f"API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"Embedding API未知错误: {e}")
            raise EmbeddingError(f"API调用异常: {str(e)}")

    async def get_embedding_single(self, text: str, 
                                   model: Optional[str] = None) -> List[float]:
        """
        获取单条文本的嵌入向量
        
        Args:
            text: 输入文本
            model: 模型名称
            
        Returns:
            List[float]: 嵌入向量
        """
        response = await self.get_embedding(text, model)
        if response.data:
            return response.data[0].embedding
        raise EmbeddingError("未返回嵌入向量")

    async def get_embeddings_batch(self, texts: List[str], 
                                   model: Optional[str] = None,
                                   batch_size: int = 100) -> List[List[float]]:
        """
        批量获取文本的嵌入向量
        
        Args:
            texts: 文本列表
            model: 模型名称
            batch_size: 批处理大小
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        all_embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.get_embedding(batch, model)
            
            # 按索引排序
            sorted_data = sorted(response.data, key=lambda x: x.index)
            batch_embeddings = [item.embedding for item in sorted_data]
            all_embeddings.extend(batch_embeddings)
            
            logger.debug(f"已处理 {min(i + batch_size, len(texts))}/{len(texts)} 条文本")

        return all_embeddings

    async def get_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表
        
        Returns:
            List[Dict]: 模型列表
        """
        url = f"{self.config.base_url}/models"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # 过滤embedding模型
            models = data.get("data", [])
            embedding_models = [
                m for m in models 
                if "embed" in m.get("id", "").lower() or "bge" in m.get("id", "").lower()
            ]
            return embedding_models or models
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    def calculate_similarity(self, embedding1: List[float], 
                            embedding2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            embedding1: 向量1
            embedding2: 向量2
            
        Returns:
            float: 余弦相似度 [-1, 1]
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("向量维度不匹配")
        
        # 计算点积
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # 计算模长
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class EmbeddingError(Exception):
    """Embedding服务错误"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class EmbeddingServiceFactory:
    """Embedding服务工厂"""

    _instances: Dict[str, EmbeddingService] = {}

    @classmethod
    def create(cls, provider: ModelProvider, base_url: str,
               api_key: Optional[str] = None, model: str = "BAAI/bge-m3",
               dimension: int = 1024, **kwargs) -> EmbeddingService:
        """创建Embedding服务实例"""
        config = EmbeddingConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            dimension=dimension,
            **kwargs
        )
        return EmbeddingService(config)

    @classmethod
    def get_or_create(cls, key: str, provider: ModelProvider,
                      base_url: str, api_key: Optional[str] = None,
                      model: str = "BAAI/bge-m3", **kwargs) -> EmbeddingService:
        """获取或创建缓存的服务实例"""
        if key not in cls._instances:
            cls._instances[key] = cls.create(
                provider=provider,
                base_url=base_url,
                api_key=api_key,
                model=model,
                **kwargs
            )
        return cls._instances[key]

    @classmethod
    async def close_all(cls):
        """关闭所有服务实例"""
        for service in cls._instances.values():
            await service.close()
        cls._instances.clear()


# 便捷函数
def create_siliconflow_embedding_service(
    api_key: str,
    model: str = "BAAI/bge-m3",
    base_url: str = "https://api.siliconflow.cn/v1",
    dimension: int = 1024
) -> EmbeddingService:
    """创建SiliconFlow Embedding服务"""
    return EmbeddingServiceFactory.create(
        provider=ModelProvider.SILICONFLOW,
        base_url=base_url,
        api_key=api_key,
        model=model,
        dimension=dimension
    )


def create_openai_embedding_service(
    api_key: str,
    model: str = "text-embedding-3-small",
    base_url: str = "https://api.openai.com/v1",
    dimension: int = 1536
) -> EmbeddingService:
    """创建OpenAI Embedding服务"""
    return EmbeddingServiceFactory.create(
        provider=ModelProvider.OPENAI,
        base_url=base_url,
        api_key=api_key,
        model=model,
        dimension=dimension
    )


def create_ollama_embedding_service(
    model: str = "nomic-embed-text",
    base_url: str = "http://localhost:11434/v1",
    dimension: int = 768
) -> EmbeddingService:
    """创建Ollama Embedding服务"""
    return EmbeddingServiceFactory.create(
        provider=ModelProvider.OLLAMA,
        base_url=base_url,
        api_key=None,
        model=model,
        dimension=dimension
    )
