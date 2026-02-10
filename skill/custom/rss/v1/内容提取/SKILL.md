---
name: 内容提取
description: 从RSS文章提取正文内容
type: hybrid
priority: 85
version: "1.0.0"
input_schema:
  type: object
  properties:
    url:
      type: string
      description: 文章URL
    html:
      type: string
      description: 原始HTML内容
  required:
    - url
output_schema:
  type: object
  properties:
    title:
      type: string
    content:
      type: string
    content_format:
      type: string
      enum: ["markdown", "html", "text"]
    author:
      type: string
    published_at:
      type: string
    extract_method:
      type: string
---

# RSS内容提取 Skill

## 功能说明

从RSS文章URL提取完整的正文内容。

## 提取方法

1. **readability-lxml**: 主提取算法
2. **fallback**: 使用meta标签和文本密度
3. **manual**: 特殊站点规则

## 使用示例

**输入:**
```json
{
  "url": "https://example.com/article/123"
}
```

**输出:**
```json
{
  "title": "文章标题",
  "content": "# 文章标题\n\n正文内容...",
  "content_format": "markdown",
  "author": "作者名",
  "published_at": "2024-01-15T10:00:00Z",
  "extract_method": "readability"
}
```
