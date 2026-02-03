# TW AI 节能器 - API 文档

> 版本: 1.0.0  
> 更新日期: 2026-02-02

---

## 1. 概述

TW AI 节能器是一个本地可部署的 AI 代理中枢，提供统一的 API 接口来管理多个 AI 供应商的模型。

### 1.1 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| API | http://localhost:8080 | 主 API 服务 |
| Swagger UI | http://localhost:8080/docs | 交互式 API 文档 |
| ReDoc | http://localhost:8080/redoc | 另一种 API 文档风格 |

### 1.2 认证方式

所有 `/proxy/v1/*` 接口需要认证：

```bash
# 认证头格式
Authorization: Bearer tw-a1b2c3d4e5f6g7h8i9j0k
# 或直接使用
Authorization: tw-a1b2c3d4e5f6g7h8i9j0k
```

### 1.3 速率限制

- 默认限制: 100 请求/分钟
- 响应头包含速率限制信息

---

## 2. API 分类

### 2.1 系统 API

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | /health | 健康检查 | 无 |
| GET | /api/v1/version | 版本信息 | 无 |
| GET | /api/v1/stats | 统计信息 | 无 |
| GET | /api/v1/logs | 查看日志 | 无 |

### 2.2 代理 API (需要认证)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /proxy/v1/models | 列出可用模型 |
| POST | /proxy/v1/chat/completions | 聊天补全 |
| POST | /proxy/v1/embeddings | 向量嵌入 |

### 2.3 连接管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/connections | 列出连接 |
| POST | /api/v1/connections | 创建连接 |
| GET | /api/v1/connections/{id} | 获取连接 |
| PUT | /api/v1/connections/{id} | 更新连接 |
| DELETE | /api/v1/connections/{id} | 删除连接 |
| PUT | /api/v1/connections/{id}/disable | 禁用连接 |
| PUT | /api/v1/connections/{id}/enable | 启用连接 |
| PUT | /api/v1/connections/{id}/regenerate-key | 重新生成 Key |

### 2.4 供应商配置

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/providers | 列出供应商 |
| PUT | /api/v1/providers | 更新供应商 |
| POST | /api/v1/providers/test | 测试连通性 |
| POST | /api/v1/providers/reload | 重载配置 |

### 2.5 会话管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/sessions | 列出会话 |
| POST | /api/v1/sessions | 创建会话 |
| GET | /api/v1/sessions/{id} | 获取会话 |
| PUT | /api/v1/sessions/{id} | 更新会话 |
| DELETE | /api/v1/sessions/{id} | 删除会话 |
| GET | /api/v1/sessions/{id}/messages | 获取消息 |
| POST | /api/v1/sessions/{id}/messages | 添加消息 |
| PUT | /api/v1/sessions/{id}/messages/{msg_id} | 更新消息 |
| DELETE | /api/v1/sessions/{id}/messages/{msg_id} | 删除消息 |
| POST | /api/v1/sessions/{id}/end | 结束会话 |
| POST | /api/v1/sessions/{id}/generate-skill | 生成 Skill |
| POST | /api/v1/sessions/batch-delete | 批量删除 |

### 2.6 Skill 管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/skills | 列出 Skill |
| POST | /api/v1/skills | 创建 Skill |
| GET | /api/v1/skills/{id} | 获取 Skill |
| PUT | /api/v1/skills/{id} | 更新 Skill |
| DELETE | /api/v1/skills/{id} | 删除 Skill |
| GET | /api/v1/skills/{id}/versions | 获取版本列表 |
| GET | /api/v1/skills/{id}/versions/{version} | 获取版本详情 |
| PUT | /api/v1/skills/{id}/versions/{version} | 更新版本 |
| DELETE | /api/v1/skills/{id}/versions/{version} | 删除版本 |
| POST | /api/v1/skills/{id}/publish | 发布版本 |
| PUT | /api/v1/skills/{id}/rollback | 回滚版本 |
| POST | /api/v1/skills/export | 导出 Skill |
| POST | /api/v1/skills/export/batch | 批量导出 |
| POST | /api/v1/skills/import | 导入 Skill |

### 2.7 向量存储

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/vectors/collections | 列出集合 |
| GET | /api/v1/vectors/collections/{name}/info | 集合信息 |
| DELETE | /api/v1/vectors/collections/{name}/delete | 清空集合 |
| POST | /api/v1/vectors/collections/{name}/rebuild | 重建索引 |
| GET | /api/v1/vectors/sessions | 搜索会话向量 |
| POST | /api/v1/vectors/sessions | 添加会话向量 |
| GET | /api/v1/vectors/sessions/{id} | 获取会话向量 |
| PUT | /api/v1/vectors/sessions/{id} | 更新会话向量 |
| DELETE | /api/v1/vectors/sessions/{id} | 删除会话向量 |
| POST | /api/v1/vectors/sessions/batch-delete | 批量删除 |
| POST | /api/v1/vectors/sessions/rebuild | 重建索引 |
| GET | /api/v1/vectors/skills | 搜索 Skill 向量 |
| POST | /api/v1/vectors/skills | 添加 Skill 向量 |
| GET | /api/v1/vectors/skills/{id} | 获取 Skill 向量 |
| PUT | /api/v1/vectors/skills/{id} | 更新 Skill 向量 |
| DELETE | /api/v1/vectors/skills/{id} | 删除 Skill 向量 |
| POST | /api/v1/vectors/skills/{id}/rebuild | 重建索引 |
| POST | /api/v1/vectors/skills/batch-delete | 批量删除 |

### 2.8 文件管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/files/skills | 列出文件 |
| GET | /api/v1/files/skills/{base_id}/{version}/skill.md | 读取 Skill 文件 |
| PUT | /api/v1/files/skills/{base_id}/{version}/skill.md | 更新 Skill 文件 |
| DELETE | /api/v1/files/skills/{base_id}/{version}/skill.md | 删除 Skill 文件 |
| GET | /api/v1/files/skills/{base_id}/{version}/examples/{name} | 读取 Example |
| PUT | /api/v1/files/skills/{base_id}/{version}/examples/{name} | 更新 Example |
| DELETE | /api/v1/files/skills/{base_id}/{version}/examples/{name} | 删除 Example |
| GET | /api/v1/files/skills/{base_id}/{version}/assets/{name} | 读取 Asset |
| PUT | /api/v1/files/skills/{base_id}/{version}/assets/{name} | 上传 Asset |
| DELETE | /api/v1/files/skills/{base_id}/{version}/assets/{name} | 删除 Asset |

### 2.9 配置管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/config | 获取配置 |
| PUT | /api/v1/config | 更新配置 |
| POST | /api/v1/config/reload | 重载配置 |

### 2.10 备份管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/backups | 列出备份 |
| POST | /api/v1/backups | 创建备份 |
| POST | /api/v1/backups/{name}/restore | 恢复备份 |
| DELETE | /api/v1/backups/{name} | 删除备份 |

### 2.11 BaseSkill 管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/baseskills | 列出模板 |
| POST | /api/v1/baseskills | 创建模板 |
| POST | /api/v1/baseskills/upload | 上传模板 |
| GET | /api/v1/baseskills/{id} | 获取模板 |
| PUT | /api/v1/baseskills/{id} | 更新模板 |
| DELETE | /api/v1/baseskills/{id} | 删除模板 |
| PUT | /api/v1/baseskills/{id}/enable | 启用模板 |
| PUT | /api/v1/baseskills/{id}/disable | 禁用模板 |
| POST | /api/v1/baseskills/reload | 重载模板 |

---

## 3. 请求示例

### 3.1 创建连接

```bash
curl -X POST http://localhost:8080/api/v1/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeepSeek Group",
    "small_model": {
      "name": "deepseek-8b",
      "base_url": "https://api.siliconflow.cn/v1/",
      "api_key": "sk-xxx"
    },
    "big_model": {
      "name": "deepseek-v3",
      "base_url": "https://api.siliconflow.cn/v1/",
      "api_key": "sk-xxx"
    }
  }'
```

### 3.2 聊天补全

```bash
curl -X POST http://localhost:8080/proxy/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer tw-your-proxy-key" \
  -d '{
    "model": "deepseek-8b",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'
```

### 3.3 列出会话

```bash
curl -X GET http://localhost:8080/api/v1/sessions \
  -H "Authorization: Bearer tw-your-proxy-key"
```

---

## 4. 响应示例

### 4.1 成功响应

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "proxy_key": "tw-a1b2c3d4e5f6",
  "status": "active",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2026-02-02T10:00:00Z"
    }
  ],
  "created_at": "2026-02-02T10:00:00Z"
}
```

### 4.2 错误响应

```json
{
  "detail": "Invalid or disabled API Key"
}
```

---

## 5. 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权，缺少或无效 API Key |
| 403 | 已禁止，API Key 被禁用 |
| 404 | 资源不存在 |
| 429 | 超出速率限制 |
| 500 | 服务器内部错误 |

---

## 6. SDK 支持

### 6.1 Python

```python
import requests

class TWProxy:
    def __init__(self, proxy_key, base_url="http://localhost:8080"):
        self.proxy_key = proxy_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {proxy_key}"}
    
    def chat_completions(self, model, messages):
        response = requests.post(
            f"{self.base_url}/proxy/v1/chat/completions",
            headers=self.headers,
            json={"model": model, "messages": messages}
        )
        return response.json()
```

---

## 7. 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-02-02 | 初始版本，106个 API 接口 |
