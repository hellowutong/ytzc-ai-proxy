# AGENTS.md - AI网关系统开发指南

## 1. 项目概述

**类型**: 个人AI网关系统 (LLM代理层)  
**技术栈**: Python 3.11 (FastAPI) + Vue 3 (Element Plus)  
**基础设施**: Docker Compose, MongoDB, Redis, Qdrant  
**部署方式**: 仅本地部署，无认证
**核心功能**: 虚拟模型代理、模型路由、对话管理、知识提取、媒体处理、RSS订阅、Skill系统、日志系统,原始会话管理
**回复语言**: 必须使用中文回答 
---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  客户端 (ChatBox AI / WebChat测试页)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI网关 (Port 8000)                        │
│  ┌──────────────┐        ┌──────────────┐                   │
│  │ /proxy/ai    │        │ /admin/ai    │                   │
│  │ 虚拟AI代理    │        │ 后台管理      │                   │
│  └──────────────┘        └──────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
│ SiliconFlow  │    │ MongoDB/Redis/   │   │ Skill系统    │
│ OpenAI       │    │ Qdrant           │   │ (Anthropic)  │
│ Ollama       │    │                  │   │              │
└──────────────┘    └──────────────────┘   └──────────────┘
```

---

## 3. 强制目录规则

```
ytzc-ai-proxy/
├── backend/              # ⚠️ 后台代码（Python/FastAPI）
├── frontend/             # ⚠️ 前端项目（Vue 3 + Element Plus）
│   └── 包含WebChat测试页面   **严格遵循，谨记！**
├── test/                 # ⚠️ 永远谨记：所有测试文件保存于此！
│   ├── backend/
│   └── frontend/
│       └── screenshots/  # ⚠️ 前端debug截图存放于此
├── skills/                # ⚠️ 所有Skill模块存放于此（Anthropic规范）
│   ├── system/           # 系统默认Skill **严格遵循，谨记！**
│   │   ├── router/v1/功能一/
│   │   ├── router/v1/功能二/
│   │   └── ...
│   └── custom/           # 用户自定义Skill **严格遵循，谨记！**
│       └── ...
├── upload/               # ⚠️ 上传目录 **严格遵循，谨记！**
│   ├── video/            # 视频文件 **严格遵循，谨记！**
│   ├── audio/            # 音频文件 **严格遵循，谨记！**
│   └── textfile/         # 文档（pdf/jpg/doc/txt/md）**严格遵循，谨记！**
├── docs/                 # ⚠️ 所有文档必须存放于此 **严格遵循，谨记！**
├── logs/                 # 日志导出
│   └── skill/            # Skill执行日志 **严格遵循，谨记！**
└── docker/               # ⚠️ 部署文件（docker-compose） **严格遵循，谨记！**
```

**部署必须使用docker-compose！**

---

## 4. 配置管理规则

### 4.1 基本规则
- **config.yml只能通过UI调用后台接口修改**，禁止直接编辑
- MongoDB/Redis/Qdrant参数必须从config.yml读取
- 所有代码禁止硬编码配置值
- 不要产生垃圾空文件夹
- 配置热重载：通过 `POST /admin/ai/v1/config/reload` 手动触发

### 4.2 ⚠️ 重要约束（必须谨记）

**🔴 config.yml 修改约束**
- **所有 config.yml 添加 key 必须询问！谨记！**
- 禁止擅自添加、删除或修改 config.yml 中的配置项
- 任何配置变更必须先获得明确授权

**🔴 模板文件保护**
- **docs 目录下有 config_template.yml 文件绝对禁止修改，谨记！**
- config_template.yml 是配置模板基准文件，用于初始化和恢复
- 任何情况下不得修改此模板文件

---

## 5. 开发工作流程

### 5.1 设计文档约束

**⚠️ 前端开发必须遵循 `./docs/frontend_design.md` 的功能设计**
- 所有页面功能、按钮、交互必须严格按照文档实现 **严格遵循，谨记！**
- 如需修改设计，必须先更新文档并获得确认 **严格遵循，谨记！**
- 组件拆分、状态管理、API封装遵循文档规范 **严格遵循，谨记！**
- 修改前端功能必须经过人为确认 **严格遵循，谨记！**

**⚠️ 前端测试必须遵循TDD原则，保证100%代码覆盖率**
- 必须使用测试驱动开发（TDD）：先写测试案例（JSON文件），后写实现
- 所有测试案例保存到 `test/frontend/cases/*.test.json`
- 必须包含：单元测试、组件测试、集成测试、E2E测试、边界测试
- 代码质量要求：圈复杂度<=10，ESLint评分>=9.0，100%分支覆盖率
- 使用Vitest + Vue Test Utils + Playwright工具链

**⚠️ 后端开发必须遵循 `./docs/backend_design.md` 的架构设计**
- 存储层抽象接口必须按照文档实现，确保可替换性
- 所有核心模块必须遵循设计模式（Repository/Adapter/Factory）
- 业务代码与存储实现解耦，通过配置切换存储类型
- 如需修改架构，必须先更新文档并获得确认 **严格遵循，谨记！**

**⚠️ 后端测试必须遵循TDD原则，保证100%代码覆盖率**
- 必须使用测试驱动开发（TDD）：先写测试案例（JSON文件），后写实现
- 所有测试案例保存到 `test/backend/cases/*.test.json`
- 必须包含：单元测试、集成测试、边界测试、异常测试、性能测试
- 代码质量要求：圈复杂度<=10，Pylint评分>=9.0，100%分支覆盖率
- 使用pytest + coverage + black + isort + mypy + pylint工具链

**⚠️ 后端API开发必须遵循 `./docs/api_design.md` 的接口设计**
- 所有接口路径、请求参数、响应格式必须严格按照文档实现
- 变量名称和数据格式必须文档一致，**严格遵循，谨记！**
- 如需修改接口，必须先更新文档并获得确认 **严格遵循，谨记！**

**⚠️ 端联调必须遵循 `./docs/api_design.md`,`./docs/frontend_design.md` 的接口设计**
- 联调规则前端优先 **严格遵循，谨记！**
- 变量名称和数据格式必须文档一致 **严格遵循，谨记！**
- 如需修改接口，必须先更新文档并获得确认 **严格遵循，谨记！**

**⚠️ 前后端统一使用 `./test/shared/mock-data/api_mock_data.json` 的 Mock 数据**
- 前端开发和测试必须使用此 Mock 数据，保证与后端数据格式完全一致
- 后端测试必须使用此 Mock 数据，保证与前后期望数据一致
- Mock 数据已包含：**正常数据、边界测试数据、异常/错误数据、压力测试数据**
- 修改 Mock 数据时必须同时更新前后端代码 **严格遵循，谨记！**
- Mock 数据变更需经过确认，避免数据不一致导致联调问题 **严格遵循，谨记！**

### 5.2 手动测试流程

**⚠️ 如果我说"手动测试"，必须先部署 docker-compose，完成了通知我可以开始。**

手动测试前置步骤：
1. 确认 docker/docker-compose.yml 存在且配置正确
2. 执行 `docker-compose -f docker/docker-compose.yml up -d`
3. 等待所有服务启动完成（MongoDB、Redis、Qdrant、Searxng、LibreX、4get）
5. 必须使用docker-compose部署前后端.**严格遵循，谨记！**
6. 验证服务健康状态
7. **通知用户**："docker-compose 部署完成，可以开始手动测试"

### 5.3 开发顺序

必须严格按照以下15步顺序开发，每一步完成后才能进入下一步：

1. docker-compose搭建第三方依赖
2. 搭建后端整体框架
3. 搭建前端整体框架（包括菜单）
4. 开发+联调：系统模块
5. 开发+联调：日志模块
6. 开发+联调：看板模块
7. 开发+联调：Skill管理模块
8. 开发+联调：虚拟模型模块
9. 开发+联调：虚拟模型配置模块
10. 开发+联调：路由转发模块
11. 开发+联调：会话模块
12. 开发+联调：知识提取模块
13. 开发+测试：media/text模块
14. 开发+联调：media/audio模块
15. 开发+联调：media/video模块
16. 开发+联调：RSS模块
17. 开发+联调: 原始会话模块
---

## 5. 构建与测试命令

### 后端

```bash
cd backend
pip install -r requirements.txt

# 运行测试
pytest ../test/backend -v --tb=short

# 运行单个测试
pytest ../test/backend/test_api.py::test_health_check -v
```

### 前端

```bash
cd frontend
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 测试截图目录：../test/frontend/screenshots/
```

### Docker

```bash
# 启动所有依赖服务
docker-compose -f docker/docker-compose.yml up -d

# 服务包括：mongodb, redis, qdrant, searxng, librex, 4get
```

---

## 6. 代码规范

### Python

```python
# 命名
snake_case 变量/函数
PascalCase 类名
UPPER_SNAKE_CASE 常量

# 导入顺序
stdlib → third-party → local

# 错误处理
import logging
logger = logging.getLogger(__name__)

try:
    result = await process()
except ValueError as e:
    logger.error(f"失败: {e}")
    raise
```

### Vue/TypeScript

```typescript
// 命名
camelCase 变量
PascalCase 组件名

// 错误处理
try {
  await fetchData()
} catch (error) {
  console.error("失败:", error)
  ElMessage.error("操作失败")
}
```

---

## 7. Skill系统规范（Anthropic规范）

### 目录结构

```
skill/
├── system/分类/v1/功能名称/
│   ├── SKILL.md              # 必须：YAML frontmatter定义
│   └── execute.py            # 可选：Python执行文件
└── custom/分类/v1/功能名称/
    └── ...
```

### SKILL.md格式

```yaml
---
name: skill名称
description: 功能描述
type: rule-based | llm-based | hybrid
priority: 1-100
version: "1.0.0"
input_schema:
  type: object
  properties:
    param1: {type: string}
output_schema:
  type: object
  properties:
    result: {type: string}
---
```

### 7类Skill管理

1. **router** - 模型路由决策（关键词/意图识别）- ⚠️ 已下沉到虚拟模型的 `routing` 配置中
2. **virtual_models** - 虚拟模型Skill（knowledge/web_search）
3. **knowledge** - 知识提取与检索
4. **rss** - RSS订阅处理
5. **audio** - 音频转录处理
6. **video** - 视频处理
7. **text** - 文档解析

### 虚拟模型路由配置（重要变更）

**⚠️ 架构变更**：路由配置已从全局 `ai-gateway.router` 下沉到每个虚拟模型的 `routing` 字段。

每个虚拟模型独立配置：
```yaml
virtual_models:
  demo1:
    routing:
      keywords:
        enable: true
        rules:
        - pattern: '@大哥'
          target: big
        - pattern: '@小弟'
          target: small
      skill:
        enabled: true
        version: v1
        custom:
          enabled: false
          version: v2
```

路由优先级（虚拟模型级别）：
1. **force_current** - 强制使用当前模型
2. **routing.keywords** - 虚拟模型的关键词规则
3. **routing.skill** - 虚拟模型的 Skill 路由
4. **current** - 默认当前模型

### Skill验证

- **文件验证**: SKILL.md格式验证（Pydantic）
- **输入验证**: JSON Schema验证
- **输出验证**: JSON Schema验证
- **执行验证**: 异常捕获与日志记录

### Skill日志

```
logs/skill/
├── system.log          # 加载/执行/错误信息
├── execution_YYYYMMDD.log  # 详细JSON执行记录
└── operation.log       # MongoDB操作日志
```

---

## 8. API结构

### 虚拟AI代理API `/proxy/ai/v1`

| 端点 | 说明 |
|------|------|
| POST /chat/completions | 对话接口（支持SSE流式） |
| GET /models | 模型列表 |
| POST /embeddings | 向量嵌入 |

### 后台管理API `/admin/ai/v1`

| 端点 | 说明 |
|------|------|
| GET/POST /config | 配置管理 |
| POST /skills/reload | 重载Skill |
| GET /skills/logs | 查询Skill日志 |
| GET /conversations | 对话历史 |
| GET /knowledge | 知识库管理 |
| GET /media | 媒体文件管理 |
| GET /rss | RSS订阅管理 |
| GET /logs | 系统日志查询 |

**注意**: 所有API无认证，仅本地部署使用

---

## 6. Git工作流

- **分支命名**: `feature/`, `bugfix/`, `hotfix/`前缀
- **提交规范**: `feat:`, `fix:`, `docs:`, `refactor:`
- **合并要求**: 本地测试通过

---

## 7. 硬件环境

- **开发**: AMD Ryzen 9 6900HX, 32GB内存, 无显卡
- **部署**: AMD aimax 395, 128GB内存, 96GB显存, Ollama 64G模型

---

## 8. 安全提示

本项目设计为**本地私有部署**，API端点**无认证**。
- 禁止暴露到公网
- 仅在可信本地网络运行
- 公网访问需通过反向代理添加认证
