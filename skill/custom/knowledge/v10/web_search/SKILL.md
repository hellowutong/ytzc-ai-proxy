---
name: web_search
description: 联网搜索Skill，使用SearXNG/LibreX/4get进行网络搜索
type: llm-based
priority: 75
version: "1.0.0"
model: "small"
input_schema:
  type: object
  properties:
    query:
      type: string
      description: 搜索查询
    search_targets:
      type: array
      items:
        type: string
        enum: ["searxng", "librex", "4get"]
      default: ["searxng"]
    top_k:
      type: integer
      default: 5
      description: 返回结果数量
  required:
    - query
output_schema:
  type: object
  properties:
    results:
      type: array
      items:
        type: object
        properties:
          title:
            type: string
          url:
            type: string
          snippet:
            type: string
          source:
            type: string
    has_results:
      type: boolean
    search_time_ms:
      type: integer
---

# 联网搜索 Skill

## 功能说明

使用多个搜索引擎进行网络搜索，获取最新信息。

## 搜索引擎

- **SearXNG**: 元搜索引擎（端口8080）
- **LibreX**: 隐私搜索引擎（端口8081）
- **4get**: 去中心化搜索（端口8082）

## 执行流程

1. 并行调用配置的搜索引擎
2. 合并和去重结果
3. 排序和过滤
4. 返回搜索结果

## 使用示例

**输入:**
```json
{
  "query": "最新AI技术进展",
  "search_targets": ["searxng", "librex"],
  "top_k": 5
}
```

**输出:**
```json
{
  "results": [
    {
      "title": "2024年AI技术趋势",
      "url": "https://example.com/ai-trends",
      "snippet": "AI技术在2024年取得了重大突破...",
      "source": "searxng"
    }
  ],
  "has_results": true,
  "search_time_ms": 1200
}
```
