"""
搜索服务 - 支持SearXNG, LibreX, 4get
"""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, quote_plus
import httpx

from models.base import (
    SearchResult,
    SearchConfig,
    SearchProvider,
)

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务 - 统一封装多种搜索引擎API"""

    def __init__(self, config: SearchConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=True
        )

    async def search(
        self,
        query: str,
        num_results: int = 10,
        category: Optional[str] = None,
        language: Optional[str] = None,
        safesearch: int = 0
    ) -> List[SearchResult]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            category: 分类（general, images, videos, news, science等）
            language: 语言代码
            safesearch: 安全搜索级别 (0=关闭, 1=中等, 2=严格)
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not query.strip():
            return []

        try:
            if self.config.provider == SearchProvider.SEARXNG:
                return await self._search_searxng(query, num_results, category, language, safesearch)
            elif self.config.provider == SearchProvider.LIBREX:
                return await self._search_librex(query, num_results, category, language)
            elif self.config.provider == SearchProvider.FOURGET:
                return await self._search_4get(query, num_results, category, language)
            else:
                raise SearchError(f"不支持的搜索提供商: {self.config.provider}")
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    async def _search_searxng(
        self,
        query: str,
        num_results: int,
        category: Optional[str],
        language: Optional[str],
        safesearch: int
    ) -> List[SearchResult]:
        """使用SearXNG搜索"""
        params = {
            "q": query,
            "format": "json",
            "pageno": 1,
            "language": language or self.config.language,
            "safesearch": safesearch,
        }
        
        if category:
            params["categories"] = category
        
        if self.config.categories and not category:
            params["categories"] = ",".join(self.config.categories)

        url = f"{self.config.base_url}/search?{urlencode(params)}"
        
        logger.debug(f"SearXNG搜索: {query}")
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:num_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content") or item.get("abstract", ""),
                engine="searxng",
                score=item.get("score")
            ))

        logger.info(f"SearXNG搜索完成: 找到 {len(results)} 条结果")
        return results

    async def _search_librex(
        self,
        query: str,
        num_results: int,
        category: Optional[str],
        language: Optional[str]
    ) -> List[SearchResult]:
        """使用LibreX搜索"""
        # LibreX 通常使用 POST 请求或特定的 GET 格式
        # 这里实现常见的 LibreX API 格式
        params = {
            "q": query,
            "p": 0,  # 页码
            "t": category or "0",  # 类型: 0=全部, 1=图片, 2=视频, 3=新闻
        }
        
        if language:
            params["lang"] = language

        url = f"{self.config.base_url}/api.php"
        
        logger.debug(f"LibreX搜索: {query}")
        
        # LibreX 可能需要 POST 请求
        try:
            response = await self.client.post(url, data=params)
        except:
            # 回退到 GET 请求
            response = await self.client.get(f"{url}?{urlencode(params)}")
        
        response.raise_for_status()
        
        # LibreX 返回的是 HTML，需要解析
        # 这里假设有 API 端点返回 JSON
        content_type = response.headers.get("content-type", "")
        
        if "json" in content_type:
            data = response.json()
            results = []
            for item in data.get("results", [])[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("description", ""),
                    engine="librex",
                    score=None
                ))
        else:
            # HTML 响应 - 需要解析（这里简化处理）
            logger.warning("LibreX返回HTML，需要额外解析")
            results = []
        
        logger.info(f"LibreX搜索完成: 找到 {len(results)} 条结果")
        return results

    async def _search_4get(
        self,
        query: str,
        num_results: int,
        category: Optional[str],
        language: Optional[str]
    ) -> List[SearchResult]:
        """使用4get搜索"""
        # 4get API 格式
        params = {
            "q": query,
            "n": num_results,
            "t": category or "web",
        }
        
        if language:
            params["lang"] = language

        url = f"{self.config.base_url}/web?{urlencode(params)}"
        
        logger.debug(f"4get搜索: {query}")
        response = await self.client.get(url)
        response.raise_for_status()
        
        # 4get 也返回 HTML，需要解析
        content_type = response.headers.get("content-type", "")
        
        if "json" in content_type:
            data = response.json()
            results = []
            for item in data.get("results", [])[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("description", ""),
                    engine="4get",
                    score=None
                ))
        else:
            logger.warning("4get返回HTML，需要额外解析")
            results = []
        
        logger.info(f"4get搜索完成: 找到 {len(results)} 条结果")
        return results

    async def search_with_fallback(
        self,
        query: str,
        fallback_configs: List[SearchConfig],
        num_results: int = 10
    ) -> List[SearchResult]:
        """
        带故障转移的搜索
        
        Args:
            query: 搜索查询
            fallback_configs: 备用搜索配置列表
            num_results: 结果数量
            
        Returns:
            List[SearchResult]: 搜索结果
        """
        # 首先尝试主搜索
        try:
            results = await self.search(query, num_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"主搜索失败: {e}")

        # 尝试备用搜索
        for config in fallback_configs:
            try:
                fallback_service = SearchService(config)
                results = await fallback_service.search(query, num_results)
                await fallback_service.close()
                
                if results:
                    logger.info(f"使用备用搜索引擎: {config.provider.value}")
                    return results
            except Exception as e:
                logger.warning(f"备用搜索失败 ({config.provider.value}): {e}")
                continue

        logger.error("所有搜索引擎均失败")
        return []

    async def get_suggestions(self, query: str) -> List[str]:
        """
        获取搜索建议
        
        Args:
            query: 搜索查询前缀
            
        Returns:
            List[str]: 建议列表
        """
        if not query.strip():
            return []

        try:
            if self.config.provider == SearchProvider.SEARXNG:
                # SearXNG 自动补全
                params = {
                    "q": query,
                    "format": "json",
                    "autocomplete": "google",  # 或 'duckduckgo', 'bing'
                }
                url = f"{self.config.base_url}/autocompleter?{urlencode(params)}"
                
                response = await self.client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("suggestions", [])[:10]
            
            return []
        except Exception as e:
            logger.debug(f"获取搜索建议失败: {e}")
            return []

    async def get_engines(self) -> List[Dict[str, Any]]:
        """
        获取可用的搜索引擎列表
        
        Returns:
            List[Dict]: 引擎列表
        """
        try:
            if self.config.provider == SearchProvider.SEARXNG:
                url = f"{self.config.base_url}/config"
                response = await self.client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("engines", [])
            
            return []
        except Exception as e:
            logger.debug(f"获取引擎列表失败: {e}")
            return []

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class SearchError(Exception):
    """搜索服务错误"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class SearchServiceFactory:
    """搜索服务工厂"""

    _instances: Dict[str, SearchService] = {}

    @classmethod
    def create(
        cls,
        provider: SearchProvider,
        base_url: str,
        timeout: int = 30,
        categories: Optional[List[str]] = None,
        language: str = "zh-CN",
        **kwargs
    ) -> SearchService:
        """创建搜索服务实例"""
        config = SearchConfig(
            provider=provider,
            base_url=base_url,
            timeout=timeout,
            categories=categories,
            language=language,
            **kwargs
        )
        return SearchService(config)

    @classmethod
    def get_or_create(cls, key: str, **kwargs) -> SearchService:
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
def create_searxng_service(
    base_url: str = "http://localhost:8080",
    categories: Optional[List[str]] = None,
    language: str = "zh-CN"
) -> SearchService:
    """创建SearXNG搜索服务"""
    return SearchServiceFactory.create(
        provider=SearchProvider.SEARXNG,
        base_url=base_url,
        categories=categories,
        language=language
    )


def create_librex_service(
    base_url: str = "http://localhost:8081",
    language: str = "zh-CN"
) -> SearchService:
    """创建LibreX搜索服务"""
    return SearchServiceFactory.create(
        provider=SearchProvider.LIBREX,
        base_url=base_url,
        language=language
    )


def create_4get_service(
    base_url: str = "http://localhost:8082",
    language: str = "zh-CN"
) -> SearchService:
    """创建4get搜索服务"""
    return SearchServiceFactory.create(
        provider=SearchProvider.FOURGET,
        base_url=base_url,
        language=language
    )
