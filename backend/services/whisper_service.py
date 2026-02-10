"""
Whisper服务 - 支持本地Whisper和API调用
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import httpx

from models.base import (
    TranscriptionResult,
    TranscriptionSegment,
    WhisperConfig,
)

logger = logging.getLogger(__name__)


class WhisperService:
    """Whisper服务 - 音频/视频转录"""

    def __init__(self, config: WhisperConfig):
        self.config = config
        self._local_model = None
        
        if config.mode == "local":
            self._init_local_model()
        elif config.mode == "api":
            self.client = httpx.AsyncClient(
                timeout=config.timeout,
                headers=self._get_headers()
            )

    def _init_local_model(self):
        """初始化本地Whisper模型"""
        try:
            import whisper
            logger.info(f"正在加载本地Whisper模型: {self.config.model}")
            
            # 使用指定的设备（如果提供）
            device = self.config.device
            self._local_model = whisper.load_model(self.config.model, device=device)
            logger.info("Whisper模型加载完成")
        except ImportError:
            logger.error("未安装openai-whisper库，请运行: pip install openai-whisper")
            raise WhisperError("缺少openai-whisper依赖")
        except Exception as e:
            logger.error(f"加载Whisper模型失败: {e}")
            raise WhisperError(f"模型加载失败: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def transcribe(
        self,
        file_path: Union[str, Path],
        language: Optional[str] = None,
        model: Optional[str] = None,
        output_format: str = "json"
    ) -> TranscriptionResult:
        """
        转录音频/视频文件
        
        Args:
            file_path: 文件路径
            language: 语言代码（如 'zh', 'en'）
            model: 模型名称（仅API模式有效）
            output_format: 输出格式
            
        Returns:
            TranscriptionResult: 转录结果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise WhisperError(f"文件不存在: {file_path}")

        if self.config.mode == "local":
            return await self._transcribe_local(file_path, language)
        else:
            return await self._transcribe_api(file_path, language, model)

    async def _transcribe_local(
        self,
        file_path: Path,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """使用本地Whisper模型转录"""
        if self._local_model is None:
            raise WhisperError("本地模型未初始化")

        try:
            logger.info(f"开始本地转录: {file_path}")
            
            # 构建转录选项
            options = {}
            lang = language or self.config.language
            if lang:
                options["language"] = lang
            
            # 执行转录
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._local_model.transcribe(str(file_path), **options)
            )

            # 解析结果
            segments = []
            for seg in result.get("segments", []):
                segments.append(TranscriptionSegment(
                    id=seg.get("id", 0),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    text=seg.get("text", "").strip(),
                    confidence=seg.get("avg_logprob")
                ))

            logger.info(f"转录完成: {len(segments)} 个片段")
            
            return TranscriptionResult(
                text=result.get("text", "").strip(),
                language=result.get("language", lang or "unknown"),
                segments=segments,
                duration=segments[-1].end if segments else None
            )

        except Exception as e:
            logger.error(f"本地转录失败: {e}")
            raise WhisperError(f"转录失败: {str(e)}")

    async def _transcribe_api(
        self,
        file_path: Path,
        language: Optional[str] = None,
        model: Optional[str] = None
    ) -> TranscriptionResult:
        """使用API转录"""
        if not self.config.base_url:
            raise WhisperError("API模式需要配置base_url")

        try:
            logger.info(f"开始API转录: {file_path}")
            
            url = f"{self.config.base_url}/audio/transcriptions"
            
            # 读取文件
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # 构建multipart表单
            files = {
                "file": (file_path.name, file_content, self._get_mime_type(file_path))
            }
            
            data = {
                "model": model or self.config.model,
            }
            
            lang = language or self.config.language
            if lang:
                data["language"] = lang

            # 发送请求
            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            result = response.json()

            logger.info("API转录完成")
            
            # 解析结果（API格式可能不同）
            text = result.get("text", "")
            
            # 如果API返回了segments
            segments = None
            if "segments" in result:
                segments = [
                    TranscriptionSegment(
                        id=seg.get("id", i),
                        start=seg.get("start", 0.0),
                        end=seg.get("end", 0.0),
                        text=seg.get("text", "").strip(),
                        confidence=seg.get("confidence")
                    )
                    for i, seg in enumerate(result["segments"])
                ]

            return TranscriptionResult(
                text=text,
                language=lang or "unknown",
                segments=segments,
                duration=segments[-1].end if segments else None
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"API转录HTTP错误: {e.response.status_code}, {e.response.text}")
            raise WhisperError(f"API调用失败: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"API转录请求错误: {e}")
            raise WhisperError(f"API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"API转录失败: {e}")
            raise WhisperError(f"转录失败: {str(e)}")

    def _get_mime_type(self, file_path: Path) -> str:
        """根据文件扩展名获取MIME类型"""
        ext = file_path.suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".mp4": "audio/mp4",
            ".wav": "audio/wav",
            ".m4a": "audio/m4a",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
            ".flac": "audio/flac",
        }
        return mime_types.get(ext, "audio/mpeg")

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        转录音频字节数据
        
        Args:
            audio_bytes: 音频数据
            filename: 文件名（用于确定格式）
            language: 语言代码
            
        Returns:
            TranscriptionResult: 转录结果
        """
        if self.config.mode == "local":
            # 保存到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            try:
                result = await self._transcribe_local(Path(temp_path), language)
                return result
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass
        else:
            # API模式直接发送字节
            if not self.config.base_url:
                raise WhisperError("API模式需要配置base_url")

            url = f"{self.config.base_url}/audio/transcriptions"
            
            files = {
                "file": (filename, audio_bytes, self._get_mime_type(Path(filename)))
            }
            
            data = {
                "model": self.config.model,
            }
            
            lang = language or self.config.language
            if lang:
                data["language"] = lang

            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            result = response.json()

            return TranscriptionResult(
                text=result.get("text", ""),
                language=lang or "unknown",
                segments=None,
                duration=None
            )

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if self.config.mode == "local" and self._local_model:
            return {
                "mode": "local",
                "model": self.config.model,
                "device": self.config.device or "auto",
                "loaded": True
            }
        else:
            return {
                "mode": self.config.mode,
                "model": self.config.model,
                "base_url": self.config.base_url,
                "language": self.config.language
            }

    async def close(self):
        """关闭服务"""
        if self.config.mode == "api" and hasattr(self, 'client'):
            await self.client.aclose()


class WhisperError(Exception):
    """Whisper服务错误"""
    
    def __init__(self, message: str):
        super().__init__(message)


class WhisperServiceFactory:
    """Whisper服务工厂"""

    _instances: Dict[str, WhisperService] = {}

    @classmethod
    def create(cls, mode: str = "local", model: str = "base",
               language: str = "zh", device: Optional[str] = None,
               base_url: Optional[str] = None, api_key: Optional[str] = None,
               **kwargs) -> WhisperService:
        """创建Whisper服务实例"""
        config = WhisperConfig(
            mode=mode,
            model=model,
            language=language,
            device=device,
            base_url=base_url,
            api_key=api_key,
            **kwargs
        )
        return WhisperService(config)

    @classmethod
    def get_or_create(cls, key: str, **kwargs) -> WhisperService:
        """获取或创建缓存的服务实例"""
        if key not in cls._instances:
            cls._instances[key] = cls.create(**kwargs)
        return cls._instances[key]

    @classmethod
    async def close_all(cls):
        """关闭所有服务实例"""
        for service in cls._instances.values():
            await service.close()
        cls._instances.clear()


# 便捷函数
def create_local_whisper_service(
    model: str = "base",
    language: str = "zh",
    device: Optional[str] = None
) -> WhisperService:
    """创建本地Whisper服务"""
    return WhisperServiceFactory.create(
        mode="local",
        model=model,
        language=language,
        device=device
    )


def create_api_whisper_service(
    base_url: str,
    api_key: Optional[str] = None,
    model: str = "whisper-1",
    language: str = "zh"
) -> WhisperService:
    """创建API Whisper服务"""
    return WhisperServiceFactory.create(
        mode="api",
        base_url=base_url,
        api_key=api_key,
        model=model,
        language=language
    )
