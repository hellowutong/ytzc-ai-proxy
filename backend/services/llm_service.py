"""
LLM服务 - 支持SiliconFlow, OpenAI, Ollama
"""

import json
import time
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx

from models.base import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionStreamResponse,
    ChatCompletionStreamChoice,
    Message,
    Usage,
    LLMConfig,
    ModelProvider,
)

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务 - 统一封装多种模型提供商的API调用"""

    def __init__(self, config: LLMConfig):
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
            if self.config.provider == ModelProvider.OPENAI:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            elif self.config.provider == ModelProvider.SILICONFLOW:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            # Ollama不需要API Key
        
        return headers

    def _get_request_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """构建请求体"""
        messages = []
        for msg in request.messages:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.name:
                message_dict["name"] = msg.name
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            messages.append(message_dict)

        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": request.temperature or self.config.temperature,
            "stream": request.stream,
        }

        if request.max_tokens:
            body["max_tokens"] = request.max_tokens
        elif self.config.max_tokens:
            body["max_tokens"] = self.config.max_tokens

        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            body["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            body["presence_penalty"] = request.presence_penalty

        return body

    async def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        非流式对话
        
        Args:
            request: 聊天完成请求
            
        Returns:
            ChatCompletionResponse: 对话响应
        """
        url = f"{self.config.base_url}/chat/completions"
        body = self._get_request_body(request)

        try:
            logger.info(f"调用LLM API: {self.config.provider.value}, model: {self.config.model}")
            response = await self.client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

            # 解析响应
            choices = []
            for choice_data in data.get("choices", []):
                message_data = choice_data.get("message", {})
                message = Message(
                    role=message_data.get("role", "assistant"),
                    content=message_data.get("content", ""),
                    name=message_data.get("name"),
                    tool_calls=message_data.get("tool_calls"),
                    tool_call_id=message_data.get("tool_call_id")
                )
                choices.append(ChatCompletionChoice(
                    index=choice_data.get("index", 0),
                    message=message,
                    finish_reason=choice_data.get("finish_reason")
                ))

            usage_data = data.get("usage", {})
            usage = Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )

            return ChatCompletionResponse(
                id=data.get("id", f"chatcmpl-{int(time.time())}"),
                created=data.get("created", int(time.time())),
                model=data.get("model", self.config.model),
                choices=choices,
                usage=usage
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP错误: {e.response.status_code}, {e.response.text}")
            raise LLMError(f"API调用失败: {e.response.status_code}", 
                          status_code=e.response.status_code)
        except httpx.RequestError as e:
            logger.error(f"LLM API请求错误: {e}")
            raise LLMError(f"API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"LLM API未知错误: {e}")
            raise LLMError(f"API调用异常: {str(e)}")

    async def stream_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """
        流式对话 - SSE格式
        
        Args:
            request: 聊天完成请求（stream=True）
            
        Yields:
            str: SSE格式的数据行
        """
        url = f"{self.config.base_url}/chat/completions"
        body = self._get_request_body(request)
        body["stream"] = True

        try:
            logger.info(f"调用LLM流式API: {self.config.provider.value}, model: {self.config.model}")
            
            async with self.client.stream("POST", url, json=body) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀
                        
                        if data == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            # 转换为标准格式
                            choices = []
                            for choice_data in chunk.get("choices", []):
                                delta = choice_data.get("delta", {})
                                choices.append(ChatCompletionStreamChoice(
                                    index=choice_data.get("index", 0),
                                    delta=delta,
                                    finish_reason=choice_data.get("finish_reason")
                                ))
                            
                            stream_response = ChatCompletionStreamResponse(
                                id=chunk.get("id", f"chatcmpl-{int(time.time())}"),
                                created=chunk.get("created", int(time.time())),
                                model=chunk.get("model", self.config.model),
                                choices=choices
                            )
                            
                            yield f"data: {stream_response.model_dump_json()}\n\n"
                            
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析SSE数据: {data}")
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM流式API HTTP错误: {e.response.status_code}")
            error_data = {
                "error": {
                    "message": f"API调用失败: {e.response.status_code}",
                    "type": "api_error",
                    "code": str(e.response.status_code)
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        except httpx.RequestError as e:
            logger.error(f"LLM流式API请求错误: {e}")
            error_data = {
                "error": {
                    "message": f"API请求失败: {str(e)}",
                    "type": "request_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        except Exception as e:
            logger.error(f"LLM流式API未知错误: {e}")
            error_data = {
                "error": {
                    "message": f"API调用异常: {str(e)}",
                    "type": "unknown_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"

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
            return data.get("data", [])
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class LLMError(Exception):
    """LLM服务错误"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class LLMServiceFactory:
    """LLM服务工厂"""

    _instances: Dict[str, LLMService] = {}

    @classmethod
    def create(cls, provider: ModelProvider, base_url: str, 
               api_key: Optional[str] = None, model: str = "",
               **kwargs) -> LLMService:
        """创建LLM服务实例"""
        config = LLMConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            **kwargs
        )
        return LLMService(config)

    @classmethod
    def get_or_create(cls, key: str, provider: ModelProvider, 
                      base_url: str, api_key: Optional[str] = None,
                      model: str = "", **kwargs) -> LLMService:
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
def create_siliconflow_service(api_key: str, model: str = "Qwen/Qwen2.5-7B-Instruct",
                                base_url: str = "https://api.siliconflow.cn/v1") -> LLMService:
    """创建SiliconFlow服务"""
    return LLMServiceFactory.create(
        provider=ModelProvider.SILICONFLOW,
        base_url=base_url,
        api_key=api_key,
        model=model
    )


def create_openai_service(api_key: str, model: str = "gpt-4",
                           base_url: str = "https://api.openai.com/v1") -> LLMService:
    """创建OpenAI服务"""
    return LLMServiceFactory.create(
        provider=ModelProvider.OPENAI,
        base_url=base_url,
        api_key=api_key,
        model=model
    )


def create_ollama_service(model: str = "llama3.1",
                          base_url: str = "http://localhost:11434/v1") -> LLMService:
    """创建Ollama服务"""
    return LLMServiceFactory.create(
        provider=ModelProvider.OLLAMA,
        base_url=base_url,
        api_key=None,
        model=model
    )
