# AI Gateway 项目 - 头脑风暴会话记录

> **Session ID**: ses_3c504e596ffeNvQiVDfb9WS7uW  
> **日期**: 2026-02-08  
> **消息数**: 19

---

## 目录

1. [项目概述](#项目概述)
2. [设计决策汇总](#设计决策汇总)
3. [前端架构设计](#前端架构设计)
4. [后端架构设计](#后端架构设计)
5. [数据库Schema设计](#数据库schema设计)
6. [API详细规范](#api详细规范)
7. [Skill系统设计](#skill系统设计)
8. [配置约束](#配置约束)

---

## 项目概述

### 项目背景
AI Gateway（AI节流网关）是一个智能AI代理系统，支持：
- 虚拟模型代理（复刻SiliconFlow格式）
- 智能模型路由（Big/Small模型自动切换）
- 知识提取与RAG检索
- 媒体处理（Whisper转录）
- RSS订阅管理
- 可插拔Skill系统

### 技术栈确认
| 层级 | 技术选择 |
|------|---------|
| 前端 | Vue 3 + TypeScript + Element Plus |
| 后端 | FastAPI (Python) |
| 数据库 | MongoDB (对话/RSS/日志) + Redis (缓存/会话) + Qdrant (向量库) |
| 部署 | Docker Compose |
| Whisper | CPU开发模式 / GPU部署模式 |

---

## 设计决策汇总

### 核心决策
| # | 决策项 | 确认方案 |
|---|--------|---------|
| 1 | 前端响应式 | 仅WEB电脑端，无需移动端适配 |
| 2 | 登录认证 | **无认证**，本地部署直接访问 |
| 3 | API版本控制 | 代理API: `proxy/api/v1`，管理API: `proxy/admin/*` |
| 4 | 会话存储 | 分层存储 - Redis(TTL=24h) + MongoDB持久化 |
| 5 | 对话界面布局 | 左右分栏（左侧会话列表常驻） |
| 6 | proxy_key显示 | 部分隐藏（`sk-xxx...xxx`格式） |
| 7 | 配置管理 | **只存config.yml，数据库不存任何配置** |
| 8 | Skill执行方式 | Python函数动态加载 |
| 9 | Web搜索 | API调用方式（SearxNG/LibreX/4get） |
| 10 | 文件上传限制 | 100MB（不分片） |

### ⚠️ 配置管理铁律
> - 所有配置必须修改 `config.yml`
> - 数据库**绝对不保存任何配置**
> - 仅 `virtual_models` 下的虚拟模型可通过API添加
> - 其他配置增加**必须经过用户同意，永远**

---

## 前端架构设计

### 路由结构
```
/                     → 重定向到 /dashboard
/dashboard            → 仪表盘首页
/chat                 → 对话管理（左右分栏布局）
/models               → 虚拟模型管理
/models/:id/edit      → 模型编辑
/knowledge            → 知识库管理
/knowledge/query      → 知识检索测试
/rss                  → RSS订阅管理
/rss/:feedId          → 订阅详情+文章列表
/media                → 媒体管理（含子菜单）
│   ├── /media/video  → 视频文件管理
│   ├── /media/audio  → 音频文件管理
│   └── /media/text   → 文本&图片管理
/logs                 → 系统日志查看
/config               → 系统配置管理
```

### 侧边栏菜单结构
```
🤖 AI Gateway
├── 📊 仪表盘
├── 💬 对话管理
├── 🤖 模型管理
├── 📚 知识库
├── 📡 RSS订阅
├── 📁 媒体管理
│   ├── 🎥 视频
│   ├── 🎵 音频
│   └── 📝 文本&图片
├── 📝 系统日志
└── ⚙️ 系统配置
```

---

## 后端架构设计

### API分层架构
```
┌─────────────────────────────────────────────────────────────┐
│  代理层 - 复刻SiliconFlow OpenAI兼容格式                      │
│  Base: /proxy/api/v1                                        │
│  Auth: Bearer {proxy_key}                                   │
│  ─────────────────────────────────────────────────────────  │
│  POST   /chat/completions    → 聊天补全（流式/非流式）       │
│  GET    /models              → 获取可用模型列表              │
│  POST   /embeddings          → 文本向量化（可选）            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  管理层 - RESTful风格（无认证）                              │
│  Base: /proxy/admin                                         │
│  ─────────────────────────────────────────────────────────  │
│  /models                 GET|POST|DELETE|PUT                │
│  /chat/sessions          GET|POST|DELETE                    │
│  /chat/sessions/:id      GET|DELETE                         │
│  /knowledge/query        POST                               │
│  /knowledge/documents    GET|POST|DELETE                    │
│  /rss/feeds              GET|POST                           │
│  /rss/feeds/:id          GET|PUT|DELETE                     │
│  /media/files            GET|POST|DELETE                    │
│  /media/files/:id/transcribe POST                           │
│  /logs                   GET                                │
└─────────────────────────────────────────────────────────────┘
```

### 日志输出策略
```
日志双轨制
├── 1. MongoDB存储（所有日志）
│   ├── system_logs    → DEBUG/INFO/WARNING/ERROR
│   └── operation_logs → 用户操作记录
│
└── 2. 文件导出（/logs文件夹）⭐ERROR强制保存
    ├── system/system_2026-02-08.log
    ├── operation/operation_2026-02-08.log
    └── error/error_2026-02-08.log  ← ERROR强制保存（冗余备份）

日志轮转：按天分割，保留30天
```

---

## 数据库Schema设计

### MongoDB Collections

#### 1. conversations - 对话会话
```yaml
conversations:
  - _id: ObjectId
  - session_id: string (唯一)
  - title: string
  - virtual_model: string (仅引用，非配置)
  - current_model: enum ["small", "big"]
  - message_count: int
  - created_at: datetime
  - updated_at: datetime
```

#### 2. messages - 消息记录
```yaml
messages:
  - _id: ObjectId
  - session_id: string (索引)
  - role: enum ["user", "assistant", "system"]
  - content: string
  - model_used: string
  - tokens_used: int
  - routing_reason: string (keyword/skill/redis/force)
  - created_at: datetime
```

#### 3. knowledge_sources - 知识源（统一抽象层）⭐核心表
```yaml
knowledge_sources:
  - _id: ObjectId
  - source_id: string (唯一，如 "chat_001_msg_003")
  - source_type: enum ["chat", "video", "audio", "text", "rss", "image"]
  
  # 原始内容
  - raw_content: 
      title: string
      content: string (文本/转录/OCR结果)
      url: string (可选)
      file_path: string
      mime_type: string
  
  # 元数据
  - metadata:
      duration_seconds: int
      word_count: int
      language: string
      source_session: string
      source_feed: string
      source_file: string
      created_by: string
  
  # 处理状态
  - processing_status: enum ["pending", "extracting", "vectorized", "failed"]
  - extracted_at: datetime
  - vector_ids: array[string] (Qdrant向量ID)
  
  - created_at: datetime
  - updated_at: datetime
```

#### 4. rss_feeds_status - RSS运行时状态
```yaml
rss_feeds_status:
  - _id: ObjectId
  - feed_name: string (关联config.yml中的name)
  - last_fetch_at: datetime
  - article_count: int
  - last_error: string
  - updated_at: datetime
```

#### 5. rss_articles - RSS文章
```yaml
rss_articles:
  - _id: ObjectId
  - feed_name: string
  - title: string
  - link: string
  - content: string
  - published_at: datetime
  - knowledge_source_id: string
  - created_at: datetime
```

#### 6. media_files - 媒体文件
```yaml
media_files:
  - _id: ObjectId
  - file_id: string (唯一)
  - filename: string
  - original_name: string
  - file_type: enum ["video", "audio", "text", "image"]
  - mime_type: string
  - size_bytes: int
  - storage_path: string
  - metadata: object
  - process_status: enum ["uploaded", "transcribing", "extracting", "completed", "failed"]
  - process_result: string
  - knowledge_source_id: string
  - created_at: datetime
```

#### 7. system_logs - 系统日志
```yaml
system_logs:
  - _id: ObjectId
  - level: enum ["DEBUG", "INFO", "WARNING", "ERROR"]
  - module: string
  - message: string
  - details: object
  - created_at: datetime
```

#### 8. operation_logs - 操作日志
```yaml
operation_logs:
  - _id: ObjectId
  - action: string
  - resource_type: string
  - resource_id: string
  - user: string (admin或IP)
  - details: object
  - ip_address: string
  - user_agent: string
  - created_at: datetime
```

### 知识流转流程
```
原始输入 → 统一抽象层(knowledge_sources) → 向量知识库(Qdrant)
   │              │                              │
   │              ├── 状态: pending              │
   │              ├── 状态: extracting           │
   │              └── 状态: vectorized → 填充vector_ids
   │
   ├── 💬 对话消息
   ├── 🎥 视频文件
   ├── 🎵 音频文件
   ├── 📝 文本文件
   ├── 🖼️ 图片(OCR)
   └── 📡 RSS文章
```

---

## API详细规范

### 代理层 API

#### POST /proxy/api/v1/chat/completions
聊天补全（复刻OpenAI格式）

**Request:**
```json
{
  "model": "demo1",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "你好"}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response (非流式):**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "Pro/deepseek-ai/DeepSeek-V3.2",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "你好！很高兴为您服务。"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  }
}
```

**Response (流式 - SSE):**
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"你好"}}]}

data: [DONE]
```

### 管理层 API

#### GET /proxy/admin/models
获取虚拟模型列表（从config.yml读取+运行时状态）

**Response:**
```json
{
  "models": [
    {
      "name": "demo1",
      "proxy_key": "sk-xxx...xxx",
      "base_url": "http://192.168.1.100:8000/proxy/v1",
      "current": "small",
      "enabled": true,
      "small": {
        "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "status": "active"
      },
      "big": {
        "model": "Pro/deepseek-ai/DeepSeek-V3.2",
        "status": "standby"
      },
      "stats": {
        "today_requests": 125,
        "total_tokens": 45600
      }
    }
  ]
}
```

#### POST /proxy/admin/models
创建虚拟模型（唯一允许修改config.yml的API）

**Request:**
```json
{
  "name": "demo3",
  "small": {
    "model": "ollama/qwen2.5:7b",
    "base_url": "http://localhost:11434/v1"
  },
  "big": {
    "model": "openai/gpt-4o",
    "api_key": "sk-xxxxx",
    "base_url": "https://api.openai.com/v1"
  }
}
```

#### POST /proxy/admin/knowledge/query
知识检索

**Request:**
```json
{
  "query": "系统架构设计",
  "top_k": 5,
  "source_types": ["chat", "rss"],
  "threshold": 0.75
}
```

**Response:**
```json
{
  "results": [
    {
      "source_id": "chat_001_msg_005",
      "source_type": "chat",
      "title": "会话: 系统架构讨论",
      "content": "系统采用分层架构...",
      "similarity": 0.92,
      "created_at": "2026-02-08T10:00:00Z"
    }
  ]
}
```

---

## Skill系统设计

### Skill目录结构
```
./skill/
├── router/
│   └── v1/
│       ├── SKILL.md
│       └── skill.py
├── knowledge/
│   ├── v1/
│   └── topics/
│       └── v1/
├── web_search/
│   └── v1/
├── rss/
│   └── v1/
├── text/
│   └── v1/
└── custom/
    ├── router/v2/
    ├── knowledge/v2/
    └── web_search/v3/
```

### SKILL.md 规范示例
```markdown
# Skill: router/v1

## 描述
根据对话内容智能判断使用big模型还是small模型

## 输入
```json
{
  "query": "用户当前输入",
  "session_history": ["最近3轮对话"],
  "current_model": "small"
}
```

## 输出
```json
{
  "target_model": "big" | "small",
  "confidence": 0.85,
  "reason": "复杂编程问题，需要更强的推理能力"
}
```

## 触发条件
- 虚拟模型配置中 router.skill.enabled = true
- 关键词路由未匹配
```

---

## 配置约束

### config.yml 新增配置
```yaml
knowledge:
  threshold:
    extraction: 0.70    # 知识提取阈值
    retrieval: 0.76     # 知识检索阈值
  scheduler:
    cron: "*/30 * * * *"
    enabled: false
  embedding:
    model: BAAI/bge-m3
    base_url: https://api.siliconflow.cn/v1
    api_key: sk-xxxxxxxxxxxxxxxx
```

### 阈值优先级规则
```
if skill_has_custom_threshold:
    use skill_threshold        # Skill自定义阈值优先
else:
    use config.yml threshold   # 否则使用config.yml配置
```

### 阈值使用场景
| 场景 | 阈值来源 | 使用方式 |
|------|---------|---------|
| **知识提取** | `threshold.extraction` (0.70) | 内容向量化后，与已有知识相似度 < 0.70 才存储（去重） |
| **知识检索** | `threshold.retrieval` (0.76) | RAG查询时只返回相似度 >= 0.76 的结果 |
| **Skill路由** | Skill内部定义 | 如果 `./skill/router/v1/SKILL.md` 中定义了阈值，则优先使用Skill阈值 |
| **主题分类** | `threshold.extraction` (0.70) 或 Skill内部定义 | 根据Skill配置决定 |

---

## 下一步建议

已完成：
- ✅ Phase 2: 架构设计
- ✅ Phase 3: 数据库Schema设计
- ✅ Phase 4: API详细规范
- ✅ Phase 5: Skill系统接口设计

待进行：
- [ ] Phase 6: 项目初始化（目录结构、FastAPI、Vue3、Docker）
- [ ] Phase 7: 开发计划（里程碑、优先级、任务拆解）

---

*导出时间: 2026-02-08*  
*更新时间: 2026-02-08 (阈值配置更新)*  
*会话ID: ses_3c504e596ffeNvQiVDfb9WS7uW*
