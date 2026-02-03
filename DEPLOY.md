# TW AI 节能器 - 部署指南

> 版本: 1.0.0  
> 日期: 2026-02-02

---

## 1. 系统要求

### 1.1 最低配置

| 组件 | 最低要求 |
|------|----------|
| CPU | 2 核心 |
| 内存 | 2 GB |
| 磁盘 | 10 GB |
| Docker | 20.x+ |
| Docker Compose | 2.x+ |

### 1.2 推荐配置

| 组件 | 推荐配置 |
|------|----------|
| CPU | 4 核心 |
| 内存 | 4 GB |
| 磁盘 | 50 GB SSD |
| Docker | 24.x+ |
| Docker Compose | 2.x+ |

---

## 2. 快速部署

### 2.1 克隆项目

```bash
git clone <repository-url>
cd ytzc-ai-proxy
```

### 2.2 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（可选）
vim .env
```

### 2.3 启动服务

```bash
# 开发模式（热重载）
docker-compose up -d

# 生产模式
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2.4 验证部署

```bash
# 检查服务状态
docker-compose ps

# 检查健康状态
curl http://localhost:8080/health

# 查看日志
docker-compose logs -f
```

---

## 3. 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| API | http://localhost:8080 | 后端 API |
| Swagger UI | http://localhost:8080/docs | API 文档 |
| Web UI | http://localhost:3000 | 前端界面 |

---

## 4. 开发模式

### 4.1 启动开发环境

```bash
# 启动所有服务（带热重载）
docker-compose up -d

# 查看日志
docker-compose logs -f proxy-api
docker-compose logs -f web-ui
```

### 4.2 代码修改

代码修改后会自动热重载：
- **proxy-api**: 修改 Python 代码自动重载
- **web-ui**: 修改 Vue 代码自动重载

### 4.3 调试

```bash
# 进入 API 容器
docker-compose exec proxy-api bash

# 运行测试
pytest tests/ -v

# 进入前端容器
docker-compose exec web-ui sh
```

---

## 5. 生产部署

### 5.1 构建生产镜像

```bash
# 构建所有镜像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 或分别构建
docker build -t ytzc-ai-proxy:prod ./proxy-api
docker build -t ytzc-web-ui:prod ./web-ui
```

### 5.2 使用 Nginx 反向代理

```bash
# 启动包含 Nginx 的配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx
```

### 5.3 配置 SSL/HTTPS

1. 获取 SSL 证书（Let's Encrypt 或其他）
2. 将证书放入 `docker/nginx/ssl/` 目录
3. 修改 `docker-compose.prod.yml` 中的端口映射

---

## 6. 数据管理

### 6.1 备份数据

```bash
# 备份 MongoDB
docker-compose exec mongodb mongodump --out=/backup/mongodb

# 备份 Qdrant
docker-compose exec qdrant tar -czf /backup/qdrant.tar.gz /qdrant/storage

# 备份文件
docker-compose exec proxy-api tar -czf /backup/data.tar.gz /app/data
```

### 6.2 恢复数据

```bash
# 恢复 MongoDB
docker-compose exec mongodb mongorestore --drop /backup/mongodb

# 恢复 Qdrant
docker-compose exec qdrant tar -xzf /backup/qdrant.tar.gz -C /

# 恢复文件
docker-compose exec proxy-api tar -xzf /backup/data.tar.gz -C /
```

### 6.3 清理数据

```bash
# 删除所有数据卷（危险！）
docker-compose down -v

# 删除部分数据卷
docker volume rm ytzc-ai-proxy_mongodb_data
docker volume rm ytzc-ai-proxy_qdrant_data
```

---

## 7. 监控与日志

### 7.1 查看日志

```bash
# 所有服务日志
docker-compose logs

# 特定服务日志
docker-compose logs proxy-api
docker-compose logs mongodb
docker-compose logs qdrant

# 实时日志
docker-compose logs -f
```

### 7.2 健康检查

```bash
# API 健康检查
curl http://localhost:8080/health

# MongoDB 健康检查
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Qdrant 健康检查
curl http://localhost:6333/health
```

### 7.3 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看 Docker 磁盘使用
docker system df
```

---

## 8. 故障排除

### 8.1 常见问题

#### 问题 1: 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep 8080

# 修改端口
# 编辑 .env 文件中的 API_PORT
```

#### 问题 2: MongoDB 连接失败

```bash
# 检查 MongoDB 状态
docker-compose logs mongodb

# 检查连接字符串
# 确保 MONGODB_URL 配置正确
```

#### 问题 3: Qdrant 无法启动

```bash
# 检查 Qdrant 日志
docker-compose logs qdrant

# 检查数据卷权限
sudo chown -R 1000:1000 ./data/qdrant
```

### 8.2 重置环境

```bash
# 停止所有服务
docker-compose down

# 删除所有数据
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

---

## 9. 配置参考

### 9.1 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| VERSION | latest | 镜像版本 |
| API_PORT | 8080 | API 服务端口 |
| WEB_PORT | 3000 | Web UI 端口 |
| MONGODB_USER | admin | MongoDB 用户名 |
| MONGODB_PASSWORD | password123 | MongoDB 密码 |
| LOG_LEVEL | INFO | 日志级别 |

### 9.2 端口映射

| 服务 | 容器端口 | 默认映射 |
|------|----------|----------|
| API | 8080 | 8080 |
| Web UI | 3000 | 3000 |
| MongoDB | 27017 | 27017 |
| Qdrant | 6333 | 6333 |

---

## 10. 更新升级

### 10.1 拉取最新镜像

```bash
docker-compose pull
```

### 10.2 更新服务

```bash
# 开发模式
docker-compose up -d

# 生产模式
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 10.3 回滚

```bash
# 回滚到上一个版本
docker-compose down
docker-compose up -d

# 或使用特定版本
docker-compose down
docker-compose pull proxy-api:latest
docker-compose up -d
```

---

## 11. 安全建议

1. **修改默认密码**: 在 `.env` 中修改 MongoDB 密码
2. **启用 SSL**: 在生产环境使用 HTTPS
3. **限制访问**: 使用防火墙限制 IP 访问
4. **定期备份**: 设置自动备份策略
5. **监控日志**: 定期检查安全日志
