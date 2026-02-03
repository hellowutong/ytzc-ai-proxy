# 向量化处理 - 提示词模板

## 输入内容

```yaml
source_content: |
  {原始文本内容}
source_metadata:
  document_id: "{文档ID}"
  source_url: "{来源URL}"
  title: "{文档标题}"
  author: "{作者}"
  created_at: "{创建时间}"
  updated_at: "{更新时间}"

chunk_config:
  chunk_size: {分块大小}
  chunk_overlap: {重叠大小}
  separators: {分隔符列表}
  encoding: "{编码格式}"

vector_config:
  embedding_model: "{嵌入模型}"
  collection_name: "{向量集合名称}"
  metadata_schema: {元数据Schema}
```

## 生成要求

1. **文本预处理**
   - 清理特殊字符和格式标记
   - 统一术语和表述
   - 保留段落结构和逻辑关系

2. **智能分块**
   - 按语义段落进行分块
   - 每个块保持完整的逻辑单元
   - 确保分块大小在配置范围内
   - 适当处理跨页/跨段内容

3. **向量生成**
   - 为每个文本块生成语义向量
   - 保留关键元数据
   - 支持后续相似度搜索

## 模板变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{source_content}` | 待处理的原始文本 | "AI人工智能技术..." |
| `{document_id}` | 文档唯一标识符 | "doc_001" |
| `{source_url}` | 原始来源URL | "https://example.com" |
| `{title}` | 文档标题 | "AI技术发展报告" |
| `{chunk_size}` | 分块大小 | 1000 |
| `{chunk_overlap}` | 分块重叠大小 | 200 |

## 输出格式

```yaml
vectorization_result:
  document_id: "{文档ID}"
  total_chunks: {总分块数}
  processing_time_ms: {处理时间(毫秒)}
  chunks:
    - chunk_id: "{块ID}"
      content: "{分块后的文本内容}"
      content_length: {内容长度}
      start_char: {起始字符位置}
      end_char: {结束字符位置}
      vector:
        model: "{嵌入模型}"
        dimensions: {向量维度}
        values: [向量值列表]
      metadata:
        source_title: "{来源标题}"
        chunk_index: {块索引}
        page_number: {页码}
      keywords: [关键词列表]
    - chunk_id: "{块ID}"
      content: "{分块后的文本内容}"
      # ... 重复上述结构
  quality_metrics:
    avg_chunk_length: {平均块长度}
    coverage_ratio: {覆盖率}
    semantic_coherence: {语义连贯性}
```

## 向量化示例

```yaml
vectorization_result:
  document_id: "doc_001"
  total_chunks: 5
  processing_time_ms: 1523
  chunks:
    - chunk_id: "chunk_001"
      content: "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。"
      content_length: 86
      start_char: 0
      end_char: 86
      vector:
        model: "BAAI/bge-large-zh"
        dimensions: 1024
        values: [0.123, 0.456, -0.789, ...]
      metadata:
        source_title: "AI技术发展报告"
        chunk_index: 0
        page_number: 1
      keywords: ["人工智能", "AI", "智能机器", "计算机科学"]
```

## 质量检查标准

1. **分块质量**
   - 每个块至少包含完整句子
   - 避免过短（<50字符）或过长（>2000字符）的块
   - 块之间逻辑连贯

2. **向量质量**
   - 向量维度符合模型规范
   - 值范围在合理区间（通常-1到1）
   - 相似文本的向量距离应较小

3. **元数据完整性**
   - 关键字提取准确
   - 来源信息保留
   - 位置信息准确
