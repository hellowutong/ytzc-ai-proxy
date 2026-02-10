# API设计文档 - ytzc-ai-proxy

**基础URL**: `http://localhost:8000`  
**协议**: HTTP (本地部署，无HTTPS)  
**认证**: 无  
**数据格式**: JSON  
**编码**: UTF-8

---

## 1. 虚拟AI代理API

### 1.1 对话接口

**POST** `/proxy/ai/v1/chat/completions`

**请求头**:
```http
Content-Type: application/json
Authorization: Bearer {proxy_key}  # config.yml中的proxy_key
```

**请求体** (OpenAI兼容格式):
```json
{
  "model": "demo1",              # 虚拟模型名称
  "messages": [
    {"role": "system", "content": "你是AI助手"},
    {"role": "user", "content": "你好"}
  ],
  "stream": true,                # 是否流式响应
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**响应** (非流式):
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "demo1",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "你好！我是AI助手。"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**响应** (流式-SSE):
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"你好"}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"！"}}]}

data: [DONE]
```

**错误响应**:
```json
{
  "error": {
    "message": "Invalid proxy_key",
    "type": "authentication_error",
    "code": 401
  }
}
```

---

### 1.2 模型列表

**GET** `/proxy/ai/v1/models`

**请求头**:
```http
Authorization: Bearer {proxy_key}
```

**响应**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "demo1",
      "object": "model",
      "created": 1704067200,
      "owned_by": "ai-gateway"
    },
    {
      "id": "demo2",
      "object": "model",
      "created": 1704067200,
      "owned_by": "ai-gateway"
    }
  ]
}
```

---

### 1.3 向量嵌入

**POST** `/proxy/ai/v1/embeddings`

**请求体**:
```json
{
  "model": "demo1",
  "input": "要嵌入的文本"
}
```

**响应**:
```json
{
  "object": "list",
  "data": [{
    "object": "embedding",
    "embedding": [0.0023064255, -0.009327292, ...],
    "index": 0
  }],
  "model": "BAAI/bge-m3",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

---

## 2. 后台管理API

### 2.1 看板（Dashboard）

#### 2.1.1 统计数据

**GET** `/admin/ai/v1/dashboard/stats`

**响应**:
```json
{
  "virtual_models": {
    "total": 5,
    "active": 4
  },
  "conversations_today": 128,
  "knowledge_documents": 1024,
  "media_queue": {
    "pending": 3,
    "processing": 2,
    "completed": 150
  },
  "rss_subscriptions": {
    "total": 10,
    "active": 8
  },
  "timestamp": "2026-02-09T14:30:00Z"
}
```

#### 2.1.2 系统健康检查

**GET** `/admin/ai/v1/dashboard/health`

**响应**:
```json
{
  "status": "healthy",  # healthy/degraded/unhealthy
  "services": {
    "mongodb": {
      "status": "healthy",
      "latency_ms": 5,
      "last_check": "2026-02-09T14:30:00Z"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "last_check": "2026-02-09T14:30:00Z"
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 8,
      "last_check": "2026-02-09T14:30:00Z"
    }
  }
}
```

#### 2.1.3 最近活动

**GET** `/admin/ai/v1/dashboard/activities?limit=20`

**查询参数**:
- `limit`: 返回数量 (默认20，最大100)
- `type`: 筛选类型 (config/skill/model/media/rss)

**响应**:
```json
{
  "activities": [
    {
      "id": "act_001",
      "timestamp": "2026-02-09T14:25:00Z",
      "type": "config",
      "action": "更新虚拟模型配置",
      "details": {"model_name": "demo1"},
      "status": "success"
    },
    {
      "id": "act_002",
      "timestamp": "2026-02-09T14:20:00Z",
      "type": "skill",
      "action": "重载Skill",
      "details": {"skill_category": "router"},
      "status": "success"
    }
  ],
  "total": 150
}
```

---

### 2.2 配置管理

#### 2.2.1 获取配置

**GET** `/admin/ai/v1/config`

**响应**:
```json
{
  "config": "完整的config.yml内容字符串",
  "format": "yaml",
  "last_modified": "2026-02-09T10:00:00Z",
  "is_valid": true
}
```

#### 2.2.2 更新配置

**PUT** `/admin/ai/v1/config`

**请求体**:
```json
{
  "config": "新的config.yml完整内容"
}
```

**响应**:
```json
{
  "success": true,
  "message": "配置已更新并重载",
  "validation_errors": [],
  "timestamp": "2026-02-09T14:30:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "配置验证失败",
  "validation_errors": [
    {"path": "ai-gateway.virtual_models.demo1.small.api_key", "message": "不能为空"}
  ]
}
```

#### 2.2.3 重载配置

**POST** `/admin/ai/v1/config/reload`

**响应**:
```json
{
  "success": true,
  "message": "配置已重载",
  "timestamp": "2026-02-09T14:30:00Z"
}
```

#### 2.2.4 验证配置

**POST** `/admin/ai/v1/config/validate`

**请求体**:
```json
{
  "config": "要验证的config.yml内容"
}
```

**响应**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["建议设置redis密码"]
}
```

---

### 2.3 虚拟模型管理

#### 2.3.1 列表

**GET** `/admin/ai/v1/models`

**响应**:
```json
{
  "models": [
    {
      "name": "demo1",
      "proxy_key_masked": "sk-xxx...abc",  # 掩码显示
      "proxy_key_full": "sk-xxxxxxxxxxxxxxxx",  # 完整key
      "base_url": "http://192.168.1.100:8000/proxy/v1",
      "current": "small",
      "force_current": false,
      "use": true,
      "small": {
        "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "base_url": "https://api.siliconflow.cn/v1"
      },
      "big": {
        "model": "Pro/deepseek-ai/DeepSeek-V3.2",
        "base_url": "https://api.siliconflow.cn/v1"
      },
      "knowledge": {
        "enabled": true,
        "shared": true,
        "skill": {"enabled": true, "version": "v1"},
        "skill_custom": {"enabled": false, "version": null}
      },
      "web_search": {
        "enabled": true,
        "skill": {"enabled": true, "version": "v2"},
        "skill_custom": {"enabled": false, "version": null},
        "target": ["searxng"]
      }
    }
  ]
}
```

#### 2.3.2 创建

**POST** `/admin/ai/v1/models`

**请求体**:
```json
{
  "name": "demo3",
  "proxy_key": "sk-yyyyyyyyyyyyyyyy",
  "base_url": "http://192.168.1.100:8000/proxy/v1",
  "current": "small",
  "force_current": false,
  "use": true,
  "small": {
    "model": "ollama/qwen2.5:7b",
    "api_key": "",
    "base_url": "http://localhost:11434/v1",
    "embedding_model": "nomic-embed-text"
  },
  "big": {
    "model": "openai/gpt-4o",
    "api_key": "sk-xxxxxxxxxxxxxxxx",
    "base_url": "https://api.openai.com/v1"
  },
  "knowledge": {
    "enabled": true,
    "shared": true,
    "skill": {"enabled": true, "version": "v1"},
    "skill_custom": {"enabled": false, "version": null}
  },
  "web_search": {
    "enabled": true,
    "skill": {"enabled": true, "version": "v2"},
    "skill_custom": {"enabled": false, "version": null},
    "target": ["LibreX", "4get"]
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "虚拟模型已创建",
  "model": {...}
}
```

#### 2.3.3 更新

**PUT** `/admin/ai/v1/models/{name}`

**请求体**: 同创建（部分字段可更新）

#### 2.3.4 删除

**DELETE** `/admin/ai/v1/models/{name}`

**响应**:
```json
{
  "success": true,
  "message": "虚拟模型已删除"
}
```

#### 2.3.5 刷新Proxy Key

**POST** `/admin/ai/v1/models/{name}/refresh-key`

**响应**:
```json
{
  "success": true,
  "message": "Proxy Key已刷新",
  "new_key": "sk-zzzzzzzzzzzzzzzzz",
  "new_key_masked": "sk-zzz...zzz"
}
```

#### 2.3.6 测试模型连接

**POST** `/admin/ai/v1/models/{name}/test`

**请求体**:
```json
{
  "model_type": "small"  # small或big
}
```

**响应**:
```json
{
  "success": true,
  "message": "连接成功",
  "latency_ms": 150,
  "model_info": {
    "id": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "context_window": 8192
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "连接失败",
  "error": "Connection timeout"
}
```

---

### 2.4 Skill管理

#### 2.4.1 获取Skill列表

**GET** `/admin/ai/v1/skills`

**响应**:
```json
{
  "categories": [
    {
      "name": "router",
      "display_name": "模型路由",
      "skills": [
        {
          "name": "关键词路由",
          "version": "v1",
          "type": "rule-based",
          "system": {"enabled": true, "version": "v1"},
          "custom": {"enabled": false, "version": "v2"}
        },
        {
          "name": "意图识别",
          "version": "v1",
          "type": "llm-based",
          "system": {"enabled": true, "version": "v1"},
          "custom": {"enabled": true, "version": "v2"}
        }
      ]
    }
  ]
}
```

#### 2.4.2 获取Skill详情

**GET** `/admin/ai/v1/skills/{category}/{name}`

**响应**:
```json
{
  "name": "意图识别",
  "category": "router",
  "description": "基于LLM意图识别的模型路由",
  "type": "llm-based",
  "system": {
    "enabled": true,
    "version": "v1",
    "path": "./skill/system/router/v1/意图识别",
    "has_custom": true
  },
  "custom": {
    "enabled": true,
    "version": "v2",
    "path": "./skill/custom/router/v2/意图识别",
    "content": "SKILL.md完整内容"
  },
  "input_schema": {...},
  "output_schema": {...}
}
```

#### 2.4.3 更新Skill配置

**PUT** `/admin/ai/v1/skills/{category}/{name}/config`

**请求体**:
```json
{
  "system_enabled": true,
  "system_version": "v1",
  "custom_enabled": true,
  "custom_version": "v2"
}
```

#### 2.4.4 编辑自定义Skill

**PUT** `/admin/ai/v1/skills/{category}/{name}/custom`

**请求体**:
```json
{
  "content": "新的SKILL.md内容"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Skill已更新",
  "validation": {
    "valid": true,
    "errors": []
  }
}
```

#### 2.4.5 重载所有Skill

**POST** `/admin/ai/v1/skills/reload`

**响应**:
```json
{
  "success": true,
  "message": "所有Skill重载成功",
  "reload_time_ms": 150,
  "loaded_skills": 15
}
```

#### 2.4.6 获取Skill版本列表

**GET** `/admin/ai/v1/skills/versions`

**查询参数**:
- `category`: Skill分类 (router, knowledge, web_search)
- `skill_type`: Skill类型 (system/custom, 默认system)

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "category": "router",
    "skill_type": "system",
    "versions": ["v1", "v2", "v3"]
  }
}
```

#### 2.4.6 重载单个Skill

**POST** `/admin/ai/v1/skills/{category}/{name}/reload`

**响应**:
```json
{
  "success": true,
  "message": "Skill已重载",
  "skill": "router/意图识别"
}
```

#### 2.4.7 获取Skill执行日志

**GET** `/admin/ai/v1/skills/logs?category=router&name=意图识别&limit=50`

**查询参数**:
- `category`: Skill分类
- `name`: Skill名称
- `limit`: 数量限制
- `start_time`: 开始时间 (ISO 8601)
- `end_time`: 结束时间

**响应**:
```json
{
  "logs": [
    {
      "timestamp": "2026-02-09T14:30:00Z",
      "skill_category": "router",
      "skill_name": "意图识别",
      "skill_version": "v1",
      "input": {"user_input": "你好"},
      "output": {"model_type": "small", "confidence": 0.95},
      "duration_ms": 120,
      "status": "success"
    }
  ],
  "total": 150
}
```

#### 2.4.8 获取Skill执行统计

**GET** `/admin/ai/v1/skills/stats`

**响应**:
```json
{
  "stats": [
    {
      "category": "router",
      "name": "意图识别",
      "total_calls": 1024,
      "success_rate": 0.98,
      "avg_duration_ms": 150
    }
  ]
}
```

---

### 2.5 对话历史

#### 2.5.1 列表

**GET** `/admin/ai/v1/conversations?model=demo1&start_time=xxx&end_time=xxx&limit=20&offset=0`

**查询参数**:
- `model`: 虚拟模型名称
- `start_time`: 开始时间
- `end_time`: 结束时间
- `keyword`: 关键词搜索
- `has_knowledge`: 是否有知识库引用 (true/false)
- `limit`: 数量限制
- `offset`: 偏移量

**响应**:
```json
{
  "conversations": [
    {
      "id": "conv_001",
      "model": "demo1",
      "message_count": 10,
      "last_message_time": "2026-02-09T14:30:00Z",
      "preview": "用户: 你好\nAI: 你好！..."
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### 2.5.2 详情

**GET** `/admin/ai/v1/conversations/{id}`

**响应**:
```json
{
  "id": "conv_001",
  "model": "demo1",
  "created_at": "2026-02-09T14:00:00Z",
  "updated_at": "2026-02-09T14:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2026-02-09T14:00:05Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "你好！我是AI助手。",
      "timestamp": "2026-02-09T14:00:08Z",
      "metadata": {
        "model_used": "small",
        "knowledge_references": [...],
        "routing_decision": {...}
      }
    }
  ]
}
```

#### 2.5.3 导出

**GET** `/admin/ai/v1/conversations/{id}/export?format=json`

**查询参数**:
- `format`: 导出格式 (json/markdown)

**响应**: 文件下载

#### 2.5.4 删除

**DELETE** `/admin/ai/v1/conversations/{id}`

---

### 2.6 知识库管理

#### 2.6.1 文档列表

**GET** `/admin/ai/v1/knowledge/documents?type=pdf&source=upload&limit=20`

**查询参数**:
- `type`: 文档类型 (pdf/txt/doc/jpg)
- `source`: 来源 (upload/rss/conversation)
- `keyword`: 关键词
- `start_time`: 开始时间
- `end_time`: 结束时间
- `limit`: 数量
- `offset`: 偏移量

**响应**:
```json
{
  "documents": [
    {
      "id": "doc_001",
      "filename": "设计文档.pdf",
      "type": "pdf",
      "source": "upload",
      "virtual_model": "demo1",
      "is_shared": true,
      "vectorized": true,
      "chunk_count": 5,
      "upload_time": "2026-02-09T10:00:00Z",
      "size_bytes": 1024000
    }
  ],
  "total": 100
}
```

#### 2.6.2 上传文档

**POST** `/admin/ai/v1/knowledge/documents`

**请求体** (multipart/form-data):
```
file: [二进制文件]
virtual_model: "demo1"
is_shared: "true"
chunk_size: "500"
overlap: "50"
language: "zh"
```

**响应**:
```json
{
  "success": true,
  "document_id": "doc_001",
  "filename": "设计文档.pdf",
  "message": "文档上传成功，正在向量化"
}
```

#### 2.6.3 预览文档

**GET** `/admin/ai/v1/knowledge/documents/{id}/preview`

**响应**:
```json
{
  "id": "doc_001",
  "content": "文档内容预览...",
  "chunks": [
    {"index": 0, "content": "第一段...", "vectorized": true},
    {"index": 1, "content": "第二段...", "vectorized": true}
  ]
}
```

#### 2.6.4 重新向量化

**POST** `/admin/ai/v1/knowledge/documents/{id}/revectorize`

**响应**:
```json
{
  "success": true,
  "message": "重新向量化任务已提交"
}
```

#### 2.6.5 删除文档

**DELETE** `/admin/ai/v1/knowledge/documents/{id}`

#### 2.6.6 获取知识库配置

**GET** `/admin/ai/v1/knowledge/config`

**响应**:
```json
{
  "embedding": {
    "model": "BAAI/bge-m3",
    "base_url": "https://api.siliconflow.cn/v1",
    "api_key": "sk-xxx"  # 掩码显示
  },
  "scheduler": {
    "cron": "*/30 * * * *",
    "enabled": false
  },
  "skills": {
    "extraction": {
      "system": {"enabled": true, "version": "v1"},
      "custom": {"enabled": true, "version": "v2"}
    },
    "topics": {
      "system": {"enabled": true, "version": "v1"},
      "custom": {"enabled": true, "version": "v2"}
    }
  },
  "topics": {
    "auto_classify": [
      {"topic": "项目架构", "patterns": ["架构", "设计", "结构"]}
    ],
    "self_classify": [
      {"topic": "股票情绪", "patterns": ["股票", "热度"]}
    ]
  }
}
```

#### 2.6.7 更新知识库配置

**PUT** `/admin/ai/v1/knowledge/config`

**请求体**:
```json
{
  "embedding": {
    "model": "BAAI/bge-m3",
    "base_url": "https://api.siliconflow.cn/v1",
    "api_key": "sk-xxx"
  },
  "scheduler": {
    "cron": "*/30 * * * *",
    "enabled": true
  },
  "skills": {...},
  "topics": {...}
}
```

#### 2.6.8 测试向量连接

**POST** `/admin/ai/v1/knowledge/test-embedding`

**响应**:
```json
{
  "success": true,
  "message": "向量服务连接成功",
  "latency_ms": 120,
  "test_vector_size": 1024
}
```

#### 2.6.9 向量检索测试

**POST** `/admin/ai/v1/knowledge/search-test`

**请求体**:
```json
{
  "query": "项目架构设计",
  "threshold": 0.76,
  "top_k": 5
}
```

**响应**:
```json
{
  "results": [
    {
      "document_id": "doc_001",
      "chunk_index": 0,
      "content": "项目采用微服务架构...",
      "score": 0.89,
      "metadata": {...}
    }
  ]
}
```

---

### 2.7 媒体处理

#### 2.7.1 列表

**GET** `/admin/ai/v1/media/{type}?status=pending&limit=20`

**路径参数**:
- `type`: video/audio/text

**查询参数**:
- `status`: pending/processing/completed/failed
- `limit`: 数量
- `offset`: 偏移量

**响应**:
```json
{
  "items": [
    {
      "id": "media_001",
      "filename": "会议录音.mp3",
      "type": "audio",
      "status": "completed",
      "size_bytes": 5242880,
      "transcription": {
        "processor": "whisper",
        "model": "base",
        "language": "zh",
        "text_length": 1500,
        "completed_at": "2026-02-09T14:30:00Z"
      },
      "progress": 100,
      "upload_time": "2026-02-09T14:00:00Z"
    }
  ],
  "total": 50
}
```

#### 2.7.2 上传文件

**POST** `/admin/ai/v1/media/{type}/upload`

**请求体** (multipart/form-data):
```
file: [二进制文件]
processor: "whisper"
model: "base"
language: "zh"
auto_transcribe: "true"
```

#### 2.7.3 URL下载

**POST** `/admin/ai/v1/media/{type}/download`

**请求体**:
```json
{
  "url": "https://example.com/video.mp4",
  "processor": "whisper",
  "model": "base",
  "language": "zh",
  "auto_transcribe": true
}
```

#### 2.7.4 查看转录文本

**GET** `/admin/ai/v1/media/{id}/transcription`

**响应**:
```json
{
  "id": "media_001",
  "text": "完整的转录文本...",
  "segments": [
    {"start": 0, "end": 10, "text": "第一段"},
    {"start": 10, "end": 20, "text": "第二段"}
  ],
  "language": "zh",
  "duration_seconds": 300
}
```

#### 2.7.5 重新转录

**POST** `/admin/ai/v1/media/{id}/retranscribe`

**请求体**:
```json
{
  "processor": "whisper",
  "model": "small",
  "language": "zh"
}
```

#### 2.7.6 删除

**DELETE** `/admin/ai/v1/media/{id}`

#### 2.7.7 获取Skill配置

**GET** `/admin/ai/v1/media/{type}/skill-config`

**响应**:
```json
{
  "type": "audio",
  "system": {"enabled": true, "version": "v1"},
  "custom": {"enabled": true, "version": "v2"}
}
```

#### 2.7.8 更新Skill配置

**PUT** `/admin/ai/v1/media/{type}/skill-config`

**请求体**:
```json
{
  "system_enabled": true,
  "system_version": "v1",
  "custom_enabled": true,
  "custom_version": "v2"
}
```

---

### 2.8 RSS订阅管理

#### 2.8.1 订阅源列表

**GET** `/admin/ai/v1/rss/subscriptions?status=active&limit=20`

**查询参数**:
- `status`: active/inactive/all
- `keyword`: 搜索关键词

**响应**:
```json
{
  "subscriptions": [
    {
      "id": "rss_001",
      "name": "AI新闻",
      "url": "https://news.ai.com/feed.xml",
      "enabled": true,
      "fetch_interval": 30,
      "retention_days": 30,
      "default_permanent": false,
      "virtual_model": "demo1",
      "article_count": 150,
      "last_fetch_time": "2026-02-09T14:00:00Z",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 10
}
```

#### 2.8.2 创建订阅

**POST** `/admin/ai/v1/rss/subscriptions`

**请求体**:
```json
{
  "name": "技术博客",
  "url": "https://blog.example.com/feed.xml",
  "enabled": true,
  "fetch_interval": 60,
  "retention_days": 30,
  "default_permanent": false,
  "virtual_model": "demo1"
}
```

#### 2.8.3 更新订阅

**PUT** `/admin/ai/v1/rss/subscriptions/{id}`

#### 2.8.4 删除订阅

**DELETE** `/admin/ai/v1/rss/subscriptions/{id}`

#### 2.8.5 立即抓取

**POST** `/admin/ai/v1/rss/subscriptions/{id}/fetch`

**响应**:
```json
{
  "success": true,
  "message": "抓取任务已提交",
  "fetch_id": "fetch_001"
}
```

#### 2.8.6 批量导入

**POST** `/admin/ai/v1/rss/subscriptions/import`

**请求体** (multipart/form-data):
```
file: [OPML文件]
```

**响应**:
```json
{
  "success": true,
  "imported": 5,
  "failed": 0
}
```

#### 2.8.7 获取文章列表

**GET** `/admin/ai/v1/rss/subscriptions/{id}/articles?limit=20&status=unread`

**查询参数**:
- `status`: all/unread/read
- `limit`: 数量
- `offset`: 偏移量

**响应**:
```json
{
  "articles": [
    {
      "id": "article_001",
      "title": "AI最新进展",
      "url": "https://news.ai.com/article/1",
      "content": "完整的文章内容...",  # 爬取的完整内容
      "summary": "摘要...",
      "published_at": "2026-02-09T10:00:00Z",
      "fetched_at": "2026-02-09T14:00:00Z",
      "is_read": false,
      "knowledge_extracted": true,
      "fetch_status": "full_content"  # full_content/summary_only/failed
    }
  ],
  "total": 150
}
```

#### 2.8.8 查看文章详情

**GET** `/admin/ai/v1/rss/articles/{id}`

**响应**:
```json
{
  "id": "article_001",
  "title": "AI最新进展",
  "url": "https://news.ai.com/article/1",
  "content": "完整的HTML/Markdown内容",
  "content_format": "markdown",  # html/markdown/plain
  "published_at": "2026-02-09T10:00:00Z",
  "knowledge_references": [...]
}
```

#### 2.8.9 标记已读/未读

**PUT** `/admin/ai/v1/rss/articles/{id}/read`

**请求体**:
```json
{
  "is_read": true
}
```

#### 2.8.10 删除文章

**DELETE** `/admin/ai/v1/rss/articles/{id}`

#### 2.8.11 获取Skill配置

**GET** `/admin/ai/v1/rss/skill-config`

**响应**:
```json
{
  "system": {"enabled": true, "version": "v1"},
  "custom": {"enabled": true, "version": "v2"}
}
```

#### 2.8.12 更新Skill配置

**PUT** `/admin/ai/v1/rss/skill-config`

---

### 2.9 日志查询

#### 2.9.1 系统日志

**GET** `/admin/ai/v1/logs/system?level=INFO&start_time=xxx&end_time=xxx&keyword=error&limit=100`

**查询参数**:
- `level`: DEBUG/INFO/WARNING/ERROR
- `start_time`: 开始时间
- `end_time`: 结束时间
- `keyword`: 关键词
- `limit`: 数量

**响应**:
```json
{
  "logs": [
    {
      "timestamp": "2026-02-09T14:30:00Z",
      "level": "INFO",
      "module": "skill.executor",
      "message": "Skill执行成功: router/意图识别",
      "context": {...}
    }
  ],
  "total": 1000
}
```

#### 2.9.2 操作日志

**GET** `/admin/ai/v1/logs/operation?type=config&status=success&limit=100`

**查询参数**:
- `type`: config/skill/model/media/rss
- `status`: success/failed
- `start_time`: 开始时间
- `end_time`: 结束时间
- `limit`: 数量

**响应**:
```json
{
  "logs": [
    {
      "id": "op_001",
      "timestamp": "2026-02-09T14:30:00Z",
      "type": "config",
      "action": "更新虚拟模型配置",
      "details": {"model_name": "demo1"},
      "status": "success",
      "operator": "admin"  # 本地部署可能为空
    }
  ],
  "total": 500
}
```

#### 2.9.3 Skill执行日志

**GET** `/admin/ai/v1/logs/skill?category=router&status=success&limit=100`

**查询参数**:
- `category`: Skill分类
- `name`: Skill名称
- `status`: success/failed/validation_error
- `start_time`: 开始时间
- `end_time`: 结束时间
- `limit`: 数量

**响应**:
```json
{
  "logs": [
    {
      "log_id": "skill_001",
      "timestamp": "2026-02-09T14:30:00Z",
      "skill_category": "router",
      "skill_name": "意图识别",
      "skill_version": "v1",
      "skill_type": "llm-based",
      "input": {"user_input": "你好"},
      "output": {"model_type": "small", "confidence": 0.95},
      "duration_ms": 120,
      "status": "success",
      "llm_model": "gpt-3.5-turbo",
      "llm_tokens_input": 50,
      "llm_tokens_output": 20
    }
  ],
  "total": 2000
}
```

#### 2.9.4 日志详情

**GET** `/admin/ai/v1/logs/{log_id}`

**响应**:
```json
{
  "log_id": "skill_001",
  "full_input": {...},
  "full_output": {...},
  "error_traceback": null,
  "metadata": {...}
}
```

#### 2.9.5 导出日志

**GET** `/admin/ai/v1/logs/export?type=system&start_time=xxx&end_time=xxx&format=json`

**查询参数**:
- `type`: system/operation/skill
- `format`: json/csv

**响应**: 文件下载

---

### 2.10 原始数据

#### 2.10.1 会话原始数据

**GET** `/admin/ai/v1/raw-data/conversations?model=demo1&start_time=xxx&limit=50`

**查询参数**:
- `model`: 虚拟模型
- `start_time`: 开始时间
- `end_time`: 结束时间
- `keyword`: 关键词
- `limit`: 数量

**响应**:
```json
{
  "records": [
    {
      "timestamp": "2026-02-09T14:30:00Z",
      "type": "user_input",
      "conversation_id": "conv_001",
      "model": "demo1",
      "data": {"content": "你好", "metadata": {...}}
    },
    {
      "timestamp": "2026-02-09T14:30:05Z",
      "type": "ai_response",
      "conversation_id": "conv_001",
      "model": "demo1",
      "data": {"content": "你好！", "model_used": "small", "knowledge_refs": [...]}
    },
    {
      "timestamp": "2026-02-09T14:30:05Z",
      "type": "routing_decision",
      "conversation_id": "conv_001",
      "data": {"from": "small", "to": "big", "reason": "复杂问题"}
    }
  ],
  "total": 1000
}
```

#### 2.10.2 多媒体原始数据

**GET** `/admin/ai/v1/raw-data/media/{type}?status=completed&limit=50`

**响应**:
```json
{
  "records": [
    {
      "id": "media_001",
      "type": "audio",
      "filename": "录音.mp3",
      "raw_transcription": {
        "text": "完整转录文本",
        "segments": [...],
        "language": "zh"
      },
      "knowledge_extraction": {
        "extracted": true,
        "chunks": [...],
        "stored_in_qdrant": true
      },
      "created_at": "2026-02-09T14:00:00Z"
    }
  ]
}
```

#### 2.10.3 RSS原始数据

**GET** `/admin/ai/v1/raw-data/rss?subscription_id=xxx&limit=50`

**响应**:
```json
{
  "records": [
    {
      "id": "article_001",
      "subscription_id": "rss_001",
      "subscription_name": "AI新闻",
      "title": "AI进展",
      "url": "https://news.ai.com/article/1",
      "raw_content": "完整的原始HTML",
      "cleaned_content": "清洗后的正文",
      "content_format": "html",
      "knowledge_extraction": {...},
      "fetch_metadata": {
        "fetch_time": "2026-02-09T14:00:00Z",
        "fetch_method": "readability",
        "success": true
      }
    }
  ]
}
```

---

## 3. 通用规范

### 3.1 请求格式

- **Content-Type**: `application/json` (除文件上传)
- **编码**: UTF-8
- **时间格式**: ISO 8601 (如 `2026-02-09T14:30:00Z`)

### 3.2 响应格式

**成功响应**:
```json
{
  "data": {...},  # 或直接在根级别
  "message": "操作成功"
}
```

**错误响应**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {...}  # 可选
  }
}
```

**HTTP状态码**:
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 认证失败（代理key错误）
- `404`: 资源不存在
- `500`: 服务器内部错误

### 3.3 分页规范

列表接口统一使用:
- `limit`: 每页数量 (默认20，最大100)
- `offset`: 偏移量 (从0开始)

**响应**:
```json
{
  "items": [...],
  "total": 1000,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### 3.4 字段命名规范

- **蛇形命名法** (snake_case): `virtual_model`, `proxy_key`
- **布尔值**: 使用 `true`/`false`，字段名如 `is_enabled`, `has_custom`
- **时间字段**: 以 `_at` 或 `_time` 结尾: `created_at`, `last_fetch_time`
- **状态字段**: 使用名词: `status`, `type`, `level`

### 3.5 敏感信息处理

- **API Key**: 列表接口返回掩码格式 `sk-xxx...abc`
- **详情接口**: 可返回完整key供复制
- **日志**: 自动脱敏敏感字段

---

## 4. WebSocket (预留)

未来可能添加WebSocket支持实时推送:
- `/ws/logs` - 实时日志推送
- `/ws/media` - 转录进度推送
- `/ws/notifications` - 系统通知

---

**文档版本**: 1.0  
**最后更新**: 2026-02-09  
**状态**: 已完成，待开发实现
