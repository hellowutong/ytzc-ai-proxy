---
name: 视频处理
description: 视频内容分析和处理Skill，提取关键帧和摘要
type: hybrid
priority: 70
version: "1.0.0"
input_schema:
  type: object
  properties:
    video_path:
      type: string
      description: 视频文件路径
    transcription:
      type: string
      description: 转录文本
    extract_keyframes:
      type: boolean
      default: false
  required:
    - video_path
    - transcription
output_schema:
  type: object
  properties:
    summary:
      type: string
    chapters:
      type: array
    keyframes:
      type: array
    topics:
      type: array
---

# 视频处理 Skill

## 功能说明

对视频内容进行深度分析，生成章节划分、摘要和主题标签。

## 处理流程

1. 分析转录文本结构
2. 检测话题转换点
3. 生成章节划分
4. 提取关键主题

## 使用示例

**输入:**
```json
{
  "video_path": "/upload/video/meeting.mp4",
  "transcription": "今天我们讨论三个议题...",
  "extract_keyframes": true
}
```

**输出:**
```json
{
  "summary": "会议讨论了产品规划...",
  "chapters": [
    {"title": "议题一", "start": 0, "end": 300}
  ],
  "keyframes": [...],
  "topics": ["产品规划", "技术方案"]
}
```
