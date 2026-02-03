---
name: vectorizer
description: 将文本内容转换为向量嵌入，存储到向量数据库。使用场景：为会话、技能等内容创建向量索引，支持语义搜索。
version: "1.0"
author: TW AI Saver
tags: [vector, embedding, storage, search, automation]
---

# Vectorizer

将文本内容转换为向量嵌入，存储到向量数据库以支持语义搜索。

## 使用时机

- 会话结束后需要创建向量索引
- Skill 内容需要向量化存储
- 批量处理历史数据创建搜索索引
- 为知识库构建向量检索能力

## 指令

1. **内容预处理**
   - 清理文本，移除无关字符
   - 保留代码块和关键格式化
   - 分割长文本为合适片段

2. **向量化处理**
   - 选择合适的 embedding 模型
   - 调用模型生成向量
   - 确保向量质量

3. **存储配置**
   - 确定目标集合名称
   - 设置元数据字段
   - 配置相似度度量方式

4. **验证存储**
   - 验证向量维度正确
   - 确认存储成功
   - 返回向量 ID

## 约束条件

- 单次处理文本不超过 8192 tokens
- 向量维度需与模型匹配
- 元数据需包含来源信息
- 支持批量处理（最多100条）

## 输出格式

```json
{
  "collection": "sessions",
  "vector_id": "vec_xxx",
  "dimension": 1024,
  "status": "stored"
}
```
