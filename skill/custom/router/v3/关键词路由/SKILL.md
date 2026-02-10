---
name: 关键词路由
description: 基于关键词匹配的模型路由决策Skill，根据用户输入中的关键词决定使用大模型还是小模型
type: rule-based
priority: 90
version: "1.0.0"
input_schema:
  type: object
  properties:
    user_input:
      type: string
      description: 用户输入文本
  required:
    - user_input
output_schema:
  type: object
  properties:
    target:
      type: string
      enum: ["small", "big", null]
      description: 目标模型类型，null表示不匹配
    matched_rule:
      type: string
      description: 匹配的规则名称
    confidence:
      type: number
      description: 匹配置信度
---

# 关键词路由 Skill

## 功能说明

根据用户输入中的关键词，快速决定应该使用大模型还是小模型。

## 路由规则

### 小模型关键词（简单查询）
- "你好", "您好", "嗨", "hello", "hi"
- "谢谢", "感谢"
- "再见", "拜拜"
- "好的", "OK", "ok"
- "简单", "简短"

### 大模型关键词（复杂任务）
- "详细", "详细说明"
- "解释", "分析一下"
- "为什么", "什么原因"
- "比较", "对比", "vs", "versus"
- "代码", "编程", "写个程序"
- "逻辑", "推理", "证明"
- "创意", "写作", "创作"
- "翻译" + 长文本
- "总结" + 长文本
- "优化", "改进", "重构"

### 特殊模式
- 数学计算：包含数字+运算符 → 大模型
- 代码相关：包含代码片段 → 大模型
- 多语言：检测非中文输入 → 大模型

## 使用示例

**输入:**
```json
{
  "user_input": "你好"
}
```

**输出:**
```json
{
  "target": "small",
  "matched_rule": "问候语",
  "confidence": 1.0
}
```

**输入:**
```json
{
  "user_input": "请详细解释一下量子计算的原理"
}
```

**输出:**
```json
{
  "target": "big",
  "matched_rule": "详细说明",
  "confidence": 0.95
}
```

## 执行逻辑

1. 小模型关键词匹配（优先）
2. 大模型关键词匹配
3. 特殊模式检测
4. 返回匹配结果
