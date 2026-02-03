# TW AI Saver - 使用指南

> TW AI Saver 是一个本地可部署的 AI 代理中枢，支持多种 AI 提供商统一管理。

---

## 目录

- [快速开始](#快速开始)
- [系统架构](#系统架构)
- [功能特性](#功能特性)
- [API 文档](#api-文档)
- [前端使用](#前端使用)
- [baseskill 模板](#baseskill-模板)
- [常见问题](#常见问题)

---

## 快速开始

### 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.10 | 3.13 |
| MongoDB | 6.0 | 7.0 |
| Qdrant | 1.0 | 1.7 |
| Node.js | 18.0 | 20.0 |

### 1. 克隆项目

```bash
git clone <repository-url>
cd ytzc-ai-proxy
```

### 2. 启动后端服务

```bash
cd proxy-api

# 安装依赖
pip install -r requirements.txt

# 启动服务 (默认端口 8080)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 3. 启动前端 (可选)

```bash
cd web-ui

# 安装依赖
npm install

# 启动开发服务器 (默认端口 3000)
npm run dev
```

### 4. 访问系统

| 服务 | 地址 | 说明 |
|------|------|------|
| API 文档 | http://localhost:8080/docs | Swagger UI |
| API 文档 | http://localhost:8080/redoc | ReDoc |
| 前端界面 | http://localhost:3000 | Vue 3 应用 |
| 健康检查 | http://localhost:8080/health | 服务状态 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      TW AI Saver                            │
├─────────────────────────────────────────────────────────────┤
│  前端层 (Vue 3 + Element Plus)                               │
│  ├── Dashboard     - 系统仪表盘                              │
│  ├── Connections   - AI 连接管理                             │
│  ├── Sessions      - 会话管理                                │
│  ├── Skills        - 技能模板                                │
│  ├── Vectors       - 向量数据库                              │
│  ├── Backups       - 备份管理                                │
│  ├── Config        - 系统配置                                │
│  └── BaseSkills    - 基础技能模板                            │
├─────────────────────────────────────────────────────────────┤
│  API 层 (FastAPI)                                           │
│  ├── /api/v1/connections  - 连接管理 API                     │
│  ├── /api/v1/sessions     - 会话管理 API                     │
│  ├── /api/v1/skills       - 技能管理 API                     │
│  ├── /api/v1/vectors      - 向量管理 API                     │
│  ├── /api/v1/baseskills   - 基础技能 API                     │
│  └── /proxy/v1/           - OpenAI 兼容代理                  │
├─────────────────────────────────────────────────────────────┤
│  服务层                                                    │
│  ├── SessionSummarizer   - 自动会话摘要                      │
│  ├── SkillZipHandler     - ZIP 导入/导出                     │
│  └── BaseSkillService    - 基础技能服务                      │
├─────────────────────────────────────────────────────────────┤
│  数据层                                                    │
│  ├── MongoDB 7.0  - 结构化数据存储                           │
│  └── Qdrant       - 向量相似度搜索                           │
├─────────────────────────────────────────────────────────────┤
│  AI 提供商                                                 │
│  ├── OpenAI      - GPT-4o, GPT-3.5-turbo                    │
│  ├── Anthropic   - Claude 3.5 Sonnet                        │
│  ├── DeepSeek    - DeepSeek Chat                            │
│  ├── Google      - Gemini 1.5 Pro                           │
│  └── SiliconFlow - 硅基流动                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 功能特性

### 1. AI 连接管理

支持连接多个 AI 提供商，统一管理 API Key 和配置。

**支持的提供商：**
- OpenAI
- Anthropic Claude
- DeepSeek
- Google Gemini
- 硅基流动 (SiliconFlow)

### 2. 智能代理转发

通过 `/proxy/v1/` 或 `/proxy/v1/chat/completions` 端点统一调用，兼容 OpenAI API 格式。

**支持的客户端**: OpenAI 官方 SDK、ChatBox、NextChat、LibreChat 等所有兼容 OpenAI API 的客户端。

```bash
# 聊天完成 (OpenAI 兼容端点)
curl -X POST http://localhost:8080/proxy/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {proxy_key}" \
  -d '{
    "model": "SiliconFlow/DeepSeek",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

**认证方式**:
- Header: `Authorization: Bearer {proxy_key}`
- Proxy Key 格式: `tw-{24位十六进制字符}` (共27字符)

**模型选择**:
- 前端会显示连接名称作为模型 ID (如 "SiliconFlow/DeepSeek")
- 实际请求会自动路由到对应的小模型或大模型配置

### 3. 会话管理

- 创建/查询/删除会话
- 自动生成会话摘要
- 消息历史记录

### 4. 技能系统 (Skill)

- 创建和管理自定义技能
- 版本控制 (发布/回滚)
- ZIP 导入/导出
- Prompt 模板管理

### 5. 向量数据库

- 集合管理
- 语义搜索
- 批量操作

### 6. baseskill 模板

系统内置基础技能模板：

| 模板 | 功能 |
|------|------|
| skill-generator | 技能生成器 |
| session-summarizer | 会话摘要生成 |
| vectorizer | 向量化处理 |
| skill-name-generator | 技能命名生成 |

---

## API 文档

### 连接管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/connections | 列出所有连接 |
| POST | /api/v1/connections | 创建连接 |
| PUT | /api/v1/connections/{id} | 更新连接 |
| DELETE | /api/v1/connections/{id} | 删除连接 |
| POST | /api/v1/connections/{id}/test | 测试连接 |

### 会话管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/sessions | 列出会话 |
| POST | /api/v1/sessions | 创建会话 |
| GET | /api/v1/sessions/{id} | 获取会话详情 |
| PUT | /api/v1/sessions/{id} | 更新会话 |
| DELETE | /api/v1/sessions/{id} | 删除会话 |
| GET | /api/v1/sessions/{id}/messages | 获取消息列表 |

### 技能管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/skills | 列出技能 |
| POST | /api/v1/skills | 创建技能 |
| GET | /api/v1/skills/{id} | 获取技能详情 |
| PUT | /api/v1/skills/{id} | 更新技能 |
| DELETE | /api/v1/skills/{id} | 删除技能 |
| POST | /api/v1/skills/{id}/publish | 发布技能 |
| POST | /api/v1/skills/{id}/rollback | 回滚版本 |
| GET | /api/v1/skills/{id}/export | 导出为 ZIP |
| POST | /api/v1/skills/upload | 导入 ZIP |

### 向量管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/vectors/collections | 列出集合 |
| POST | /api/v1/vectors/search | 搜索向量 |
| POST | /api/v1/vectors/upsert | 插入向量 |
| POST | /api/v1/vectors/delete | 删除向量 |

### baseskill 管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/baseskills | 列出模板 |
| POST | /api/v1/baseskills | 创建模板 |
| GET | /api/v1/baseskills/{id} | 获取模板详情 |
| PUT | /api/v1/baseskills/{id} | 更新模板 |
| DELETE | /api/v1/baseskills/{id} | 删除模板 |
| PUT | /api/v1/baseskills/{id}/enable | 启用模板 |
| PUT | /api/v1/baseskills/{id}/disable | 禁用模板 |
| POST | /api/v1/baseskills/reload | 重载模板 |

---

## 前端使用

### 登录

首次访问需要输入 Proxy Key：

```
默认 Proxy Key: tw-537294261af9b0d492653794
```

### 仪表盘

- 查看系统统计信息
- 监控连接、会话、技能数量
- 查看 AI 提供商分布
- 系统状态监控

### 连接管理

在「连接管理」页面中，您可以添加和管理 AI 提供商的连接。

#### 添加连接步骤

1. 点击「添加连接」
2. 填写连接配置（小模型必填，大模型可选）
3. 点击「测试小模型」验证配置
4. 点击「刷新」按钮生成 Proxy Key
5. 点击「保存」

#### 第三方客户端调用配置

**⚠️ 重要：客户端（如 ChatBox、NextChat）需要使用 TW AI Saver 的代理地址**

| 设置项 | 值 |
|--------|-----|
| **API 地址** | `http://localhost:8080/proxy/v1/` |
| **Auth 密钥** | 连接列表中的 Proxy Key |
| **模型名称** | 填写上面配置的小模型名称 |

#### 错误示例 ❌

```
在 ChatBox 中：
API 地址: https://api.siliconflow.cn/v1           # 错误：这是 AI 提供商地址
API 地址: http://localhost:8080/api/v1/connections # 错误：这是管理 API
模型名称: deepseek-chat                           # 错误：需要完整模型名
```

#### 正确示例 ✅

```
在 ChatBox 中：
API 地址: http://localhost:8080/proxy/v1/          # 正确：TW AI Saver 代理地址
Auth:     tw-20847477705e                          # 正确：Proxy Key
模型:     deepseek-ai/DeepSeek-R1-0528-Qwen3-8B   # 正确：完整模型名
```

#### API 参考

实际请求转发到 AI 提供商，参考 SiliconFlow API：

```bash
# 请求格式
curl -X POST http://localhost:8080/proxy/v1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <Proxy Key>" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

#### 各提供商配置示例

**⚠️ 重要：AI Base URL 必须以 `/v1` 结尾，且是 AI 提供商的地址，不是 TW AI Saver 的地址**

| 提供商 | AI Base URL (AI 提供商) | 模型名称 |
|--------|-------------------------|----------|
| **硅基流动** | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini` |
| **Anthropic** | `https://api.anthropic.com/v1` | `claude-sonnet-4-20250514` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Google** | `https://generativelanguage.googleapis.com/v1` | `gemini-1.5-pro` |

#### Proxy Key 说明

- **用途**: 客户端调用 API 时的认证凭据
- **格式**: `tw-` + 24位十六进制字符串
- **生成**: 点击表单中的「刷新」按钮自动生成
- **安全**: 建议每个连接使用独立的 Proxy Key

### 会话管理

1. 点击「新建会话」
2. 输入会话标题
3. 在会话详情中查看消息
4. 支持批量删除会话

### 技能管理

1. 点击「新建技能」
2. 填写名称、描述
3. 编写 Prompt 模板
4. 配置规则 (YAML 格式)
5. 发布技能

### 导入/导出

- **导出**: 点击导出按钮下载 ZIP
- **导入**: 点击导入按钮上传 ZIP

---

## baseskill 模板

### 模板结构

每个 baseskill 模板包含三个文件：

```
baseskill/
└── skill-name/
    ├── SKILL.md          # 技能定义
    ├── prompt-template.md # Prompt 模板
    └── rules.yaml        # 生成规则
```

### SKILL.md 示例

```yaml
---
name: skill-generator
description: 自动生成 Skill 模板
version: "1.0"
author: TW AI Saver
tags: [generator, skill, template]
---

# Skill Generator

## 使用时机
当需要生成新的 Skill 模板时使用。

## 指令
1. 分析用户需求
2. 生成符合规范的 Skill
3. 输出 YAML 格式配置
```

### 使用方式

1. 在前端进入「基础技能」页面
2. 查看所有可用模板
3. 点击「查看」查看详情
4. 启用/禁用模板

---

## 常见问题

### Q1: 后端服务无法启动？

检查端口是否被占用：
```bash
# Windows
netstat -ano | findstr :8080

# Linux/Mac
lsof -i :8080
```

### Q2: MongoDB 连接失败？

确保 MongoDB 服务已启动：
```bash
docker run -d --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:7
```

### Q3: 如何切换主题？

前端界面右上角有主题切换按钮，支持亮色/暗色模式。

### Q4: Proxy Key 是什么？

Proxy Key 是访问 API 的认证凭据，可以在系统配置中生成和管理。

### Q5: 如何备份数据？

1. 进入「备份管理」页面
2. 点击「创建备份」
3. 下载备份文件

### Q6: 如何添加新的 AI 提供商？

1. 修改 `config.yaml` 配置文件
2. 添加提供商配置
3. 重启服务

### Q7: 向量搜索没有结果？

确保：
1. 向量已正确插入
2. 集合已创建
3. 查询文本长度合适

---

## 配置文件

### config.yaml

```yaml
# 服务器配置
server:
  host: "0.0.0.0"
  port: 8080

# MongoDB 配置
mongodb:
  uri: "mongodb://localhost:27017"
  database: "tw_ai_saver"

# Qdrant 配置
qdrant:
  url: "http://localhost:6333"

# AI 提供商配置
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
    models:
      - "gpt-4o"
      - "gpt-3.5-turbo"
```

---

## Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 监控和维护

### 健康检查

```bash
curl http://localhost:8080/health
```

响应示例：
```json
{
  "status": "ok",
  "mongodb": true,
  "qdrant": true,
  "version": "1.0.0"
}
```

### 日志查看

```bash
# 后端日志
tail -f proxy-api/logs/app.log

# Nginx 日志 (如果使用)
tail -f nginx/logs/access.log
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-02-02 | 初始版本发布 |
| v1.0.1 | 2026-02-03 | 优化连接管理界面，增加 Proxy Key 自动生成功能 |
| v1.1.0 | 2026-02-03 | 简化代理地址为固定端点，添加点击复制功能 |

---

## 贡献指南

1. Fork 本项目
2. 创建特性分支
3. 提交代码
4. 创建 Pull Request

---

## 许可证

MIT License

---

> 最后更新时间: 2026-02-03
