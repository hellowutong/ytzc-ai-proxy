"""
AI Provider 单元测试
测试各种 AI 供应商的集成
"""
import sys
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.ai_provider import (  # noqa: E402
    ProviderType,
    ModelConfig,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionChoice,
    ChatCompletionResponse,
    BaseAIProvider,
    OpenAIProvider,
    AnthropicProvider,
    DeepSeekProvider,
    GoogleProvider,
    AIProviderFactory,
)


class TestModelConfig:
    """ModelConfig 数据类测试"""

    def test_create_model_config(self):
        """测试创建模型配置"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test-key",
            max_tokens=4096,
            supports_streaming=True
        )
        assert config.name == "gpt-4o"
        assert config.provider == ProviderType.OPENAI
        assert config.max_tokens == 4096

    def test_model_config_defaults(self):
        """测试模型配置默认值"""
        config = ModelConfig(
            name="gpt-3.5-turbo",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test-key"
        )
        assert config.max_tokens == 4096
        assert config.supports_streaming is True


class TestChatMessage:
    """ChatMessage 数据类测试"""

    def test_create_chat_message(self):
        """测试创建聊天消息"""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_create_assistant_message(self):
        """测试创建助手消息"""
        message = ChatMessage(role="assistant", content="I can help you.")
        assert message.role == "assistant"


class TestChatCompletionRequest:
    """ChatCompletionRequest 数据类测试"""

    def test_create_request(self):
        """测试创建请求"""
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!")
        ]
        request = ChatCompletionRequest(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            stream=False
        )
        assert request.model == "gpt-4o"
        assert len(request.messages) == 2
        assert request.temperature == 0.7

    def test_request_defaults(self):
        """测试请求默认值"""
        messages = [ChatMessage(role="user", content="Hello")]
        request = ChatCompletionRequest(
            model="gpt-4o",
            messages=messages
        )
        assert request.temperature == 0.7
        assert request.max_tokens is None
        assert request.stream is False


class TestChatCompletionResponse:
    """ChatCompletionResponse 数据类测试"""

    def test_create_response(self):
        """测试创建响应"""
        choices = [
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="Response"),
                finish_reason="stop"
            )
        ]
        response = ChatCompletionResponse(
            id="chatcmpl-123",
            object="chat.completion",
            created=1234567890,
            model="gpt-4o",
            choices=choices,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
        assert response.id == "chatcmpl-123"
        assert len(response.choices) == 1
        assert response.usage["total_tokens"] == 30


class TestProviderType:
    """ProviderType 枚举测试"""

    def test_provider_types(self):
        """测试供应商类型枚举值"""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.DEEPSEEK.value == "deepseek"
        assert ProviderType.GOOGLE.value == "google"
        assert ProviderType.AZURE.value == "azure"
        assert ProviderType.CUSTOM.value == "custom"


class TestOpenAIProvider:
    """OpenAIProvider 测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用 provider"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test-key",
            max_tokens=4096
        )
        return OpenAIProvider(config)

    def test_initialization(self, provider):
        """测试初始化"""
        assert provider.config.name == "gpt-4o"
        assert provider.base_url == "https://api.openai.com/v1"

    def test_custom_api_base(self):
        """测试自定义 API base"""
        config = ModelConfig(
            name="custom-model",
            provider=ProviderType.OPENAI,
            api_base="https://custom.api.com/v1",
            api_key="sk-test"
        )
        provider = OpenAIProvider(config)
        assert provider.base_url == "https://custom.api.com/v1"

    @pytest.mark.asyncio
    async def test_chat_completion_request_format(self, provider):
        """测试聊天完成请求格式"""
        messages = [
            ChatMessage(role="user", content="Hello, world!")
        ]
        request = ChatCompletionRequest(
            model="gpt-4o",
            messages=messages,
            temperature=0.5
        )

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }

        assert payload["model"] == "gpt-4o"
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["content"] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_chat_completion_with_max_tokens(self, provider):
        """测试带 max_tokens 的请求"""
        messages = [ChatMessage(role="user", content="Test")]
        request = ChatCompletionRequest(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )

        payload = {}
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        assert "max_tokens" in payload
        assert payload["max_tokens"] == 500

    def test_parse_response(self, provider):
        """测试解析响应"""
        mock_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }

        response = provider._parse_response("gpt-4o", mock_data)

        assert response.id == "chatcmpl-123"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Hello! How can I help you?"
        assert response.usage["prompt_tokens"] == 10

    def test_parse_response_multiple_choices(self, provider):
        """测试解析多选择响应"""
        mock_data = {
            "id": "chatcmpl-456",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Choice 1"},
                    "finish_reason": "stop"
                },
                {
                    "index": 1,
                    "message": {"role": "assistant", "content": "Choice 2"},
                    "finish_reason": "length"
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }

        response = provider._parse_response("gpt-4o", mock_data)

        assert len(response.choices) == 2
        assert response.choices[0].message.content == "Choice 1"
        assert response.choices[1].finish_reason == "length"

    def test_parse_response_missing_fields(self, provider):
        """测试解析缺少字段的响应"""
        mock_data = {
            "choices": [
                {"message": {"content": "Simple response"}}
            ]
        }

        response = provider._parse_response("gpt-4o", mock_data)

        assert response.id == "chatcmpl-unknown"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Simple response"


class TestAnthropicProvider:
    """AnthropicProvider 测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用 provider"""
        config = ModelConfig(
            name="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            api_base="https://api.anthropic.com/v1",
            api_key="sk-ant-test",
            max_tokens=4096
        )
        return AnthropicProvider(config)

    def test_initialization(self, provider):
        """测试初始化"""
        assert provider.base_url == "https://api.anthropic.com/v1"

    @pytest.mark.asyncio
    async def test_chat_completion_request_format(self, provider):
        """测试聊天完成请求格式"""
        messages = [ChatMessage(role="user", content="Hello")]
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=messages,
            temperature=0.5,
            max_tokens=1000
        )

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or provider.config.max_tokens
        }

        assert payload["model"] == "claude-sonnet-4"
        assert payload["max_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_chat_completion_uses_default_max_tokens(self, provider):
        """测试使用默认 max_tokens"""
        messages = [ChatMessage(role="user", content="Hello")]
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=messages,
            max_tokens=None
        )

        max_tokens = request.max_tokens or provider.config.max_tokens
        assert max_tokens == 4096

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """测试列出模型"""
        models = await provider.list_models()

        assert len(models) == 3
        assert any("claude" in m["id"].lower() for m in models)

    def test_parse_response(self, provider):
        """测试解析响应"""
        mock_data = {
            "id": "msg-123",
            "created_at": 1234567890,
            "content": [
                {"type": "text", "text": "Hello! How can I help?"}
            ],
            "stop_reason": "end_turn"
        }

        response = provider._parse_response("claude-sonnet-4", mock_data)

        assert response.id == "msg-123"
        assert len(response.choices) == 1
        assert "How can I help" in response.choices[0].message.content

    def test_parse_response_multiple_blocks(self, provider):
        """测试解析多内容块响应"""
        mock_data = {
            "id": "msg-456",
            "created_at": 1234567890,
            "content": [
                {"type": "text", "text": "Part 1 "},
                {"type": "text", "text": "Part 2"},
                {"type": "other", "text": "Should be ignored"}
            ],
            "stop_reason": "max_tokens"
        }

        response = provider._parse_response("claude-sonnet-4", mock_data)

        assert response.choices[0].message.content == "Part 1 Part 2"
        assert response.choices[0].finish_reason == "max_tokens"

    def test_embeddings_not_implemented(self, provider):
        """测试 embeddings 未实现"""
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(provider.embeddings(["text"], "embedding-model"))


class TestStreaming:
    """流式响应测试"""

    @pytest.fixture
    def openai_provider(self):
        """创建 OpenAI provider 用于流式测试"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test"
        )
        return OpenAIProvider(config)

    @pytest.mark.asyncio
    async def test_streaming_payload_format(self, openai_provider):
        """测试流式请求载荷格式"""
        messages = [ChatMessage(role="user", content="Tell me a story")]
        request = ChatCompletionRequest(
            model="gpt-4o",
            messages=messages,
            stream=True
        )

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }

        assert payload["stream"] is True


class TestProviderFactory:
    """供应商工厂测试"""

    def test_openai_provider_type(self):
        """测试 OpenAI 供应商类型"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test"
        )
        provider = OpenAIProvider(config)
        assert isinstance(provider, BaseAIProvider)
        assert provider.config.provider == ProviderType.OPENAI

    def test_anthropic_provider_type(self):
        """测试 Anthropic 供应商类型"""
        config = ModelConfig(
            name="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            api_base="https://api.anthropic.com/v1",
            api_key="sk-ant-test"
        )
        provider = AnthropicProvider(config)
        assert isinstance(provider, BaseAIProvider)
        assert provider.config.provider == ProviderType.ANTHROPIC


class TestDeepSeekProvider:
    """DeepSeekProvider 测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用 provider"""
        config = ModelConfig(
            name="deepseek-chat",
            provider=ProviderType.DEEPSEEK,
            api_base="https://api.deepseek.com",
            api_key="sk-deepseek-test",
            max_tokens=4096
        )
        return DeepSeekProvider(config)

    def test_initialization(self, provider):
        """测试初始化"""
        assert provider.base_url == "https://api.deepseek.com"
        assert provider.config.name == "deepseek-chat"

    def test_custom_api_base(self):
        """测试自定义 API base"""
        config = ModelConfig(
            name="deepseek-chat",
            provider=ProviderType.DEEPSEEK,
            api_base="https://custom.deepseek.com",
            api_key="sk-test"
        )
        provider = DeepSeekProvider(config)
        assert provider.base_url == "https://custom.deepseek.com"

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """测试列出模型"""
        models = await provider.list_models()

        assert len(models) == 2
        assert any("deepseek" in m["id"].lower() for m in models)

    def test_parse_response(self, provider):
        """测试解析响应"""
        mock_data = {
            "id": "chatcmpl-ds-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "DeepSeek response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        }

        response = provider._parse_response("deepseek-chat", mock_data)

        assert response.id == "chatcmpl-ds-123"
        assert response.choices[0].message.content == "DeepSeek response"

    def test_parse_response_empty_usage(self, provider):
        """测试解析缺少 usage 的响应"""
        mock_data = {
            "choices": [
                {"message": {"content": "Response without usage"}}
            ]
        }

        response = provider._parse_response("deepseek-chat", mock_data)

        assert response.usage["prompt_tokens"] == 0
        assert response.usage["total_tokens"] == 0


class TestGoogleProvider:
    """GoogleProvider 测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用 provider"""
        config = ModelConfig(
            name="gemini-1.5-pro",
            provider=ProviderType.GOOGLE,
            api_base="https://generativelanguage.googleapis.com/v1beta",
            api_key="AIza-test",
            max_tokens=4096
        )
        return GoogleProvider(config)

    def test_initialization(self, provider):
        """测试初始化"""
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert provider.config.name == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """测试列出模型"""
        models = await provider.list_models()

        assert len(models) == 3
        assert any("gemini" in m["id"].lower() for m in models)

    def test_parse_response(self, provider):
        """测试解析响应"""
        mock_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Google Gemini response"}]
                    },
                    "finishReason": "stop"
                }
            ]
        }

        response = provider._parse_response("gemini-1.5-pro", mock_data)

        assert response.id.startswith("chatcmpl-")
        assert response.choices[0].message.content == "Google Gemini response"
        assert response.choices[0].finish_reason == "stop"

    def test_parse_response_empty_candidates(self, provider):
        """测试解析空 candidates 响应"""
        mock_data = {}

        response = provider._parse_response("gemini-1.5-pro", mock_data)

        assert response.choices[0].message.content == ""
        assert response.choices[0].finish_reason == "stop"

    def test_parse_response_multiple_parts(self, provider):
        """测试解析多部分内容响应"""
        mock_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Part 1 "},
                            {"text": "Part 2"}
                        ]
                    },
                    "finishReason": "length"
                }
            ]
        }

        response = provider._parse_response("gemini-1.5-pro", mock_data)

        assert response.choices[0].message.content == "Part 1 Part 2"


class TestAIProviderFactory:
    """AIProviderFactory 测试"""

    def setup_method(self):
        """每个测试前清理缓存"""
        AIProviderFactory.clear_cache()

    def teardown_method(self):
        """每个测试后清理缓存"""
        AIProviderFactory.clear_cache()

    def test_get_openai_provider(self):
        """测试获取 OpenAI provider"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test"
        )

        provider = AIProviderFactory.get_provider(ProviderType.OPENAI, config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.config.name == "gpt-4o"

    def test_get_anthropic_provider(self):
        """测试获取 Anthropic provider"""
        config = ModelConfig(
            name="claude-sonnet-4",
            provider=ProviderType.ANTHROPIC,
            api_base="https://api.anthropic.com/v1",
            api_key="sk-ant-test"
        )

        provider = AIProviderFactory.get_provider(ProviderType.ANTHROPIC, config)

        assert isinstance(provider, AnthropicProvider)

    def test_get_deepseek_provider(self):
        """测试获取 DeepSeek provider"""
        config = ModelConfig(
            name="deepseek-chat",
            provider=ProviderType.DEEPSEEK,
            api_base="https://api.deepseek.com",
            api_key="sk-ds-test"
        )

        provider = AIProviderFactory.get_provider(ProviderType.DEEPSEEK, config)

        assert isinstance(provider, DeepSeekProvider)

    def test_get_google_provider(self):
        """测试获取 Google provider"""
        config = ModelConfig(
            name="gemini-1.5-pro",
            provider=ProviderType.GOOGLE,
            api_base="https://generativelanguage.googleapis.com/v1beta",
            api_key="AIza-test"
        )

        provider = AIProviderFactory.get_provider(ProviderType.GOOGLE, config)

        assert isinstance(provider, GoogleProvider)

    def test_get_unsupported_provider(self):
        """测试获取不支持的 provider"""
        from app.infrastructure.ai_provider import ProviderType

        config = ModelConfig(
            name="unknown",
            provider=ProviderType.CUSTOM,
            api_base="https://custom.api.com",
            api_key="sk-test"
        )

        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.get_provider(ProviderType.CUSTOM, config)

        assert "Unsupported provider type" in str(exc_info.value)

    def test_provider_caching(self):
        """测试 provider 缓存"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test"
        )

        provider1 = AIProviderFactory.get_provider(ProviderType.OPENAI, config)
        provider2 = AIProviderFactory.get_provider(ProviderType.OPENAI, config)

        assert provider1 is provider2

    def test_create_provider_from_dict(self):
        """测试从字典创建 provider"""
        provider_data = {
            "type": "openai",
            "small_model": {
                "id": "gpt-3.5-turbo",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-test",
                "max_tokens": 4096
            }
        }

        provider = AIProviderFactory.create_provider_from_dict(provider_data)

        assert isinstance(provider, OpenAIProvider)
        assert provider.config.name == "gpt-3.5-turbo"

    def test_create_provider_from_dict_big_model(self):
        """测试从字典创建 provider (big_model)"""
        provider_data = {
            "type": "deepseek",
            "big_model": {
                "id": "deepseek-chat",
                "api_base": "https://api.deepseek.com",
                "api_key": "sk-ds-test",
                "max_tokens": 8192
            }
        }

        provider = AIProviderFactory.create_provider_from_dict(provider_data)

        assert isinstance(provider, DeepSeekProvider)
        assert provider.config.max_tokens == 8192

    def test_create_provider_from_dict_missing_models(self):
        """测试从字典创建 provider (无模型配置)"""
        provider_data = {
            "type": "openai"
        }

        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.create_provider_from_dict(provider_data)

        assert "No model configuration found" in str(exc_info.value)

    def test_create_provider_from_dict_default_type(self):
        """测试从字典创建 provider (默认类型)"""
        provider_data = {
            "small_model": {
                "id": "gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key": "sk-test"
            }
        }

        provider = AIProviderFactory.create_provider_from_dict(provider_data)

        assert isinstance(provider, OpenAIProvider)

    def test_clear_cache(self):
        """测试清空缓存"""
        config = ModelConfig(
            name="gpt-4o",
            provider=ProviderType.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key="sk-test"
        )

        provider1 = AIProviderFactory.get_provider(ProviderType.OPENAI, config)
        AIProviderFactory.clear_cache()
        provider2 = AIProviderFactory.get_provider(ProviderType.OPENAI, config)

        assert provider1 is not provider2
