---
name: 文档解析
description: 解析PDF/Word/图片文档，提取文本内容
type: hybrid
priority: 85
version: "1.0.0"
input_schema:
  type: object
  properties:
    file_path:
      type: string
      description: 文档路径
    file_type:
      type: string
      enum: ["pdf", "doc", "docx", "txt", "jpg", "jpeg", "png"]
    ocr_language:
      type: string
      default: "chi_sim+eng"
  required:
    - file_path
    - file_type
output_schema:
  type: object
  properties:
    text:
      type: string
    pages:
      type: integer
    metadata:
      type: object
    structured_data:
      type: array
---

# 文档解析 Skill

## 功能说明

解析各种格式的文档，提取文本内容和元数据。

## 支持的格式

- **PDF**: PyPDF2/pdfplumber
- **Word**: python-docx
- **图片**: Tesseract OCR
- **文本**: 直接读取

## 使用示例

**输入:**
```json
{
  "file_path": "/upload/textfile/doc.pdf",
  "file_type": "pdf"
}
```

**输出:**
```json
{
  "text": "文档完整文本内容...",
  "pages": 10,
  "metadata": {
    "title": "文档标题",
    "author": "作者"
  },
  "structured_data": [...]
}
```
