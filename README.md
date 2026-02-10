# AI网关系统

企业级AI网关系统，提供虚拟模型代理、模型路由、知识管理等功能。

## 快速开始

### 1. 启动基础设施

```bash
cd docker
docker-compose up -d
```

这将启动：
- MongoDB (27017)
- Redis (6379)
- Qdrant (6333)
- SearXNG (8080)
- LibreX (8081)
- 4get (8082)

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端服务

```bash
python main.py
```

或使用uvicorn：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发文档

- [AGENTS.md](AGENTS.md) - 开发指南
- [docs/backend_design.md](docs/backend_design.md) - 后端设计文档
- [docs/frontend_design.md](docs/frontend_design.md) - 前端设计文档
- [docs/api_design.md](docs/api_design.md) - API设计文档

## 项目结构

```
ytzc-ai-proxy/
├── backend/              # FastAPI后端
├── frontend/             # Vue3前端
├── docker/               # Docker配置
├── docs/                 # 文档
├── test/                 # 测试
└── scripts/              # 脚本
```

## 技术栈

- **后端**: Python 3.11 + FastAPI
- **前端**: Vue 3 + Element Plus
- **数据库**: MongoDB + Redis + Qdrant
- **搜索**: SearXNG + LibreX + 4get
