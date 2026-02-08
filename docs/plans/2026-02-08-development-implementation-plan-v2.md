# AI Gateway 开发实施计划 v2.0

> **日期**: 2026-02-08  
> **版本**: v2.0  
> **预计工期**: 5-6周  
> **核心约束**: 配置管理Template Pattern - virtual_models可增删改，其他节点只改值不改Key

---

## 设计模式规范

### 1. 配置管理 - Template Pattern

**核心实现**:
```python
class ConfigTemplate(ABC):
    """配置模板基类"""
    
    @abstractmethod
    def can_modify_structure(self) -> bool:
        """是否允许修改结构（增删Key）"""
        pass

class VirtualModelsTemplate(ConfigTemplate):
    """virtual_models节点 - 完全自由"""
    def can_modify_structure(self) -> bool:
        return True  # 允许新增/删除模型

class FixedNodeTemplate(ConfigTemplate):
    """固定节点 - 只改值不改Key"""
    def can_modify_structure(self) -> bool:
        return False  # 不允许增删Key
    
    def validate_value_change(self, key_path, old_val, new_val):
        if not self._key_exists_in_template(key_path):
            raise ConfigError(f"不允许修改Key: {key_path}")
```

**配置管理器**:
```python
class ConfigManager:
    """基于Template Pattern的配置管理"""
    
    def add_virtual_model(self, name, config):
        """唯一允许新增节点的操作"""
        template = self._templates["virtual_models"]
        if not template.can_modify_structure():
            raise ConfigError("不允许修改结构")
        # ... 添加逻辑
    
    def set(self, key_path, value):
        """修改值 - 会验证是否允许"""
        node_type = key_path.split('.')[0]
        template = self._templates[node_type]
        template.validate_value_change(key_path, old_val, value)
        # ... 修改逻辑
```

### 2. 媒体处理 - Strategy Pattern

```python
class MediaProcessor(ABC):
    """媒体处理器策略接口"""
    
    @abstractmethod
    async def extract_content(self, file_path: str) -> str:
        pass

class TextProcessor(MediaProcessor): ...
class VideoProcessor(MediaProcessor): ...  # Whisper
class AudioProcessor(MediaProcessor): ...  # Whisper（复用Video逻辑）
class ImageProcessor(MediaProcessor): ...  # OCR
```

### 3. Skill配置 - Strategy Pattern

各模块独立实现Skill配置，通过config_path读取/修改config.yml:

```python
class SkillBase(ABC):
    @property
    @abstractmethod
    def config_path(self) -> str:
        """config.yml中的路径，如 'ai-gateway.router.skill'"""
        pass
    
    def is_enabled(self) -> bool:
        return config.get(f"{self.config_path}.enabled", False)
    
    def set_enabled(self, enabled: bool):
        """只改值，不改Key"""
        config.set(f"{self.config_path}.enabled", enabled)
```

---

## 里程碑规划

| 里程碑 | 内容 | 时间 | 优先级 |
|--------|------|------|--------|
| **M1** | 基础设施 + 框架 | Week 1 | P0 |
| **M2** | 日志 + 看板 + 系统配置 | Week 2 | P1 |
| **M3** | 虚拟模型 + 路由转发 | Week 2-3 | P1 |
| **M4** | 会话模块 | Week 3 | P2 |
| **M5** | 原始数据 + 知识提取 | Week 4 | P2 |
| **M6** | 知识检索 + Skill系统 | Week 4-5 | P2 |
| **M7** | 媒体模块 (Text/Video/Audio) | Week 5 | P3 |
| **M8** | RSS模块 | Week 5-6 | P3 |
| **M9** | 集成测试 + 优化 | Week 6 | P3 |

---

## Phase 1: 基础设施 (Week 1)

### 任务 1.1: Docker Compose 基础设施
**预计**: 6-8小时 | **阻塞**: 无

**服务清单**:
- MongoDB (27017) - 数据持久化
- Redis (6379) - 缓存/会话
- Qdrant (6333) - 向量库
- SearxNG (8080) - 搜索服务
- LibreX (8081) - 搜索服务
- 4get (8082) - 搜索服务

**文件**:
- `docker-compose.yml`
- `docker/.env.example`
- `docker/mongodb/init.js`
- `docker/redis/redis.conf`

---

### 任务 1.2: 后端框架 + 配置管理（Template Pattern）
**预计**: 10-12小时 | **阻塞**: 任务1.1

**文件结构**:
```
./app/
├── main.py                      # FastAPI入口
├── core/
│   ├── config_manager.py        # 配置管理器
│   ├── config_template.py       # 配置模板定义
│   ├── logger.py               # 双轨制日志
│   ├── exceptions.py
│   └── middleware.py
├── db/
│   ├── mongodb.py
│   ├── redis.py
│   └── qdrant.py
└── models/
    ├── base.py
    └── log.py
```

**关键实现要点**:
1. ConfigManager使用Template Pattern验证修改
2. virtual_models可增删改
3. 其他节点只改值不改Key
4. 文件热重载监听

**验证测试**:
```python
# ✅ 允许
config.add_virtual_model("test", {...})
config.set("knowledge.threshold.extraction", 0.75)

# ❌ 禁止（抛出ConfigStructureError）
config.set("knowledge.new_key", "value")
```

---

### 任务 1.3: 前端框架搭建
**预计**: 8-10小时 | **阻塞**: 无（可与1.2并行）

**文件结构**:
```
./wei-ui/
├── src/
│   ├── router/
│   │   └── index.ts        # 所有路由
│   ├── stores/
│   │   └── index.ts        # Pinia
│   ├── api/
│   │   └── request.ts      # Axios封装
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Config.vue      # 系统配置（只读）⭐
│   │   ├── Logs.vue
│   │   ├── Models.vue
│   │   ├── Chat.vue
│   │   ├── RawData.vue     # 原始数据 ⭐
│   │   ├── Knowledge.vue
│   │   ├── Media.vue
│   │   └── RSS.vue
│   └── components/
│       └── Layout/
│           ├── Layout.vue
│           ├── Sidebar.vue
│           └── Header.vue
```

---

## Phase 2: 核心基础模块 (Week 2)

### 任务 2.1: 日志模块（前后端+联调）
**预计**: 1.5天 | **阻塞**: 任务1.2, 1.3

**后端**:
- `app/services/log_service.py`
- `app/routers/logs.py`

**API**:
```python
GET /proxy/admin/logs?level=INFO&page=1&size=20
POST /proxy/admin/logs/export
```

**验收**:
- 日志双轨制（MongoDB + 文件）
- ERROR日志强制保存到/logs/error/

---

### 任务 2.2: 系统配置模块（只读）⭐新增
**预计**: 1天 | **阻塞**: 任务1.2, 1.3

**说明**: 只读展示config.yml，方便核对配置

**后端**:
```python
GET /proxy/admin/config       # 返回整个config.yml
GET /proxy/admin/config/:node # 返回指定节点
```

**前端**:
- 树形展示config.yml
- 语法高亮
- 节点折叠/展开
- 搜索Key

**⚠️ 注意**: 此界面只读，修改通过各自模块的API

---

### 任务 2.3: 看板模块（前后端+联调）
**预计**: 2天 | **阻塞**: 任务2.1

**后端**:
```python
GET /proxy/admin/dashboard/stats
# 返回: today_requests, active_sessions, knowledge_count, 
#       model_usage, system_status, rss_status
```

**前端**:
- 统计卡片
- 请求趋势图（Echarts）
- 模型使用占比饼图
- 系统状态指示器

---

## Phase 3: 虚拟模型与路由 (Week 2-3)

### 任务 3.1: 虚拟模型模块（前后端+联调）
**预计**: 2天 | **阻塞**: 任务1.2

**后端**:
- `app/services/model_service.py`
- `app/routers/models.py`

**使用ConfigManager**:
```python
class ModelService:
    def create_model(self, name, config):
        """允许新增节点"""
        config_manager.add_virtual_model(name, config)
    
    def update_model_field(self, name, field, value):
        """修改值"""
        config_manager.set(f"virtual_models.{name}.{field}", value)
    
    def delete_model(self, name):
        """删除模型"""
        config_manager.delete_virtual_model(name)
```

**API**:
```python
GET /proxy/admin/models
POST /proxy/admin/models              # 创建
PUT /proxy/admin/models/:name/switch  # 切换small/big
DELETE /proxy/admin/models/:name
```

**前端**:
- 模型列表（卡片式）
- proxy_key部分隐藏（sk-xxx...xxx）
- 创建/编辑弹窗
- 切换small/big

---

### 任务 3.2: 路由转发模块（前后端+联调）
**预计**: 2天 | **阻塞**: 任务3.1

**后端**:
- `app/routers/proxy.py` - /proxy/api/v1/*
- `app/core/router_engine.py` - 路由决策
- `app/core/model_client.py` - OpenAI客户端

**路由决策流程**:
1. 检查 force-current
2. 检查关键词路由（@大哥/@小弟）
3. 检查Skill路由（如果启用）
4. 默认使用current

**API**:
```python
POST /proxy/api/v1/chat/completions   # 复刻SiliconFlow
GET /proxy/api/v1/models
```

---

## Phase 4: 会话模块 (Week 3)

### 任务 4.1: 会话模块（前后端+联调+测试）
**预计**: 3天 | **阻塞**: 任务3.2

**后端**:
- `app/services/chat_service.py`
- `app/routers/chat.py`

**关键功能**:
- SSE流式响应
- 会话状态管理（Redis TTL=24h）
- 消息持久化（MongoDB）
- 模型切换提示

**API**:
```python
GET /proxy/admin/chat/sessions
GET /proxy/admin/chat/sessions/:id
DELETE /proxy/admin/chat/sessions/:id
POST /proxy/admin/chat/sessions/:id/messages
```

**前端**:
- 左右分栏布局
- 会话列表（搜索、新建、删除）
- 聊天界面
- SSE流式消息接收

---

## Phase 5: 原始数据与知识系统 (Week 4)

### 任务 5.1: 原始数据模块（前后端+联调）⭐新增
**预计**: 2天 | **阻塞**: 任务4.1

**说明**: 统一管理所有知识源的原始数据（对话、RSS、视频、音频、文本、图片）

**后端**:
- `app/services/raw_data_service.py`
- `app/routers/raw_data.py`

**数据库Schema**:
```yaml
knowledge_sources:
  - source_id: string (唯一)
  - source_type: enum [chat, video, audio, text, image, rss]
  - source_category: string
  - raw_content: {title, content, url, file_path}
  - metadata: {source_name, source_session, source_feed}
  - processing_status: enum [pending, extracting, extracted, failed]
  - extraction_count: int
  - is_edited: boolean
  - created_at: datetime
```

**API**:
```python
GET /proxy/admin/raw-data?source_type=&status=&search=
GET /proxy/admin/raw-data/:id
PUT /proxy/admin/raw-data/:id       # 编辑内容
DELETE /proxy/admin/raw-data/:id
POST /proxy/admin/raw-data/:id/extract  # 手动提取
POST /proxy/admin/raw-data/batch    # 批量操作
```

**前端功能**:
- 来源分类统计（💬 523 | 📡 421 | 🎥 156...）
- 状态筛选（待处理/已提取/失败）
- 搜索（标题、内容）
- 编辑原始内容
- 手动触发提取

---

### 任务 5.2: 知识提取模块（前后端+联调）
**预计**: 2天 | **阻塞**: 任务5.1

**后端**:
- `app/services/knowledge_service.py`
- `app/core/skill_executor.py`

**自动触发时机**:
- 对话结束后自动提取 → 原始数据 → 提取Skill → Qdrant
- RSS抓取后自动提取
- 媒体转录完成后自动提取

---

### 任务 5.3: 知识检索（RAG）模块（前后端+联调）
**预计**: 1.5天 | **阻塞**: 任务5.2

**后端**:
```python
POST /proxy/admin/knowledge/query
{
  "query": "系统架构设计",
  "top_k": 5,
  "threshold": 0.76,  # 使用config.yml中的值
  "source_types": ["chat", "rss"]
}
```

**前端**:
- 知识检索测试界面
- 相似度阈值显示
- 来源筛选
- 结果展示

---

## Phase 6: Skill系统 (Week 4-5)

### 任务 6.1: Skill系统基础（Strategy Pattern）
**预计**: 2天 | **阻塞**: 任务3.2

**文件结构**:
```
./skill/
├── base.py                    # Skill基类
├── loader.py                  # Skill加载器
├── executor.py                # Skill执行器
├── router/v1/SKILL.md         # 路由Skill描述
├── router/v1/skill.py         # 路由Skill实现
├── knowledge/v1/SKILL.md
├── knowledge/v1/skill.py
└── web_search/v1/
    ├── SKILL.md
    └── skill.py
```

**Skill基类**:
```python
class SkillBase(ABC):
    @property
    @abstractmethod
    def config_path(self) -> str:
        """config.yml路径，如 'ai-gateway.router.skill'"""
        pass
    
    def is_enabled(self) -> bool:
        return config.get(f"{self.config_path}.enabled", False)
    
    def set_enabled(self, enabled: bool):
        """只改值，不改Key"""
        config.set(f"{self.config_path}.enabled", enabled)
```

---

### 任务 6.2: 各模块集成Skill配置
**预计**: 1天 | **阻塞**: 任务6.1

在各业务模块中集成各自的Skill配置:
- 路由模块 → RouterSkill
- 知识提取模块 → KnowledgeExtractSkill  
- Web搜索模块 → WebSearchSkill

每个Skill独立管理自己的config.yml配置节点

---

## Phase 7: 媒体模块 (Week 5)

### 任务 7.1: 媒体基础框架 + Text模块（Strategy Pattern）
**预计**: 1.5天 | **阻塞**: 任务5.1

**实现**:
```python
class MediaProcessor(ABC):
    """媒体处理器策略接口"""
    
    @abstractmethod
    async def extract_content(self, file_path: str) -> str:
        pass

class TextProcessor(MediaProcessor): ...
class ImageProcessor(MediaProcessor): ...  # OCR

class WhisperProcessor(MediaProcessor):
    """Video/Audio共用Whisper基类"""
    async def extract_content(self, file_path):
        # CPU/GPU自动检测
        device = "cuda" if torch.cuda.is_available() else "cpu"
        whisper = whisper.load_model("base", device=device)
        return await whisper.transcribe(file_path)

class VideoProcessor(WhisperProcessor): ...
class AudioProcessor(WhisperProcessor): ...
```

---

### 任务 7.2: Video模块（前后端+测试）
**预计**: 2天 | **阻塞**: 任务7.1

**功能**:
- 视频上传
- Whisper转录
- 转录结果保存
- 自动触发知识提取

---

### 任务 7.3: Audio模块（前后端+测试）
**预计**: 1.5天 | **阻塞**: 任务7.1

**说明**: 复用WhisperProcessor基类

---

## Phase 8: RSS模块 (Week 5-6)

### 任务 8.1: RSS模块（前后端+联调）
**预计**: 2.5天 | **阻塞**: 任务7.1

**后端**:
- `app/services/rss_service.py`
- `app/tasks/rss_scheduler.py` - 定时任务

**功能**:
- RSS抓取（定时）
- 内容存储（MongoDB）
- 自动提取知识
- Skill配置集成

---

## Phase 9: 集成测试 (Week 6)

### 任务 9.1: 集成测试与优化
**预计**: 3天 | **阻塞**: 所有前述任务

**测试内容**:
- [ ] End-to-end测试（完整对话流程）
- [ ] 配置管理测试（Template Pattern验证）
- [ ] 并发测试
- [ ] 性能测试
- [ ] 错误恢复测试

**文档**:
- README.md
- docs/DEPLOYMENT.md
- docs/API.md

---

## 配置管理验证清单

开发过程中必须持续验证：

```python
# ✅ 允许的操作
config.add_virtual_model("test", {...})                    # 新增模型
config.delete_virtual_model("test")                        # 删除模型
config.set("virtual_models.test.current", "big")          # 修改值
config.set("knowledge.threshold.extraction", 0.75)        # 修改值
config.set("knowledge.skill.enabled", False)              # 修改值

# ❌ 禁止的操作（会抛出ConfigStructureError）
config.set("knowledge.new_field", "value")                # 新增Key
config.set("rss.new_feed", {...})                         # 新增Key
del config._config["knowledge"]["threshold"]              # 删除Key
```

---

## 任务依赖图

```
Week 1:
  [1.1 Docker] ──┬──> [1.2 后端框架]
                └──> [1.3 前端框架]

Week 2:
  [2.1 日志] ──> [2.2 系统配置]
              ──> [2.3 看板]
              ──> [3.1 虚拟模型]

Week 3:
  [3.2 路由转发] ──> [4.1 会话模块]
                 ──> [5.1 原始数据]

Week 4:
  [5.2 知识提取] ──> [5.3 知识检索]
                ──> [6.1 Skill系统]

Week 5:
  [6.2 Skill集成] ──> [7.1 媒体基础]
                  ──> [7.2 Video]
                  ──> [7.3 Audio]
                  ──> [8.1 RSS]

Week 6:
  [9.1 集成测试]
```

---

## 总结

| 项目 | 数值 |
|------|------|
| **总任务数** | 23个 |
| **预计工期** | 5-6周 |
| **核心设计模式** | Template Pattern（配置）+ Strategy Pattern（媒体/Skill） |
| **新增模块** | 原始数据管理、系统配置查看、RAG检索 |

**关键约束已落实**:
- ✅ Template Pattern确保配置管理铁律
- ✅ Strategy Pattern实现媒体处理器复用
- ✅ 原始数据模块在知识提取之前完成
- ✅ 系统配置只读界面
- ✅ RAG查询功能
- ✅ 各模块独立管理Skill配置（只改值不改Key）

---

**准备开始实施？** 还是从Phase 1任务1.1开始？
