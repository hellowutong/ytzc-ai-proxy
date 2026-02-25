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

**重要变更**:
- **支持流式响应**：根据虚拟模型配置的 `stream_support` 决定是否支持流式
- **ChatBox兼容**：支持OpenAI标准格式，包括 `content` 为数组的格式
- **响应格式标准化**：移除非标准字段，完全兼容OpenAI API

**请求头**:
```http
Content-Type: application/json
Authorization: Bearer {proxy_key}  # config.yml中的proxy_key
```

**请求体** (OpenAI兼容格式):
```json
{
  "model": "demo1",              # 虚拟模型名称
  "conversation_id": "conv_xxx",  // 可选，首次对话不传
  "messages": [
    {"role": "system", "content": "你是AI助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false  // 可选：true/false，根据虚拟模型配置决定是否支持
}
```

**支持的消息格式**:
```json
// 格式1: 传统字符串（WebChat）
{"role": "user", "content": "讲一个故事"}

// 格式2: 数组格式（ChatBox）
{"role": "user", "content": [{"type": "text", "text": "讲一个故事"}]}
```

**非流式响应** (`stream: false`):
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

**流式响应** (`stream: true` 且虚拟模型配置 `stream_support: true`):
```
data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", "choices": [{"delta": {"role": "assistant"}}]}

data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "Hello"}}]}

data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "!"}}]}

data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", "choices": [{"finish_reason": "stop"}]}

data: [DONE]
```

**流式支持配置**:
在 `config.yml` 中为每个虚拟模型配置：
```yaml
ai-gateway:
  virtual_models:
    demo1:
      proxy_key: xxxxxxxxxxxxxxxxxxxxx
      stream_support: true  # 是否支持流式响应
      ...
```

**注意**: 
- 如果客户端请求流式但模型不支持 (`stream_support: false`)，将降级为非流式响应
- 响应格式完全兼容OpenAI API，移除了 `conversation_id` 和 `metadata` 等非标准字段

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
  "timestamp": "2026-02-24T14:30:00Z"
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
      "last_check": "2026-02-24T14:30:00Z"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "last_check": "2026-02-24T14:30:00Z"
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 8,
      "last_check": "2026-02-24T14:30:00Z"
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
      "timestamp": "2026-02-24T14:25:00Z",
      "type": "config",
      "action": "更新虚拟模型配置",
      "details": {"model_name": "demo1"},
      "status": "success"
    },
    {
      "id": "act_002",
      "timestamp": "2026-02-24T14:20:00Z",
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
  "last_modified": "2026-02-24T10:00:00Z",
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
  "timestamp": "2026-02-24T14:30:00Z"
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
  "timestamp": "2026-02-24T14:30:00Z"
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

#### 2.2.5 获取路由配置

**GET** `/admin/ai/v1/config/router`

**响应**:
```json
{
  "code": 200,
  "data": {
    "force": "small",
    "enable-force": true,
    "keywords": {
      "enable": false,
      "rules": [
        { "pattern": "@大哥", "target": "big" },
        { "pattern": "@小弟", "target": "small" }
      ]
    },
    "skill": {
      "enabled": true,
      "version": "v1",
      "custom": {
        "enabled": true,
        "version": "v2"
      }
    }
  }
}
```

---

#### 2.2.6 保存路由配置

**POST** `/admin/ai/v1/config/router`

**请求体**:
```json
{
  "force": "small",
  "enable-force": true,
  "keywords": {
    "enable": true,
    "rules": [
      { "pattern": "@大哥", "target": "big" },
      { "pattern": "@小弟", "target": "small" }
    ]
  },
  "skill": {
    "enabled": true,
    "version": "v1",
    "custom": {
      "enabled": false,
      "version": "v2"
    }
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "路由配置保存成功",
  "data": null
}
```

---

#### 2.2.7 测试路由

**POST** `/admin/ai/v1/config/router/test`

**请求体**:
```json
{
  "input": "@大哥 你好",
  "virtual_model": "demo1"
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "model_type": "big",
    "matched_rule": "global_keyword:@大哥",
    "reason": "全局关键词匹配: @大哥",
    "confidence": 1.0
  }
}
```

---

### 2.3 虚拟模型管理

#### 2.3.1 列表

**GET** `/admin/ai/v1/virtual-models`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "name": "demo1",
      "proxy_key": "sk-demo1-a1b2c3d4e5f6g7h8",
      "base_url": "http://192.168.1.100:8000/proxy/v1",
      "current": "small",
      "force_current": false,
      "stream_support": true,
      "use": true,
      "small": {
        "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "api_key": "sk-xxx",
        "base_url": "https://api.siliconflow.cn/v1"
      },
      "big": {
        "model": "Pro/deepseek-ai/DeepSeek-V3.2",
        "api_key": "sk-xxx",
        "base_url": "https://api.siliconflow.cn/v1"
      },
      "routing": {
        "keywords": {
          "enable": false,
          "rules": [
            {"pattern": "@大哥", "target": "big"},
            {"pattern": "@小弟", "target": "small"}
          ]
        },
        "skill": {
          "enabled": true,
          "version": "v1",
          "custom": {
            "enabled": false,
            "version": "v2"
          }
        }
      },
      "knowledge": {
        "enabled": true,
        "shared": true,
        "system_default_skill": "v1",
        "custom_skill": "v1",
        "use_system_default": true,
        "use_custom": false
      },
      "web_search": {
        "enabled": true,
        "system_default_skill": "v1",
        "custom_skill": "v1",
        "use_system_default": true,
        "use_custom": false,
        "targets": ["searxng"]
      },
      "keyword_switching": {
        "enabled": false,
        "small_keywords": [],
        "big_keywords": []
      }
    }
  ]
}
```

**说明**:
- 实际API端点为 `/admin/ai/v1/virtual-models`（非 `/admin/ai/v1/models`）
- `routing` 字段为新增的路由配置（与 `keyword_switching` 并存）
- `routing.keywords` 使用 `enable` 字段（注意不是 `enabled`）
- `keyword_switching` 为传统的关键词切换配置（按 small/big 分类）
- `stream_support` 表示是否支持流式响应（SSE），默认为 true

#### 2.3.2 获取详情

**GET** `/admin/ai/v1/virtual-models/{name}`

**路径参数**:
- `name`: 虚拟模型名称

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "name": "demo1",
    "proxy_key": "sk-demo1-a1b2c3d4e5f6g7h8",
    "base_url": "http://192.168.1.100:8000/proxy/v1",
    "use": true,
    "routing": {
      "current": "small",
      "force_current": false,
      "models": {
        "small": {
          "name": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
          "api_key": "sk-xxx",
          "base_url": "https://api.siliconflow.cn/v1",
          "provider": "siliconflow",
          "priority": 1
        },
        "big": {
          "name": "Pro/deepseek-ai/DeepSeek-V3.2",
          "api_key": "sk-xxx",
          "base_url": "https://api.siliconflow.cn/v1",
          "provider": "siliconflow",
          "priority": 2
        }
      },
      "keyword_switching": {
        "enabled": true,
        "rules": [
          { "pattern": "@大哥", "target": "big" },
          { "pattern": "@小弟", "target": "small" }
        ]
      }
    },
    "knowledge": {
      "enabled": true,
      "shared": true
    },
    "web_search": {
      "enabled": true
    }
  }
}
```

**说明**:
- 返回完整的虚拟模型配置，包含新的可扩展路由结构
- `routing.models` 包含所有模型配置（当前支持 small/big，未来可扩展）
- `routing.keyword_switching.rules` 中的 `target` 可以是任意模型ID

---

#### 2.3.3 创建

**POST** `/admin/ai/v1/virtual-models`

**请求体**:
```json
{
  "name": "demo3",
  "proxy_key": "sk-yyyyyyyyyyyyyyyy",
  "base_url": "http://192.168.1.100:8000/proxy/v1",
  "current": "small",
  "force_current": false,
  "stream_support": true,
  "use": true,
  "small": {
    "model": "ollama/qwen2.5:7b",
    "api_key": "",
    "base_url": "http://localhost:11434/v1"
  },
  "big": {
    "model": "openai/gpt-4o",
    "api_key": "sk-xxxxxxxxxxxxxxxx",
    "base_url": "https://api.openai.com/v1"
  },
  "routing": {
    "keywords": {
      "enable": false,
      "rules": []
    },
    "skill": {
      "enabled": true,
      "version": "v1",
      "custom": {
        "enabled": false,
        "version": "v2"
      }
    }
  },
  "knowledge": {
    "enabled": true,
    "shared": true,
    "system_default_skill": "v1",
    "custom_skill": "v1",
    "use_system_default": true,
    "use_custom": false
  },
  "web_search": {
    "enabled": true,
    "system_default_skill": "v1",
    "custom_skill": "v1",
    "use_system_default": true,
    "use_custom": false,
    "targets": ["searxng"]
  },
  "keyword_switching": {
    "enabled": false,
    "small_keywords": [],
    "big_keywords": []
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "模型创建成功",
  "data": {...}
}
```

#### 2.3.4 更新

**PUT** `/admin/ai/v1/virtual-models/{name}`

**请求体**: 同创建（部分字段可更新）

**响应**:
```json
{
  "code": 200,
  "message": "模型更新成功",
  "data": {...}
}
```

---

#### 2.3.5 删除

**DELETE** `/admin/ai/v1/virtual-models/{name}`

**响应**:
```json
{
  "code": 200,
  "message": "模型删除成功",
  "data": null
}
```

---

#### 2.3.6 切换当前模型

**POST** `/admin/ai/v1/virtual-models/{name}/switch`

**请求体**:
```json
{
  "target": "small"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "已切换到小模型",
  "data": {
    "current": "small"
  }
}
```

---

#### 2.3.7 测试模型连接

**POST** `/admin/ai/v1/models/test-connection`

**请求体**:
```json
{
  "model": "deepseek-ai/DeepSeek-R1",
  "api_key": "sk-xxx",
  "base_url": "https://api.siliconflow.cn/v1"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "连接成功",
  "data": {
    "latency_ms": 150
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "模型名称和Base URL不能为空",
  "data": null
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

#### 2.3.8 添加新模型（可扩展架构）

**POST** `/admin/ai/v1/virtual-models/{name}/models`

**说明**: 为虚拟模型添加新的模型配置（支持扩展到N个模型）

**路径参数**:
- `name`: 虚拟模型名称

**请求体**:
```json
{
  "model_id": "coding",
  "config": {
    "name": "codellama/CodeLlama-70b-Instruct-hf",
    "api_key": "sk-xxx",
    "base_url": "https://api.siliconflow.cn/v1",
    "provider": "siliconflow",
    "priority": 3
  }
}
```

**请求字段说明**:
- `model_id`: 模型ID（如 coding, vision, analysis 等）
- `config.name`: 实际模型名称
- `config.api_key`: API密钥
- `config.base_url`: API基础URL
- `config.provider`: 提供商（siliconflow/openai/ollama）
- `config.priority`: 优先级（用于排序显示）

**响应**:
```json
{
  "code": 200,
  "message": "模型添加成功",
  "data": {
    "model_id": "coding",
    "config": {
      "name": "codellama/CodeLlama-70b-Instruct-hf",
      "api_key": "sk-xxx",
      "base_url": "https://api.siliconflow.cn/v1",
      "provider": "siliconflow",
      "priority": 3
    }
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "模型ID已存在",
  "data": null
}
```

---

### 2.4 Skill管理

#### 2.4.1 获取Skill列表

**GET** `/admin/ai/v1/skills`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "categories": [
      {
        "name": "router",
        "display_name": "模型路由",
        "skills": [
          {
            "name": "关键词路由",
            "is_system": true,
            "current_version": "v1",
            "type": "rule-based"
          },
          {
            "name": "意图识别",
            "is_system": true,
            "current_version": "v1",
            "type": "llm-based"
          },
          {
            "name": "X_skill",
            "is_system": false,
            "current_version": "v2",
            "all_versions": ["v1", "v2", "v3"],
            "type": "hybrid"
          }
        ]
      },
      {
        "name": "virtual_models",
        "display_name": "虚拟模型",
        "skills": [
          {
            "name": "knowledge",
            "is_system": true,
            "current_version": "v1",
            "type": "llm-based"
          },
          {
            "name": "web_search",
            "is_system": true,
            "current_version": "v1",
            "type": "llm-based"
          }
        ]
      }
    ]
  }
}
```

**说明**: 
- `is_system`: true 表示系统默认Skill（只读），false 表示自定义Skill（可编辑）
- `all_versions`: 仅自定义Skill有此字段，列出所有可用版本
- **架构说明**: 虽然每个虚拟模型在 `config.yml` 中都有独立的 `routing` 配置，但为了 Skill 管理的统一性，前端将 `router` 作为 `virtual_models` 的子节点展示

#### 2.4.2 获取Skill详情（支持多版本）

**GET** `/admin/ai/v1/skills/{category}/{name}`

**查询参数**:
- `is_custom`: true/false，是否为自定义Skill
- `version`: 可选，指定获取特定版本的内容

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "name": "X_skill",
    "category": "router",
    "is_custom": true,
    "current_version": "v2",
    "all_versions": ["v1", "v2", "v3"],
    "description": "我的自定义路由逻辑",
    "type": "hybrid",
    "enabled": true,
    "current_content": "当前版本(v2)的SKILL.md完整内容",
    "input_schema": {...},
    "output_schema": {...}
  }
}
```

**说明**:
- 如果指定 `version` 参数，返回该版本的 `current_content`
- 如果不指定，返回 `current_version` 的内容
- `all_versions` 列出该Skill的所有可用版本

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

#### 2.4.4 编辑自定义Skill（指定版本）

**PUT** `/admin/ai/v1/skills/{category}/{name}`

**查询参数**:
- `version`: 要编辑的版本（如 v1, v2, v3）

**请求体**:
```json
{
  "content": "新的SKILL.md内容",
  "save_mode": "update_current"
}
```

**说明**:
- `save_mode`: 保存模式
  - `update_current`: 更新当前版本（默认）
  - `create_new`: 保存为新版本
- 如果 `save_mode` 为 `create_new`，需要同时提供 `new_version` 字段

**响应**:
```json
{
  "code": 200,
  "message": "Skill已更新",
  "data": {
    "category": "router",
    "name": "X_skill",
    "version": "v2",
    "updated_at": "2026-02-14T21:30:00Z",
    "validation": {
      "valid": true,
      "errors": [],
      "warnings": []
    }
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

#### 2.4.6 获取某分类下所有Skills（支持多Skill）

**GET** `/admin/ai/v1/skills/{category}`

**说明**: 获取指定分类下的所有Skills（系统默认和自定义）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "category": "router",
    "system_skills": [
      {
        "name": "关键词路由",
        "current_version": "v1",
        "all_versions": ["v1"],
        "description": "基于关键词的模型路由",
        "type": "rule-based",
        "enabled": true
      },
      {
        "name": "意图识别",
        "current_version": "v1",
        "all_versions": ["v1"],
        "description": "基于LLM的意图识别路由",
        "type": "llm-based",
        "enabled": true
      }
    ],
    "custom_skills": [
      {
        "name": "X_skill",
        "current_version": "v2",
        "all_versions": ["v1", "v2", "v3"],
        "description": "我的自定义路由逻辑",
        "type": "hybrid",
        "enabled": true
      },
      {
        "name": "Y_skill",
        "current_version": "v1",
        "all_versions": ["v1"],
        "description": "另一个自定义路由",
        "type": "llm-based",
        "enabled": false
      }
    ]
  }
}
```

#### 2.4.7 获取Skill版本列表

**GET** `/admin/ai/v1/skills/{category}/{name}/versions`

**查询参数**:
- `is_custom`: 是否自定义 (true/false)

**说明**: 
- 获取指定Skill的所有可用版本
- 支持系统默认和自定义Skill

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "category": "router",
    "name": "X_skill",
    "is_custom": true,
    "current_version": "v2",
    "versions": [
      {
        "version": "v1",
        "created_at": "2026-01-15T10:30:00Z",
        "is_active": false
      },
      {
        "version": "v2",
        "created_at": "2026-02-01T14:20:00Z",
        "is_active": true
      },
      {
        "version": "v3",
        "created_at": "2026-02-10T09:15:00Z",
        "is_active": false
      }
    ]
  }
}
```

#### 2.4.8 创建自定义Skill

**POST** `/admin/ai/v1/skills/{category}`

**请求体**:
```json
{
  "name": "X_skill",
  "version": "v1",
  "copy_from": {
    "type": "system",
    "skill_name": "关键词路由",
    "version": "v1"
  }
}
```

**说明**:
- `copy_from`: 可选，指定复制来源
  - `type`: "system" 或 "custom"
  - `skill_name`: 来源Skill名称
  - `version`: 来源版本
- 如果不指定 `copy_from`，则创建空白Skill模板

**响应**:
```json
{
  "code": 200,
  "message": "Skill创建成功",
  "data": {
    "category": "router",
    "name": "X_skill",
    "version": "v1",
    "path": "./skill/custom/router/v1/X_skill"
  }
}
```

#### 2.4.9 创建新版本

**POST** `/admin/ai/v1/skills/{category}/{name}/versions`

**请求体**:
```json
{
  "new_version": "v3",
  "copy_from_version": "v2"
}
```

**说明**:
- 为现有自定义Skill创建新版本
- `copy_from_version`: 可选，指定复制来源版本，默认为当前版本

**响应**:
```json
{
  "code": 200,
  "message": "版本创建成功",
  "data": {
    "category": "router",
    "name": "X_skill",
    "version": "v3",
    "path": "./skill/custom/router/v3/X_skill"
  }
}
```

#### 2.4.10 删除自定义Skill

**DELETE** `/admin/ai/v1/skills/{category}/{name}`

**查询参数**:
- `is_custom`: 必须指定为 true（只能删除自定义Skill）

**说明**: 删除整个Skill及其所有版本

**响应**:
```json
{
  "code": 200,
  "message": "Skill已删除",
  "data": {
    "category": "router",
    "name": "X_skill",
    "deleted_versions": ["v1", "v2", "v3"]
  }
}
```

#### 2.4.11 删除版本

**DELETE** `/admin/ai/v1/skills/{category}/{name}/versions/{version}`

**说明**: 
- 删除指定版本
- 不能删除当前激活版本

**响应**:
```json
{
  "code": 200,
  "message": "版本已删除",
  "data": {
    "category": "router",
    "name": "X_skill",
    "version": "v1"
  }
}
```

#### 2.4.12 校验Skill内容

**POST** `/admin/ai/v1/skills/validate`

**请求体**:
```json
{
  "content": "SKILL.md完整内容"
}
```

**说明**: 
- 校验SKILL.md内容格式
- 不保存，仅返回校验结果
- 用于编辑时的实时校验

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": false,
    "errors": [
      {
        "line": 15,
        "column": 8,
        "field": "output_schema.properties.result.type",
        "message": "type值无效，应为 'integer' 而非 'int'"
      }
    ],
    "warnings": [
      {
        "line": 10,
        "message": "input_schema 缺少 description 字段",
        "suggestion": "建议添加description以提高可读性"
      }
    ]
  }
}
```

#### 2.4.14 重载单个Skill

**POST** `/admin/ai/v1/skills/{category}/{name}/reload`

**查询参数**:
- `version`: 可选，指定重载特定版本

**响应**:
```json
{
  "code": 200,
  "message": "Skill已重载",
  "data": {
    "category": "router",
    "name": "X_skill",
    "version": "v2"
  }
}
```

#### 2.4.15 获取Skill执行日志

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
      "timestamp": "2026-02-24T14:30:00Z",
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

#### 2.4.16 获取Skill文件树

**GET** `/admin/ai/v1/skills/{category}/{name}/tree`

**查询参数**:
- `is_custom`: 是否自定义 Skill (true/false)
- `version`: Skill 版本 (如 v1, v2)

**说明**: 获取 Skill 目录下的完整文件树结构，支持任意层级的子文件夹

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "name": "pdf-processing",
    "type": "directory",
    "path": "",
    "children": [
      {
        "name": "SKILL.md",
        "type": "file",
        "path": "SKILL.md",
        "extension": "md",
        "size": 2456,
        "isEditable": true
      },
      {
        "name": "references",
        "type": "directory",
        "path": "references/",
        "children": [
          {
            "name": "api.md",
            "type": "file",
            "path": "references/api.md",
            "extension": "md",
            "size": 1024,
            "isEditable": true
          },
          {
            "name": "examples.md",
            "type": "file",
            "path": "references/examples.md",
            "extension": "md",
            "size": 2048,
            "isEditable": true
          }
        ]
      },
      {
        "name": "scripts",
        "type": "directory",
        "path": "scripts/",
        "children": [
          {
            "name": "analyze.py",
            "type": "file",
            "path": "scripts/analyze.py",
            "extension": "py",
            "size": 3072,
            "isEditable": true
          },
          {
            "name": "image.png",
            "type": "file",
            "path": "scripts/image.png",
            "extension": "png",
            "size": 10240,
            "isEditable": false
          }
        ]
      }
    ]
  }
}
```

**文件类型说明**:
- `isEditable: true`: 可编辑文件（.md, .py）
- `isEditable: false`: 不可编辑文件（图片、二进制等）

---

#### 2.4.17 读取文件内容

**GET** `/admin/ai/v1/skills/{category}/{name}/content`

**查询参数**:
- `is_custom`: 是否自定义 Skill (true/false)
- `version`: Skill 版本
- `path`: 文件相对路径（如 `references/api.md`、`scripts/analyze.py`）

**说明**: 读取 Skill 目录下的任意文件内容

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "path": "references/api.md",
    "content": "# API Reference\\n\\n## Overview\\n...",
    "size": 1024,
    "extension": "md",
    "isEditable": true,
    "lastModified": "2026-02-23T10:30:00Z"
  }
}
```

**错误响应** (文件不可编辑):
```json
{
  "code": 400,
  "message": "该文件类型不支持在线编辑",
  "data": {
    "path": "scripts/image.png",
    "extension": "png"
  }
}
```

---

#### 2.4.18 保存文件内容

**PUT** `/admin/ai/v1/skills/{category}/{name}/content`

**查询参数**:
- `is_custom`: 是否自定义 Skill (true/false)
- `version`: Skill 版本
- `path`: 文件相对路径

**请求体**:
```json
{
  "content": "# Updated API Reference\\n\\n## Overview\\n..."
}
```

**说明**: 
- 保存文件内容到指定路径
- 如果文件不存在，自动创建
- 如果目录不存在，自动创建父目录
- 仅支持 `.md` 和 `.py` 文件

**响应**:
```json
{
  "code": 200,
  "message": "文件保存成功",
  "data": {
    "path": "references/api.md",
    "size": 1536,
    "lastModified": "2026-02-23T14:30:00Z"
  }
}
```

**错误响应** (文件类型不支持):
```json
{
  "code": 400,
  "message": "仅支持保存 .md 和 .py 文件",
  "data": null
}
```

---

#### 2.4.19 文件管理操作

**POST** `/admin/ai/v1/skills/{category}/{name}/files`

**查询参数**:
- `is_custom`: 是否自定义 Skill (true/false)
- `version`: Skill 版本

**请求体** (创建文件):
```json
{
  "operation": "create",
  "type": "file",
  "path": "references/new-doc.md",
  "content": "# New Document\\n\\nContent here..."
}
```

**请求体** (创建文件夹):
```json
{
  "operation": "create",
  "type": "directory",
  "path": "prompts"
}
```

**请求体** (重命名):
```json
{
  "operation": "rename",
  "oldPath": "references/old-name.md",
  "newPath": "references/new-name.md"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "operation": "create",
    "path": "references/new-doc.md",
    "type": "file"
  }
}
```

**错误响应** (文件已存在):
```json
{
  "code": 409,
  "message": "文件已存在",
  "data": {
    "path": "references/new-doc.md"
  }
}
```

**错误响应** (非法路径):
```json
{
  "code": 400,
  "message": "非法路径：不允许使用 .. 或绝对路径",
  "data": {
    "path": "../outside/file.md"
  }
}
```

---

#### 2.4.20 删除文件/文件夹

**DELETE** `/admin/ai/v1/skills/{category}/{name}/files`

**查询参数**:
- `is_custom`: 是否自定义 Skill (true/false)
- `version`: Skill 版本
- `path`: 要删除的文件或文件夹路径

**说明**: 
- 删除文件或文件夹
- 删除文件夹时会递归删除所有内容
- **禁止删除 SKILL.md 文件**（返回 400 错误）

**响应**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "path": "references/old-doc.md",
    "type": "file"
  }
}
```

**错误响应** (禁止删除 SKILL.md):
```json
{
  "code": 400,
  "message": "不能删除 SKILL.md 主文件",
  "data": {
    "path": "SKILL.md"
  }
}
```

---

#### 2.4.21 增强校验

**POST** `/admin/ai/v1/skills/validate-enhanced`

**请求体**:
```json
{
  "content": "---\\nname: pdf-processing\\ndescription: I can help you...\\ntype: rule-based\\n---\\n\\n# Instructions\\n...",
  "path": "SKILL.md"
}
```

**说明**: 
- 增强版校验，支持描述字段格式检查
- 检测描述是否使用第三人称（警告但不阻止）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [
      {
        "line": 2,
        "field": "description",
        "type": "third_person",
        "message": "描述建议使用第三人称",
        "suggestion": "将 'I can help you' 改为 'Extracts and processes PDF files'"
      }
    ],
    "metadata": {
      "name": "pdf-processing",
      "description": "I can help you...",
      "type": "rule-based"
    }
  }
}
```

---

### 2.5 对话历史

#### 2.5.1 创建对话

**POST** `/admin/ai/v1/conversations`

**请求体**:
```json
{
  "model": "demo1",                    // 必需: 虚拟模型名称
  "metadata": {                        // 可选: 对话元数据
    "source": "webchat" | "rss",       // 来源类型
    "title": "对话标题",                // 可选: 自定义标题
    "article_id": "article_uuid",      // RSS场景: 文章ID
    "article_title": "文章标题",        // RSS场景: 文章标题
    "feed_id": "feed_uuid"             // RSS场景: 订阅源ID
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "conv_xxx",
    "model": "demo1",
    "metadata": {                      // 返回metadata
      "source": "rss",
      "article_title": "文章标题..."
    },
    "created_at": "2026-02-24T14:00:00Z",
    "updated_at": "2026-02-24T14:00:00Z"
  }
}
```

---

#### 2.5.1.1 RSS文章对话场景

**说明**: RSS页面创建对话时，自动附加文章上下文

**创建流程**:
1. 用户选中RSS文章
2. 前端调用`POST /conversations`携带metadata
3. 后端创建对话，metadata原样存储
4. 前端自动发送第一条system message加载文章内容

**System Message格式**:
```json
{
  "role": "system",
  "content": "你正在阅读一篇RSS文章。请基于以下内容回答用户问题。\n\n文章标题: {title}\n文章来源: {feed_name}\n发布时间: {published_at}\n\n文章内容:\n{content}"
}
```

---

#### 2.5.1.2 快捷操作Prompt设计

**说明**: 快捷按钮（总结/翻译/关键点）通过标准对话接口实现

| 快捷按钮 | Prompt模板 |
|----------|-------------|
| **总结** | `请用中文总结这篇文章的主要内容，不超过200字。` |
| **翻译** | `请将这篇文章翻译成英文，保留原文格式和段落结构。` |
| **关键点** | `请提取这篇文章的3-5个关键要点，用bullet points形式列出。` |

**调用方式** (POST /proxy/ai/v1/chat/completions):
```json
{
  "model": "demo1",
  "conversation_id": "conv_xxx",
  "messages": [
    {"role": "system", "content": "文章内容..."},
    {"role": "user", "content": "请帮我总结这篇文章"}
  ],
  "temperature": 0.7
}
```

---

#### 2.5.2 列表

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
      "last_message_time": "2026-02-24T14:30:00Z",
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
  "created_at": "2026-02-24T14:00:00Z",
  "updated_at": "2026-02-24T14:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2026-02-24T14:00:05Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "你好！我是AI助手。",
      "timestamp": "2026-02-24T14:00:08Z",
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

#### 2.5.5 添加消息到对话

**POST** `/admin/ai/v1/conversations/{conversation_id}/messages`

**说明**: 向指定对话添加一条消息（通常由职责链内部调用）

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "role": "user",           // 必需: user/assistant/system
  "content": "你好",        // 必需: 消息内容
  "metadata": {             // 可选: 附加元数据
    "model_used": "big",
    "timestamp": "2026-01-01T12:00:00Z"
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "消息添加成功",
  "data": null
}
```

**错误响应**:
```json
{
  "code": 404,
  "message": "对话不存在",
  "data": null
}
```

#### 2.5.6 批量删除对话

**DELETE** `/admin/ai/v1/conversations/batch`

**请求体**:
```json
{
  "ids": ["conv_001", "conv_002", "conv_003"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "已删除 3 个对话",
  "data": {
    "success_count": 3,
    "failed_count": 0,
    "failed_ids": []
  }
}
```

**说明**:
- 批量删除多个对话
- 返回成功删除的数量和失败的ID列表
- 即使部分删除失败，也会继续处理其他ID

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
      "upload_time": "2026-02-24T10:00:00Z",
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
        "completed_at": "2026-02-24T14:30:00Z"
      },
      "progress": 100,
      "upload_time": "2026-02-24T14:00:00Z"
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

#### 2.8.1 获取订阅源列表

**GET** `/admin/ai/v1/rss/feeds?enabled=true&page=1&page_size=20`

**查询参数**:
- `enabled`: true/false/all - 按启用状态筛选（可选，默认all）
- `page`: 页码（可选，默认1）
- `page_size`: 每页数量（可选，默认20）

**响应**:
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "少数派",
      "url": "https://sspai.com/feed",
      "enabled": true,
      "fetch_interval": 30,
      "retention_days": 30,
      "default_permanent": false,
      "last_fetch_time": "2026-02-24T14:00:00Z",
      "article_count": 150,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-02-24T12:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

#### 2.8.2 创建订阅源

**POST** `/admin/ai/v1/rss/feeds`

**请求体**:
```json
{
  "name": "技术博客",
  "url": "https://blog.example.com/feed.xml",
  "enabled": true,
  "fetch_interval": 60,
  "retention_days": 30,
  "default_permanent": false
}
```

**响应**:
```json
{
  "id": "507f1f77bcf86cd799439012",
  "name": "技术博客",
  "url": "https://blog.example.com/feed.xml",
  "enabled": true,
  "fetch_interval": 60,
  "retention_days": 30,
  "default_permanent": false,
  "last_fetch_time": null,
  "article_count": 0,
  "created_at": "2026-02-24T14:00:00Z",
  "updated_at": "2026-02-24T14:00:00Z"
}
```

#### 2.8.3 更新订阅源

**PUT** `/admin/ai/v1/rss/feeds/{id}`

**请求体**（字段可选）:
```json
{
  "name": "更新后的名称",
  "enabled": false,
  "fetch_interval": 120,
  "retention_days": 7,
  "default_permanent": true
}
```

**响应**: 更新后的完整订阅源对象

#### 2.8.4 删除订阅源

**DELETE** `/admin/ai/v1/rss/feeds/{id}`

**响应**:
```json
{
  "success": true,
  "message": "订阅源已删除"
}
```

#### 2.8.5 立即抓取订阅源

**POST** `/admin/ai/v1/rss/feeds/{id}/fetch`

**响应**:
```json
{
  "success": true,
  "message": "抓取任务已提交",
  "fetch_id": "fetch_001",
  "feed_id": "507f1f77bcf86cd799439011"
}
```

#### 2.8.6 获取文章列表

**GET** `/admin/ai/v1/rss/articles?feed_id={id}&is_read=false&page=1&page_size=20`

**查询参数**:
- `feed_id`: 订阅源ID（可选）
- `is_read`: true/false - 按已读状态筛选（可选）
- `page`: 页码（可选，默认1）
- `page_size`: 每页数量（可选，默认20）

**响应**:
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439021",
      "feed_id": "507f1f77bcf86cd799439011",
      "feed_name": "少数派",
      "title": "AI最新进展",
      "url": "https://news.ai.com/article/1",
      "content": "完整的文章内容...",
      "content_length": 3500,
      "published_at": "2026-02-24T10:00:00Z",
      "fetched_at": "2026-02-24T14:00:00Z",
      "is_read": false
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

#### 2.8.7 获取文章详情

**GET** `/admin/ai/v1/rss/articles/{id}`

**响应**:
```json
{
  "id": "507f1f77bcf86cd799439021",
  "feed_id": "507f1f77bcf86cd799439011",
  "feed_name": "少数派",
  "title": "AI最新进展",
  "url": "https://news.ai.com/article/1",
  "content": "完整的HTML/Markdown内容...",
  "content_length": 3500,
  "published_at": "2026-02-24T10:00:00Z",
  "fetched_at": "2026-02-24T14:00:00Z",
  "is_read": true
}
```

#### 2.8.8 标记文章已读/未读

**POST** `/admin/ai/v1/rss/articles/{id}/read`

**请求体**:
```json
{
  "is_read": true
}
```

**响应**:
```json
{
  "success": true,
  "message": "已标记为已读",
  "article_id": "507f1f77bcf86cd799439021",
  "is_read": true
}
```
KV|```
SP|
MW|#### 2.8.9 删除文章
TZ|
RB|**DELETE** `/admin/ai/v1/rss/articles/{id}`
JR|
BR|**响应**:
YP|```json
YS|{
ZS|  "success": true,
JW|  "message": "文章已删除",
QM|  "article_id": "507f1f77bcf86cd799439021"
KV|}
SP|
MW|#### 2.8.10 批量删除文章
TZ|
RB|**DELETE** `/admin/ai/v1/rss/articles/batch`
JR|
PH|**查询参数**:
ZP|- `ids`: 文章ID列表，逗号分隔 (如 `id1,id2,id3`)
VJ|
QJ|**请求体** (可选，优先使用查询参数):
YP|```json
VW|{
KB|  "article_ids": ["id1", "id2", "id3"]
MZ|}
WH|```
TX|
BR|**响应**:
YP|```json
WV|{
YK|  "code": 200,
VS|  "message": "已删除 3 篇文章",
HY|  "data": {
NY|    "success_count": 3,
SK|    "failed_count": 0,
YS|    "failed_ids": []
YT|  }
MS|}
WY|```
JK|
VJ|**说明**:
HQ|- 批量删除多篇文章
YN|- 返回成功删除的数量和失败的ID列表
PZ|- 即使部分删除失败，也会继续处理其他ID
ZP|
WR|#### 2.8.11 获取热门订阅源推荐
#### 2.8.9 获取热门订阅源推荐

**GET** `/admin/ai/v1/rss/discover`

**响应**:
```json
{
  "sources": [
    {
      "name": "少数派",
      "url": "https://sspai.com/feed",
      "description": "高品质数字消费指南",
      "subscriber_count": "31.5K"
    },
    {
      "name": "36氪",
      "url": "https://36kr.com/feed",
      "description": "科技创投商业资讯",
      "subscriber_count": "12.5K"
    },
    {
      "name": "阮一峰的网络日志",
      "url": "http://www.ruanyifeng.com/blog/atom.xml",
      "description": "科技爱好者周刊",
      "subscriber_count": "8.9K"
    },
    {
      "name": "知乎日报",
      "url": "https://www.zhihu.com/rss",
      "description": "知乎精选内容",
      "subscriber_count": "6.2K"
    },
    {
      "name": "GitHub Trending",
      "url": "https://github.com/trending",
      "description": "GitHub热门项目",
      "subscriber_count": "5.8K"
    },
    {
      "name": "InfoQ",
      "url": "https://www.infoq.cn/feed",
      "description": "企业级技术社区",
      "subscriber_count": "4.5K"
    },
    {
      "name": "稀土掘金",
      "url": "https://juejin.cn/rss",
      "description": "开发者技术社区",
      "subscriber_count": "3.2K"
    },
    {
      "name": "V2EX",
      "url": "https://www.v2ex.com/index.xml",
      "description": "创意工作者社区",
      "subscriber_count": "2.1K"
    },
    {
      "name": "机器之心",
      "url": "https://www.jiqizhixin.com/rss",
      "description": "人工智能媒体",
      "subscriber_count": "1.8K"
    },
    {
      "name": "爱范儿",
      "url": "https://www.ifanr.com/feed",
      "description": "数字公民媒体",
      "subscriber_count": "1.5K"
    }
  ]
}
```

#### 2.8.10 获取RSS配置

**GET** `/admin/ai/v1/config` （返回config.yml中的rss部分）

**Config.yml RSS配置结构**:
```yaml
rss:
  max_concurrent: 5          # 最大并发抓取
  auto_fetch: true           # 自动抓取
  fetch_interval: 30         # 抓取间隔（分钟）
  retention_days: 30         # 保留天数
  default_permanent: false   # 默认永久保存
  skill:                     # Skill配置
    enabled: true
    version: "v1"
    custom:
      enabled: true
      version: "v1"
```

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
      "timestamp": "2026-02-24T14:30:00Z",
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
      "timestamp": "2026-02-24T14:30:00Z",
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
- `category`: Skill分类 (router, virtual_models, knowledge, web_search, rss, audio, video, text)
- `name`: Skill名称
- `status`: success/failed/validation_error
- `start_time`: 开始时间
- `end_time`: 结束时间
- `limit`: 数量

**说明**: 
- `router`（模型路由）在 API 中是独立的 Skill 分类
- **架构说明**: 虽然每个虚拟模型在 `config.yml` 中都有独立的 `routing` 配置，但为了 Skill 管理的统一性，前端将 `router` 作为 `virtual_models` 的子节点展示

**响应**:
```json
{
  "logs": [
    {
      "log_id": "skill_001",
      "timestamp": "2026-02-24T14:30:00Z",
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
      "timestamp": "2026-02-24T14:30:00Z",
      "type": "user_input",
      "conversation_id": "conv_001",
      "model": "demo1",
      "data": {"content": "你好", "metadata": {...}}
    },
    {
      "timestamp": "2026-02-24T14:30:05Z",
      "type": "ai_response",
      "conversation_id": "conv_001",
      "model": "demo1",
      "data": {"content": "你好！", "model_used": "small", "knowledge_refs": [...]}
    },
    {
      "timestamp": "2026-02-24T14:30:05Z",
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
      "created_at": "2026-02-24T14:00:00Z"
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
        "fetch_time": "2026-02-24T14:00:00Z",
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
- **时间格式**: ISO 8601 (如 `2026-02-24T14:30:00Z`)

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
**最后更新**: 2026-02-24  
**状态**: 已完成，待开发实现
