---
name: 意图识别
description: 基于LLM的意图识别路由Skill，分析用户输入的意图复杂度，决定使用大模型还是小模型
type: llm-based
priority: 70
version: "1.0.0"
model: "small"
input_schema:
  type: object
  properties:
    user_input:
      type: string
      description: 用户输入文本
    context:
      type: string
      description: 会话上下文摘要
  required:
    - user_input
output_schema:
  type: object
  properties:
    model_type:
      type: string
      enum: ["small", "big"]
      description: 推荐的模型类型
    confidence:
      type: number
      description: 置信度 0-1
    reason:
      type: string
      description: 决策理由
    fallback:
      type: boolean
      description: 是否建议回退到默认模型
---

# 意图识别 Skill

## 功能说明

使用LLM分析用户输入的意图复杂度，判断应该使用大模型还是小模型。

## 分类标准

### 小模型适用场景
- 简单问答
- 日常对话
- 明确的事实查询
- 简单指令
- 无需推理的问题

### 大模型适用场景
- 复杂推理
- 代码生成
- 创意写作
- 多步骤任务
- 需要分析的问题
- 开放式问题

## Prompt模板

```
分析以下用户输入，判断其意图复杂度：

用户输入: {user_input}
上下文: {context}

请评估：
1. 任务复杂度（1-10分）
2. 是否需要推理能力
3. 是否需要专业知识
4. 是否需要创造性思维

基于以上评估，决定使用哪个模型：
- small：适合简单任务（复杂度<5，无需推理）
- big：适合复杂任务（复杂度≥5，需要推理或创造性）

输出格式（JSON）：
{
  "model_type": "small|big",
  "confidence": 0.0-1.0,
  "reason": "决策理由",
  "fallback": false
}
```

## 使用示例

**输入:**
```json
{
  "user_input": "今天天气怎么样？",
  "context": "用户刚开始对话"
}
```

**输出:**
```json
{
  "model_type": "small",
  "confidence": 0.95,
  "reason": "简单的天气查询，不需要复杂推理",
  "fallback": false
}
```
