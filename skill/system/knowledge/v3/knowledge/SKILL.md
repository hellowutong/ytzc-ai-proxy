---
name: knowledge
description: 知识库检索Skill，根据用户查询从向量数据库检索相关知识
type: llm-based
priority: 80
version: "1.0.0"
model: "small"
input_schema:
  type: object
  properties:
    query:
      type: string
      description: 用户查询
    virtual_model:
      type: string
      description: 虚拟模型名称
    top_k:
      type: integer
      default: 5
      description: 返回结果数量
    threshold:
      type: number
      default: 0.76
      description: 相似度阈值
  required:
    - query
    - virtual_model
output_schema:
  type: object
  properties:
    chunks:
      type: array
      items:
        type: object
        properties:
          content:
            type: string
          score:
            type: number
          source:
            type: string
    has_results:
      type: boolean
    total_found:
      type: integer
---

# 知识库检索 Skill

## 功能说明

根据用户查询，从向量数据库中检索相关知识片段。

## 执行流程

1. 获取查询的embedding
2. 在Qdrant中搜索相似向量
3. 过滤相似度阈值
4. 返回知识片段

## 使用示例

**输入:**
```json
{
  "query": "项目架构是什么样的？",
  "virtual_model": "demo1",
  "top_k": 5,
  "threshold": 0.76
}
```

**输出:**
```json
{
  "chunks": [
    {
      "content": "系统采用微服务架构，包含...",
      "score": 0.89,
      "source": "设计文档.pdf"
    }
  ],
  "has_results": true,
  "total_found": 3
}
```
