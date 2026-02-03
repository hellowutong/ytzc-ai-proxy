"""
AI Provider Integration Layer
支持多种AI供应商: OpenAI, Anthropic, DeepSeek, Google, Azure等
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
import json


class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    AZURE = "azure"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    name: str
    provider: ProviderType
    api_base: str
    api_key: str
    max_tokens: int = 4096
    supports_streaming: bool = True


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


@dataclass
class ChatCompletionChoice:
    index: int
    message: ChatMessage
    finish_reason: str


@dataclass
class ChatCompletionResponse:
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


class BaseAIProvider(ABC):
    """AI供应商基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    @abstractmethod
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass
    
    @abstractmethod
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        pass
    
    @abstractmethod
    async def embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict]:
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI 供应商实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.api_base or "https://api.openai.com/v1"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "stream": False
            }
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(request.model, data)
    
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "stream": True
            }
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
    
    async def embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json={"input": texts, "model": model}
            )
            response.raise_for_status()
            
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    
    async def list_models(self) -> List[Dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            response = await client.get(f"{self.base_url}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return [
                {"id": m["id"], "object": "model", "owned_by": m.get("owned_by", "openai")}
                for m in data.get("data", [])
                if "gpt" in m["id"].lower()
            ]
    
    def _parse_response(self, model: str, data: dict) -> ChatCompletionResponse:
        choices = []
        for choice in data.get("choices", []):
            message_data = choice.get("message", {})
            choices.append(ChatCompletionChoice(
                index=choice.get("index", 0),
                message=ChatMessage(
                    role=message_data.get("role", "assistant"),
                    content=message_data.get("content", "")
                ),
                finish_reason=choice.get("finish_reason", "stop")
            ))
        
        usage = data.get("usage", {})
        return ChatCompletionResponse(
            id=data.get("id", "chatcmpl-unknown"),
            object="chat.completion",
            created=data.get("created", 0),
            model=model,
            choices=choices,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        )


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude 供应商实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "x-api-key": self.config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or self.config.max_tokens
            }
            
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(request.model, data)
    
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "x-api-key": self.config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "stream": True
            }
            
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[5:])
                        if "delta" in data and "text" in data["delta"]:
                            yield data["delta"]["text"]
    
    async def embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        raise NotImplementedError("Anthropic does not currently offer embeddings API")
    
    async def list_models(self) -> List[Dict]:
        return [
            {"id": "claude-sonnet-4-20250514", "object": "model", "owned_by": "anthropic"},
            {"id": "claude-opus-4-20250514", "object": "model", "owned_by": "anthropic"},
            {"id": "claude-3-7-sonnet-20250514", "object": "model", "owned_by": "anthropic"},
        ]
    
    def _parse_response(self, model: str, data: dict) -> ChatCompletionResponse:
        content_blocks = data.get("content", [])
        content = "".join(
            block.get("text", "") 
            for block in content_blocks 
            if block.get("type") == "text"
        )
        
        return ChatCompletionResponse(
            id=data.get("id", "chatcmpl-unknown"),
            object="chat.completion",
            created=int(data.get("created_at", 0)),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=content),
                    finish_reason=data.get("stop_reason", "stop")
                )
            ],
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            }
        )


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek 供应商实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.api_base or "https://api.deepseek.com"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "stream": False
            }
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(request.model, data)
    
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "stream": True
            }
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
    
    async def embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json={"input": texts, "model": model}
            )
            response.raise_for_status()
            
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    
    async def list_models(self) -> List[Dict]:
        return [
            {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
            {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
        ]
    
    def _parse_response(self, model: str, data: dict) -> ChatCompletionResponse:
        choices = []
        for choice in data.get("choices", []):
            message_data = choice.get("message", {})
            choices.append(ChatCompletionChoice(
                index=choice.get("index", 0),
                message=ChatMessage(
                    role=message_data.get("role", "assistant"),
                    content=message_data.get("content", "")
                ),
                finish_reason=choice.get("finish_reason", "stop")
            ))
        
        usage = data.get("usage", {})
        return ChatCompletionResponse(
            id=data.get("id", "chatcmpl-unknown"),
            object="chat.completion",
            created=data.get("created", 0),
            model=model,
            choices=choices,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        )


class GoogleProvider(BaseAIProvider):
    """Google Gemini 供应商实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{self.base_url}/models/{request.model}:generateContent?key={self.config.api_key}"
            
            contents = []
            for m in request.messages:
                if m.role == "user":
                    contents.append({"role": "user", "parts": [{"text": m.content}]})
                elif m.role == "model":
                    contents.append({"role": "model", "parts": [{"text": m.content}]})
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature,
                    "maxOutputTokens": request.max_tokens or self.config.max_tokens
                }
            }
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(request.model, data)
    
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{self.base_url}/models/{request.model}:streamGenerateContent?key={self.config.api_key}"
            
            contents = []
            for m in request.messages:
                if m.role == "user":
                    contents.append({"role": "user", "parts": [{"text": m.content}]})
                elif m.role == "model":
                    contents.append({"role": "model", "parts": [{"text": m.content}]})
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature,
                    "maxOutputTokens": request.max_tokens or self.config.max_tokens
                }
            }
            
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        data = json.loads(line)
                        if "candidates" in data:
                            content = data["candidates"][0]["content"]["parts"][0].get("text", "")
                            if content:
                                yield content
    
    async def embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{self.base_url}/models/{model}:embedContent?key={self.config.api_key}"
            
            embeddings = []
            for text in texts:
                response = await client.post(
                    url,
                    json={"content": {"parts": [{"text": text}]}}
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data.get("embedding", {}).get("values", []))
            
            return embeddings
    
    async def list_models(self) -> List[Dict]:
        return [
            {"id": "gemini-1.5-pro", "object": "model", "owned_by": "google"},
            {"id": "gemini-1.5-flash", "object": "model", "owned_by": "google"},
            {"id": "gemini-1.0-pro", "object": "model", "owned_by": "google"},
        ]
    
    def _parse_response(self, model: str, data: dict) -> ChatCompletionResponse:
        candidates = data.get("candidates", [])
        content = ""
        finish_reason = "stop"
        
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
            finish_reason = candidates[0].get("finishReason", "stop")
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{hash(model)}",
            object="chat.completion",
            created=0,
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=content),
                    finish_reason=finish_reason
                )
            ],
            usage={"prompt_tokens": 0, "completion_tokens": len(content), "total_tokens": len(content)}
        )


class AIProviderFactory:
    """AI供应商工厂"""
    
    _providers: Dict[str, BaseAIProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_type: ProviderType, config: ModelConfig) -> BaseAIProvider:
        provider_key = f"{provider_type.value}:{config.name}"
        
        if provider_key not in cls._providers:
            if provider_type == ProviderType.OPENAI:
                cls._providers[provider_key] = OpenAIProvider(config)
            elif provider_type == ProviderType.ANTHROPIC:
                cls._providers[provider_key] = AnthropicProvider(config)
            elif provider_type == ProviderType.DEEPSEEK:
                cls._providers[provider_key] = DeepSeekProvider(config)
            elif provider_type == ProviderType.GOOGLE:
                cls._providers[provider_key] = GoogleProvider(config)
            else:
                raise ValueError(f"Unsupported provider type: {provider_type}")
        
        return cls._providers[provider_key]
    
    @classmethod
    def create_provider_from_dict(cls, provider_data: Dict) -> BaseAIProvider:
        provider_type = ProviderType(provider_data.get("type", "openai"))
        
        model_configs = []
        for model_key in ["small_model", "big_model"]:
            if model_key in provider_data:
                model_data = provider_data[model_key]
                config = ModelConfig(
                    name=model_data.get("id", "unknown"),
                    provider=provider_type,
                    api_base=model_data.get("api_base", ""),
                    api_key=model_data.get("api_key", ""),
                    max_tokens=model_data.get("max_tokens", 4096)
                )
                model_configs.append(config)
        
        if model_configs:
            return cls.get_provider(provider_type, model_configs[0])
        raise ValueError("No model configuration found")
    
    @classmethod
    def clear_cache(cls):
        cls._providers.clear()
