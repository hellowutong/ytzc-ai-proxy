# AI网关系统 - 前后端架构设计

> **Session**: 头脑风暴 Phase 2  
> **目标**: 输出详细前后端架构图，核对需求完整性

---

## 一、系统整体架构图

```mermaid
flowchart TB
    subgraph Client["📱 客户端层"]
        C1[ChatBox AI]
        C2[第三方应用]
        C3[Web UI]
    end

    subgraph Gateway["🌐 AI 节流网关 (Port 8000)"]
        direction TB
        Auth[认证模块<br/>proxy_key验证]
        Router[路由决策引擎<br/>关键词/Redis/Skill]
        SessionMgr[会话管理器]
        Proxy[API代理转发]
        Config[热加载配置]
    end

    subgraph Backend["⚙️ 后端服务层 (./app)"]
        direction TB
        API[RESTful API]
        Core[核心业务逻辑]
        SkillSys[Skill系统]
        
        subgraph Modules["功能模块"]
            Knowledge[知识提取模块]
            Media[媒体处理模块<br/>Whisper转录]
            RSS[RSS订阅模块]
        end
    end

    subgraph Frontend["🎨 前端层 (./wei-ui)"]
        direction TB
        UI_Dash[管理仪表盘]
        UI_Chat[聊天界面]
        UI_Config[配置管理]
    end

    subgraph Storage["💾 数据存储层"]
        direction TB
        Mongo[(MongoDB<br/>对话/会话/RSS)]
        Redis[(Redis<br/>缓存/会话状态)]
        Qdrant[(Qdrant<br/>向量知识库)]
    end

    subgraph External["🌐 外部服务"]
        SF[SiliconFlow API]
        OpenAI[OpenAI兼容API]
        SearxNG[SearxNG搜索]
        LibreX[LibreX搜索]
    end

    Client -->|HTTP/SSE| Gateway
    Gateway -->|内部调用| Backend
    Gateway <-->|会话状态| Redis
    Backend -->|CRUD| Mongo
    Backend -->|向量检索| Qdrant
    Backend -->|代理请求| External
    Frontend -->|管理API| Backend
    Backend -->|Skill调用| SkillSys
```

---

## 二、后端架构详图 (./app)

```mermaid
flowchart TB
    subgraph App["Backend Application (./app)"]
        direction TB
        
        subgraph Entry["入口层"]
            Main[main.py<br/>FastAPI应用启动]
            Middleware[中间件层<br/>CORS/日志/异常处理]
        end

        subgraph RouterLayer["路由层 (routers/)"]
            R_Proxy[/proxy/v1/<br/>代理转发/]
            R_Chat[/chat/<br/>对话管理/]
            R_Knowledge[/knowledge/<br/>知识库/]
            R_Media[/media/<br/>媒体处理/]
            R_RSS[/rss/<br/>RSS订阅/]
            R_Config[/config/<br/>配置管理/]
            R_Skill[/skill/<br/>Skill执行/]
        end

        subgraph ServiceLayer["服务层 (services/)"]
            S_Router[RouterService<br/>模型路由决策]
            S_Chat[ChatService<br/>对话管理]
            S_Knowledge[KnowledgeService<br/>知识提取]
            S_Media[MediaService<br/>媒体转录]
            S_RSS[RSSService<br/>RSS抓取]
            S_Config[ConfigService<br/>配置热加载]
        end

        subgraph CoreLayer["核心层 (core/)"]
            ConfigMgr[ConfigManager<br/>YAML配置管理]
            ModelClient[ModelClient<br/>模型调用封装]
            AuthMgr[AuthManager<br/>proxy_key验证]
            SessionMgr[SessionManager<br/>会话管理]
        end

        subgraph ModelLayer["模型层 (models/)"]
            M_Chat[ChatModels<br/>对话/消息/会话]
            M_Knowledge[KnowledgeModels<br/>知识/向量]
            M_Media[MediaModels<br/>媒体/转录]
            M_RSS[RSSModels<br/>订阅/文章]
            M_Config[ConfigModels<br/>配置实体]
        end

        subgraph DBLayer["数据层 (db/)"]
            MongoConn[MongoDB连接<br/>Motor异步驱动]
            RedisConn[Redis连接<br/>Redis-py]
            QdrantConn[Qdrant连接<br/>Qdrant客户端]
        end

        subgraph Utils["工具层 (utils/)"]
            U_Embed[Embedding工具<br/>向量生成]
            U_Whisper[Whisper工具<br/>音视频转录]
            U_Logger[日志工具<br/>系统/操作日志]
            U_Validator[验证工具<br/>请求校验]
        end
    end

    Main --> Middleware
    Middleware --> RouterLayer
    RouterLayer --> ServiceLayer
    ServiceLayer --> CoreLayer
    ServiceLayer --> ModelLayer
    ServiceLayer --> DBLayer
    ServiceLayer --> Utils
    CoreLayer --> DBLayer
```

---

## 三、前端架构详图 (./wei-ui)

```mermaid
flowchart TB
    subgraph Frontend["Frontend Application (./wei-ui)"]
        direction TB
        
        subgraph TechStack["技术栈"]
            TS_Vue[Vue 3 + TypeScript]
            TS_Vite[Vite构建工具]
            TS_Pinia[Pinia状态管理]
            TS_Router[Vue Router]
            TS_UI[Element Plus / Ant Design Vue]
            TS_Axios[Axios HTTP客户端]
            TS_SSE[SSE客户端<br/>EventSource]
        end

        subgraph Views["页面层 (views/)"]
            V_Dash[Dashboard.vue<br/>系统概览仪表盘]
            V_Chat[Chat.vue<br/>对话界面]
            V_Models[Models.vue<br/>虚拟模型管理]
            V_Knowledge[Knowledge.vue<br/>知识库管理]
            V_RSS[RSSManager.vue<br/>RSS订阅管理]
            V_Media[Media.vue<br/>媒体文件管理]
            V_Config[Config.vue<br/>系统配置]
            V_Logs[Logs.vue<br/>日志查看]
        end

        subgraph Components["组件层 (components/)"]
            C_Layout[Layout.vue<br/>布局框架]
            C_Sidebar[Sidebar.vue<br/>侧边导航]
            C_ChatBox[ChatBox.vue<br/>聊天组件]
            C_Message[MessageItem.vue<br/>消息展示]
            C_ModelCard[ModelCard.vue<br/>模型卡片]
            C_FileUpload[FileUpload.vue<br/>文件上传]
        end

        subgraph Stores["状态层 (stores/)"]
            ST_App[app.ts<br/>应用全局状态]
            ST_Chat[chat.ts<br/>对话状态]
            ST_Config[config.ts<br/>配置状态]
            ST_User[user.ts<br/>用户信息]
        end

        subgraph API["API层 (api/)"]
            A_Proxy[proxy.ts<br/>代理接口]
            A_Chat[chat.ts<br/>对话接口]
            A_Knowledge[knowledge.ts<br/>知识库接口]
            A_Media[media.ts<br/>媒体接口]
            A_RSS[rss.ts<br/>RSS接口]
            A_Config[config.ts<br/>配置接口]
        end

        subgraph UtilsFE["工具层 (utils/)"]
            UF_Request[request.ts<br/>请求封装]
            UF_SSE[sse.ts<br/>流式响应处理]
            UF_Format[format.ts<br/>数据格式化]
            UF_Validation[validation.ts<br/>表单验证]
        end
    end

    TechStack --> Views
    TechStack --> Components
    Views --> Components
    Views --> Stores
    Views --> API
    API --> UtilsFE
```

---

## 四、数据流架构图

```mermaid
sequenceDiagram
    autonumber
    participant Client as 客户端
    participant Gateway as AI网关
    participant Router as 路由引擎
    participant Skill as Skill系统
    participant Service as 业务服务
    participant Redis as Redis
    participant Mongo as MongoDB
    participant Qdrant as Qdrant
    participant ModelAPI as 模型API

    %% 对话请求流程
    rect rgb(230, 245, 255)
        Note over Client,ModelAPI: 对话请求流程
        Client->>Gateway: POST /proxy/v1/chat/completions<br/>Authorization: Bearer {proxy_key}
        Gateway->>Gateway: 验证proxy_key → 匹配虚拟模型
        Gateway->>Redis: 获取会话状态
        Redis-->>Gateway: 返回会话上下文
        
        alt Skill路由启用
            Gateway->>Skill: 调用Router Skill判断
            Skill-->>Gateway: 返回目标模型(big/small)
        else 关键词路由
            Gateway->>Router: 关键词匹配
            Router-->>Gateway: 返回目标模型
        end
        
        Gateway->>Service: 转发到对应模型服务
        Service->>Mongo: 保存用户消息
        Service->>ModelAPI: 转发请求到实际模型API
        
        alt 流式响应
            ModelAPI-->>Service: SSE流式数据
            Service-->>Gateway: 流式转发
            Gateway-->>Client: SSE响应
        else 非流式响应
            ModelAPI-->>Service: 完整响应
            Service->>Mongo: 保存AI回复
            Service-->>Gateway: 返回响应
            Gateway-->>Client: JSON响应
        end
    end

    %% 知识提取流程
    rect rgb(255, 245, 230)
        Note over Client,Qdrant: 知识提取流程
        Service->>Service: 异步提取知识
        Service->>U_Embed: 生成embedding向量
        U_Embed-->>Service: 返回向量
        Service->>Qdrant: 存储到向量库
        Service->>Mongo: 记录知识元数据
    end

    %% RAG检索流程
    rect rgb(230, 255, 230)
        Note over Client,Qdrant: RAG检索增强流程
        Gateway->>Service: 需要知识增强
        Service->>U_Embed: 将查询文本向量化
        U_Embed-->>Service: 返回查询向量
        Service->>Qdrant: 相似度搜索(top_k)
        Qdrant-->>Service: 返回相关知识
        Service->>Service: 构建RAG提示词
    end
```

---

## 五、部署架构图 (Docker)

```mermaid
flowchart TB
    subgraph DockerEnv["Docker Compose 部署架构"]
        direction TB
        
        subgraph Network["ai-gateway-network"]
            direction TB
            
            subgraph AppContainer["app容器"]
                FastAPI[FastAPI应用<br/>Port 8000]
            end
            
            subgraph UIContainer["wei-ui容器"]
                NginxUI[Nginx<br/>Port 80/443]
            end
            
            subgraph SkillContainer["skill-volume"]
                SkillVol[技能目录挂载<br/>./skill:/app/skill]
            end
            
            subgraph UploadContainer["upload-volume"]
                UploadVol[上传目录挂载<br/>./upload:/app/upload]
            end
            
            subgraph LogContainer["log-volume"]
                LogVol[日志目录挂载<br/>./logs:/app/logs]
            end
            
            MongoDB[(MongoDB<br/>Port 27017)]
            RedisDB[(Redis<br/>Port 6379)]
            QdrantDB[(Qdrant<br/>Port 6333)]
        end
        
        subgraph ExternalAccess["外部访问"]
            User((用户))
        end
    end
    
    User -->|HTTP| NginxUI
    User -->|API| FastAPI
    NginxUI -->|反向代理| FastAPI
    FastAPI --> MongoDB
    FastAPI --> RedisDB
    FastAPI --> QdrantDB
    FastAPI -.->|读取| SkillVol
    FastAPI -.->|写入| UploadVol
    FastAPI -.->|写入| LogVol
```

---

## 六、Skill系统架构图

```mermaid
flowchart TB
    subgraph SkillSystem["Skill系统架构 (./skill)"]
        direction TB
        
        subgraph CoreSkill["核心Skill"]
            SK_Router[router/v1/<br/>路由决策Skill]
            SK_Knowledge[knowledge/v1/<br/>知识提取Skill]
            SK_WebSearch[web_search/v1/<br/>联网搜索Skill]
            SK_RSS[rss/v1/<br/>RSS处理Skill]
        end
        
        subgraph TopicSkill["主题分类Skill"]
            SK_Topic[knowledge/topics/v1/<br/>自动主题分类]
        end
        
        subgraph CustomSkill["自定义Skill"]
            CS_Router[custom/router/v2/<br/>自定义路由]
            CS_Knowledge[custom/knowledge/v2/<br/>自定义知识处理]
            CS_WebSearch[custom/web_search/v3/<br/>自定义搜索]
            CS_RSS[custom/rss/v2/<br/>自定义RSS处理]
        end
        
        subgraph SkillInterface["Skill接口规范"]
            SI_MD[SKILL.md<br/>技能描述文件]
            SI_Code[skill.py<br/>技能执行代码]
            SI_Config[config.yml<br/>技能配置]
        end
    end
    
    subgraph Execution["执行流程"]
        Trigger{触发条件} -->|匹配| Loader[SkillLoader<br/>技能加载器]
        Loader -->|执行| Executor[SkillExecutor<br/>技能执行器]
        Executor -->|返回结果| Gateway[网关路由决策]
    end
    
    CoreSkill --> SkillInterface
    TopicSkill --> SkillInterface
    CustomSkill --> SkillInterface
    SkillInterface --> Execution
```

---

## 七、需求核对清单

### ✅ 核心功能覆盖检查

| # | 功能模块 | 需求描述 | 架构支持 | 状态 |
|---|---------|---------|---------|------|
| 1 | **虚拟模型代理** | 复刻SiliconFlow格式，统一API接口 | ✅ Proxy路由层 + ModelClient | 🟢 |
| 2 | **模型路由** | 关键词/Redis会话/Skill智能切换 | ✅ RouterService + Skill系统 | 🟢 |
| 3 | **对话管理** | 会话CRUD，实时保存MongoDB | ✅ ChatService + MongoDB | 🟢 |
| 4 | **知识提取** | 对话/媒体/RSS提取，持久化Qdrant | ✅ KnowledgeService + Qdrant | 🟢 |
| 5 | **媒体处理** | 音视频转文字(Whisper) | ✅ MediaService + Whisper工具 | 🟢 |
| 6 | **RSS订阅** | 自动抓取，提取知识 | ✅ RSSService + 定时任务 | 🟢 |
| 7 | **Skill系统** | 可插拔技能模块 | ✅ SkillLoader + SkillExecutor | 🟢 |
| 8 | **日志系统** | 系统日志+操作日志 | ✅ Logger工具 + 日志目录 | 🟢 |

### ✅ 目录结构核对

| 目录 | 用途 | 状态 |
|-----|------|------|
| `./docker` | 部署文件 | 🟢 架构图已包含 |
| `./logs` | 日志导出 | 🟢 数据流已规划 |
| `./wei-ui` | 前端项目 | 🟢 前端架构详图 |
| `./app` | 后台代码 | 🟢 后端架构详图 |
| `./docs` | 文档目录 | 🟢 本文件存放位置 |
| `./test` | 测试目录 | 🟢 已规划 |
| `./skill` | 技能目录 | 🟢 Skill系统架构 |
| `./upload` | 上传目录 | 🟢 媒体处理支持 |

### ✅ 配置项核对 (config.yml)

| 配置节点 | 用途 | 架构支持 |
|---------|------|---------|
| `app.*` | 服务基础配置 | 🟢 FastAPI启动配置 |
| `storage.mongodb.*` | MongoDB连接 | 🟢 MongoConn模块 |
| `storage.qdrant.*` | Qdrant连接 | 🟢 QdrantConn模块 |
| `storage.redis.*` | Redis连接 | 🟢 RedisConn模块 |
| `ai-gateway.router.*` | 路由配置 | 🟢 RouterService |
| `ai-gateway.virtual_models.*` | 虚拟模型配置 | 🟢 ConfigManager |
| `ai-gateway.knowledge.*` | 知识库配置 | 🟢 KnowledgeService |
| `ai-gateway.rss.*` | RSS配置 | 🟢 RSSService |
| `ai-gateway.media.*` | 媒体配置 | 🟢 MediaService |
| `ai-gateway.log.*` | 日志配置 | 🟢 Logger工具 |

### ✅ 外部服务集成

| 服务类型 | 具体服务 | 集成方式 |
|---------|---------|---------|
| 模型API | SiliconFlow | OpenAI兼容格式代理 |
| 模型API | OpenAI/GPT | 直接代理 |
| 搜索服务 | SearxNG | WebSearch Skill |
| 搜索服务 | LibreX | WebSearch Skill |
| 搜索服务 | 4get | WebSearch Skill |

---

## 八、待确认问题

### 🔍 需要您确认的设计决策：

1. **前端技术栈选择**
   - 推荐：Vue 3 + TypeScript + Element Plus
   - 备选：React + TypeScript + Ant Design
   - 您的偏好是？

2. **Whisper处理器选择**
   - 开发环境(无显卡32G)：faster_whisper (CPU模式)
   - 部署环境(AMD aimax 395 96G显存)：whisper_npu 或 faster_whisper (GPU模式)
   - 是否需要同时支持CPU/GPU自动检测？

3. **Skill系统执行方式**
   - 选项A: Python函数动态加载 (推荐，简单高效)
   - 选项B: 独立进程/微服务 (复杂但隔离性好)
   - 您的选择？

4. **Web搜索Skill实现**
   - SearxNG/LibreX/4get 是通过API调用还是直接集成搜索逻辑？
   - 是否需要支持多搜索引擎结果聚合？

5. **文件上传大小限制**
   - 视频：100MB (当前配置)
   - 音频：100MB (当前配置)
   - 是否需要支持更大文件的分片上传？

---

## 九、下一步建议

确认以上问题后，建议按以下顺序进行：

1. **Phase 3**: 数据库Schema设计 (MongoDB Collections + Qdrant Collections)
2. **Phase 4**: API接口规范设计 (OpenAPI/Swagger文档)
3. **Phase 5**: Skill系统接口规范详细设计
4. **Phase 6**: 项目初始化和开发计划

---

**以上架构是否满足您的需求？请确认或提出修改意见。**
