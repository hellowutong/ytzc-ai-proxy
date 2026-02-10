---
name: 转录处理
description: 音频转录后的处理Skill，格式化输出并提取关键信息
type: llm-based
priority: 70
version: "1.0.0"
model: "small"
input_schema:
  type: object
  properties:
    transcription:
      type: string
      description: Whisper转录的原始文本
    language:
      type: string
      default: "zh"
    process_type:
      type: string
      enum: ["format", "summarize", "extract"]
      default: "format"
  required:
    - transcription
output_schema:
  type: object
  properties:
    processed_text:
      type: string
    segments:
      type: array
    key_points:
      type: array
    duration_ms:
      type: integer
---

# 音频转录处理 Skill

## 功能说明

对Whisper转录结果进行后处理，包括格式化、摘要和要点提取。

## 处理类型

- **format**: 格式化文本（修正标点、分段）
- **summarize**: 生成摘要
- **extract**: 提取关键信息

## 使用示例

**输入:**
```json
{
  "transcription": "呃 今天我们要讨论的是...",
  "language": "zh",
  "process_type": "format"
}
```

**输出:**
```json
{
  "processed_text": "今天我们要讨论的是...",
  "segments": [...],
  "key_points": [...],
  "duration_ms": 120
}
```
