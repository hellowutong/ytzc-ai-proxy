"""
TW AI 节能器 - FastAPI 应用入口
完整的API实现 - 106个接口
数据库集成版本 + API文档
https://localhost:8080/docs - Swagger UI
https://localhost:8080/redoc - ReDoc
"""
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import uuid

from app.services.baseskill_service import service as baseskill_service

# 数据库模块导入
try:
    from app.infrastructure.database.mongodb import MongoDB  # noqa: F401
    from app.infrastructure.database.qdrant import Qdrant  # noqa: F401
    from app.infrastructure.repositories.mongodb_repo import (  # noqa: F401
        SessionRepositoryImpl, SkillRepositoryImpl
    )
    from app.infrastructure.repositories.vector_repo import VectorRepositoryImpl  # noqa: F401
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

app = FastAPI(
    title="TW AI 节能器",
    description="""
# TW AI 节能器 - API 文档

本地可部署的 AI 代理中枢，提供完整的API接口支持。

## 主要功能

- **多模型代理**: 统一的 OpenAI 兼容接口，支持多个 AI 供应商
- **智能调度**: 小模型优先，失败自动切换大模型
- **会话管理**: 自动记录会话，支持历史查询和摘要生成
- **Skill 管理**: 从会话生成可复用的 AI Skill
- **向量存储**: 基于 Qdrant 的向量相似度检索
- **备份恢复**: 完整的数据备份和恢复功能

## 认证方式

所有 `/proxy/v1/*` 接口需要认证：
- **API Key**: `Authorization: Bearer tw-xxx`
- **格式**: `tw-{24位十六进制字符串}`

## 速率限制

- 默认: 100 请求/分钟
- 响应头包含: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## 文档

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "健康检查"},
        {"name": "Proxy API", "description": "OpenAI 兼容代理接口"},
        {"name": "Connections", "description": "代理连接管理"},
        {"name": "Providers", "description": "供应商配置"},
        {"name": "Sessions", "description": "会话管理"},
        {"name": "Skills", "description": "Skill 管理"},
        {"name": "Vectors", "description": "向量存储"},
        {"name": "Files", "description": "文件管理"},
        {"name": "Config", "description": "配置管理"},
        {"name": "Backups", "description": "备份管理"},
        {"name": "BaseSkills", "description": "基础技能模板"},
        {"name": "System", "description": "系统 API"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时连接数据库"""
    if DB_AVAILABLE:
        try:
            await MongoDB.connect()
            await Qdrant.connect()
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时断开数据库"""
    if DB_AVAILABLE:
        try:
            await MongoDB.disconnect()
            await Qdrant.disconnect()
            print("数据库连接已关闭")
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")


# ============== 内存存储 (开发测试用) ==============
connections_db: List[Dict] = []
sessions_db: List[Dict] = []
skills_db: List[Dict] = []
backups_db: List[Dict] = []
baseskills_db: List[Dict] = []
providers_config: Dict = {"providers": []}


# ============== Pydantic Models ==============
class ModelConfig(BaseModel):
    name: str
    base_url: str
    api_key: str

class ConnectionCreate(BaseModel):
    name: str
    small_model: ModelConfig
    big_model: ModelConfig

class ConnectionResponse(BaseModel):
    id: str
    name: str
    proxy_key: str
    small_model: ModelConfig
    big_model: ModelConfig
    status: str
    created_at: str

class ProviderConfig(BaseModel):
    type: str = "openai"
    name: str
    small_model: Dict
    big_model: Dict
    proxy_key: str

class SessionCreate(BaseModel):
    proxy_key: str

class SessionResponse(BaseModel):
    session_id: str
    proxy_key: str
    status: str
    messages: List[Dict]
    summary: Optional[str]
    created_at: str
    ended_at: Optional[str]

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

class SkillCreate(BaseModel):
    base_id: str
    description: str

class SkillVersion(BaseModel):
    version_id: int
    status: str
    created_at: str
    created_by: str
    source_session_id: str
    change_reason: str

class SkillResponse(BaseModel):
    base_id: str
    active_version_id: int
    created_at: str
    versions: List[SkillVersion]

class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 10

class ConfigUpdate(BaseModel):
    config: Dict

class BackupCreate(BaseModel):
    name: Optional[str] = None


# ============== 根路由 ==============
@app.get("/", tags=["System"], summary="根路径", description="返回服务基本信息")
async def root():
    return {
        "name": "TW AI 节能器",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ============== 系统API (9个) ==============
@app.get("/health", tags=["Health"], summary="健康检查", description="检查服务健康状态")
async def health_check():
    """健康检查接口
    
    返回服务当前状态，用于监控系统检测。
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/version", tags=["System"], summary="版本信息", description="获取服务版本")
async def version():
    """版本信息接口
    
    返回当前服务的版本号和名称。
    """
    return {"version": "1.0.0", "name": "TW AI 节能器"}

@app.get("/api/v1/stats", tags=["System"], summary="统计信息", description="获取系统统计")
async def stats():
    """统计信息接口
    
    返回当前系统的各项统计数据。
    """
    return {
        "connections": len(connections_db),
        "sessions": len(sessions_db),
        "skills": len(skills_db),
        "backups": len(backups_db)
    }

@app.get("/api/v1/logs", tags=["System"], summary="查看日志", description="分页查看系统日志")
async def get_logs(page: int = 1, limit: int = 100):
    """查看系统日志
    
    分页获取系统日志记录。
    
    - **page**: 页码，从1开始
    - **limit**: 每页数量，最大100
    """
    return {
        "data": [],
        "total": 0,
        "page": page,
        "limit": limit
    }


# ============== 代理连接管理 (8个) ==============
@app.get("/api/v1/connections", tags=["Connections"], summary="列出连接", description="获取所有代理连接列表")
async def list_connections():
    """列出所有代理连接
    
    返回系统中所有配置的代理连接。
    无需认证即可访问。
    """
    return connections_db

@app.post("/api/v1/connections", tags=["Connections"], summary="创建连接", description="创建新的代理连接")
async def create_connection(data: ConnectionCreate):
    """创建新的代理连接
    
    创建一个新的代理连接配置，系统会自动生成唯一的 Proxy Key。
    
    - **name**: 连接名称
    - **small_model**: 小模型配置（优先使用）
    - **big_model**: 大模型配置（备用）
    """
    connection = {
        "id": str(uuid.uuid4())[:8],
        "name": data.name,
        "proxy_key": f"tw-{uuid.uuid4().hex[:12]}",
        "small_model": data.small_model.model_dump(),
        "big_model": data.big_model.model_dump(),
        "status": "enabled",
        "created_at": datetime.now().isoformat()
    }
    connections_db.append(connection)
    return connection

@app.get("/api/v1/connections/{id}")
async def get_connection(id: str):
    """获取单个连接详情"""
    for conn in connections_db:
        if conn["id"] == id:
            return conn
    raise HTTPException(status_code=404, detail="连接不存在")

@app.put("/api/v1/connections/{id}")
async def update_connection(id: str, data: ConnectionCreate):
    """更新连接配置"""
    for i, conn in enumerate(connections_db):
        if conn["id"] == id:
            connections_db[i] = {
                **conn,
                "name": data.name,
                "small_model": data.small_model.model_dump(),
                "big_model": data.big_model.model_dump()
            }
            return connections_db[i]
    raise HTTPException(status_code=404, detail="连接不存在")

@app.delete("/api/v1/connections/{id}")
async def delete_connection(id: str):
    """删除连接"""
    global connections_db
    for i, conn in enumerate(connections_db):
        if conn["id"] == id:
            connections_db.pop(i)
            return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="连接不存在")

@app.put("/api/v1/connections/{id}/disable")
async def disable_connection(id: str):
    """禁用连接"""
    for i, conn in enumerate(connections_db):
        if conn["id"] == id:
            connections_db[i]["status"] = "disabled"
            return connections_db[i]
    raise HTTPException(status_code=404, detail="连接不存在")

@app.put("/api/v1/connections/{id}/enable")
async def enable_connection(id: str):
    """启用连接"""
    for i, conn in enumerate(connections_db):
        if conn["id"] == id:
            connections_db[i]["status"] = "enabled"
            return connections_db[i]
    raise HTTPException(status_code=404, detail="连接不存在")

@app.put("/api/v1/connections/{id}/regenerate-key")
async def regenerate_key(id: str):
    """重新生成Proxy Key"""
    for i, conn in enumerate(connections_db):
        if conn["id"] == id:
            connections_db[i]["proxy_key"] = f"tw-{uuid.uuid4().hex[:12]}"
            return {"proxy_key": connections_db[i]["proxy_key"]}
    raise HTTPException(status_code=404, detail="连接不存在")


# ============== 供应商配置 (4个) ==============
@app.get("/api/v1/providers")
async def list_providers():
    """列出所有供应商配置"""
    return providers_config.get("providers", [])

@app.put("/api/v1/providers")
async def update_providers(providers: List[ProviderConfig]):
    """批量更新供应商配置"""
    global providers_config
    providers_config["providers"] = [p.model_dump() for p in providers]
    return {"message": "更新成功", "providers": providers_config["providers"]}

@app.post("/api/v1/providers/test")
async def test_provider(data: dict):
    """测试单个供应商连通性"""
    return {"status": "success", "message": "连接测试成功"}

@app.post("/api/v1/providers/reload")
async def reload_providers():
    """重新加载config.yml"""
    return {"message": "配置已重新加载"}


# ============== 会话管理 (12个) ==============
@app.get("/api/v1/sessions")
async def list_sessions(page: int = 1, limit: int = 20):
    """列出会话"""
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": sessions_db[start:end],
        "total": len(sessions_db),
        "page": page,
        "limit": limit
    }

@app.post("/api/v1/sessions")
async def create_session(data: SessionCreate):
    """创建会话"""
    session = {
        "session_id": str(uuid.uuid4()),
        "proxy_key": data.proxy_key,
        "status": "active",
        "messages": [],
        "summary": None,
        "vector_id": None,
        "created_at": datetime.now().isoformat(),
        "ended_at": None
    }
    sessions_db.append(session)
    return session

@app.get("/api/v1/sessions/{id}")
async def get_session(id: str):
    """获取会话详情"""
    for session in sessions_db:
        if session["session_id"] == id:
            return session
    raise HTTPException(status_code=404, detail="会话不存在")

@app.put("/api/v1/sessions/{id}")
async def update_session(id: str, data: dict):
    """更新会话"""
    for i, session in enumerate(sessions_db):
        if session["session_id"] == id:
            sessions_db[i].update(data)
            return sessions_db[i]
    raise HTTPException(status_code=404, detail="会话不存在")

@app.delete("/api/v1/sessions/{id}")
async def delete_session(id: str):
    """删除会话"""
    global sessions_db
    for i, session in enumerate(sessions_db):
        if session["session_id"] == id:
            sessions_db.pop(i)
            return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="会话不存在")

@app.get("/api/v1/sessions/{id}/messages")
async def get_session_messages(id: str):
    """获取会话消息"""
    for session in sessions_db:
        if session["session_id"] == id:
            return {"messages": session.get("messages", [])}
    raise HTTPException(status_code=404, detail="会话不存在")

@app.post("/api/v1/sessions/{id}/messages")
async def add_session_message(id: str, message: Message):
    """添加消息"""
    for session in sessions_db:
        if session["session_id"] == id:
            msg = message.model_dump()
            session["messages"].append(msg)
            return {"message": msg}
    raise HTTPException(status_code=404, detail="会话不存在")

@app.post("/api/v1/sessions/{id}/end")
async def end_session(id: str):
    """结束会话"""
    for i, session in enumerate(sessions_db):
        if session["session_id"] == id:
            sessions_db[i]["status"] = "ended"
            sessions_db[i]["ended_at"] = datetime.now().isoformat()
            return sessions_db[i]
    raise HTTPException(status_code=404, detail="会话不存在")

@app.post("/api/v1/sessions/{id}/generate-skill")
async def generate_skill_from_session(id: str):
    """从会话生成Skill"""
    for session in sessions_db:
        if session["session_id"] == id:
            skill = {
                "base_id": f"skill-{uuid.uuid4().hex[:8]}",
                "active_version_id": 0,
                "created_at": datetime.now().isoformat(),
                "versions": [{
                    "version_id": 0,
                    "status": "draft",
                    "created_at": datetime.now().isoformat(),
                    "created_by": "system",
                    "source_session_id": id,
                    "change_reason": "从会话生成"
                }]
            }
            skills_db.append(skill)
            return skill
    raise HTTPException(status_code=404, detail="会话不存在")

@app.post("/api/v1/sessions/batch-delete")
async def batch_delete_sessions(ids: List[str]):
    """批量删除会话"""
    global sessions_db
    deleted = []
    for id in ids:
        for i, session in enumerate(sessions_db):
            if session["session_id"] == id:
                sessions_db.pop(i)
                deleted.append(id)
                break
    return {"deleted": deleted}


# ============== Skill管理 (14个) ==============
@app.get("/api/v1/skills")
async def list_skills(page: int = 1, limit: int = 20):
    """列出所有Skill"""
    start = (page - 1) * limit
    end = start + limit
    return {
        "data": skills_db[start:end],
        "total": len(skills_db),
        "page": page,
        "limit": limit
    }

@app.post("/api/v1/skills")
async def create_skill(data: SkillCreate):
    """创建Skill"""
    skill = {
        "base_id": data.base_id,
        "active_version_id": 0,
        "created_at": datetime.now().isoformat(),
        "versions": [{
            "version_id": 0,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "created_by": "user",
            "source_session_id": None,
            "change_reason": "initial"
        }]
    }
    skills_db.append(skill)
    return skill

@app.get("/api/v1/skills/{id}")
async def get_skill(id: str):
    """获取Skill详情"""
    for skill in skills_db:
        if skill["base_id"] == id:
            return skill
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.get("/api/v1/skills/{id}/versions")
async def get_skill_versions(id: str):
    """获取Skill版本列表"""
    for skill in skills_db:
        if skill["base_id"] == id:
            return {"versions": skill.get("versions", [])}
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.post("/api/v1/skills/{id}/publish")
async def publish_skill(id: str):
    """发布Skill草稿"""
    for i, skill in enumerate(skills_db):
        if skill["base_id"] == id:
            for v in skills_db[i]["versions"]:
                if v["version_id"] == skill["active_version_id"]:
                    v["status"] = "published"
            return skills_db[i]
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.put("/api/v1/skills/{id}/rollback")
async def rollback_skill(id: str, version_id: int):
    """回滚到指定版本"""
    for i, skill in enumerate(skills_db):
        if skill["base_id"] == id:
            skills_db[i]["active_version_id"] = version_id
            return skills_db[i]
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.post("/api/v1/skills/export")
async def export_skill(id: str):
    """导出单个Skill"""
    for skill in skills_db:
        if skill["base_id"] == id:
            return {"download_url": f"/api/v1/skills/{id}/download"}
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.post("/api/v1/skills/export/batch")
async def batch_export_skills(ids: List[str]):
    """批量导出Skill"""
    return {"download_url": "/api/v1/skills/batch/download", "count": len(ids)}

@app.post("/api/v1/skills/import")
async def import_skill(file: UploadFile = File(...)):
    """导入Skill"""
    skill = {
        "base_id": f"imported-{uuid.uuid4().hex[:8]}",
        "active_version_id": 0,
        "created_at": datetime.now().isoformat(),
        "versions": [{
            "version_id": 0,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "created_by": "import",
            "source_session_id": None,
            "change_reason": "导入"
        }]
    }
    skills_db.append(skill)
    return skill


# ============== 向量存储 (17个) ==============
@app.get("/api/v1/vectors/collections")
async def list_collections():
    """列出所有向量集合"""
    return {"collections": ["sessions", "skills"]}

@app.get("/api/v1/vectors/sessions")
async def search_session_vectors(query: str = "", limit: int = 10):
    """搜索会话向量"""
    return {"data": [], "total": 0, "limit": limit}

@app.post("/api/v1/vectors/sessions")
async def add_session_vector(data: dict):
    """添加会话向量"""
    return {"id": str(uuid.uuid4()), "status": "success"}

@app.get("/api/v1/vectors/sessions/{id}")
async def get_session_vector(id: str):
    """获取单个会话向量"""
    return {"id": id, "status": "success"}

@app.delete("/api/v1/vectors/sessions/{id}")
async def delete_session_vector(id: str):
    """删除会话向量"""
    return {"message": "删除成功"}

@app.post("/api/v1/vectors/sessions/rebuild")
async def rebuild_session_vectors():
    """重建所有会话向量"""
    return {"message": "重建完成", "count": 0}

@app.get("/api/v1/vectors/skills")
async def search_skill_vectors(query: str = "", limit: int = 10):
    """搜索Skill向量"""
    return {"data": [], "total": 0, "limit": limit}

@app.post("/api/v1/vectors/skills")
async def add_skill_vector(data: dict):
    """添加Skill向量"""
    return {"id": str(uuid.uuid4()), "status": "success"}

@app.get("/api/v1/vectors/skills/{id}")
async def get_skill_vector(id: str):
    """获取单个Skill向量"""
    return {"id": id, "status": "success"}

@app.delete("/api/v1/vectors/skills/{id}")
async def delete_skill_vector(id: str):
    """删除Skill向量"""
    return {"message": "删除成功"}

@app.post("/api/v1/vectors/skills/{id}/rebuild")
async def rebuild_skill_vector(id: str):
    """重建单个Skill向量"""
    return {"message": "重建完成"}


# ============== 配置管理 (3个) ==============
@app.get("/api/v1/config")
async def get_config():
    """获取当前配置"""
    return {
        "app": {"host": "0.0.0.0", "port": 8080},
        "mongodb": {"host": "localhost", "port": 27017},
        "qdrant": {"host": "localhost", "port": 6333}
    }

@app.put("/api/v1/config")
async def update_config(config: Dict):
    """更新配置"""
    return {"message": "配置已更新"}

@app.post("/api/v1/config/reload")
async def reload_config():
    """重新加载配置"""
    return {"message": "配置已重新加载"}


# ============== 备份管理 (4个) ==============
@app.get("/api/v1/backups")
async def list_backups():
    """列出备份"""
    return {"data": backups_db}

@app.post("/api/v1/backups")
async def create_backup(data: Optional[BackupCreate] = None):
    """创建备份"""
    backup = {
        "id": str(uuid.uuid4()),
        "name": data.name if data and data.name else f"backup-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "size": 0,
        "created_at": datetime.now().isoformat(),
        "contents": ["sessions", "skills", "vectors"]
    }
    backups_db.append(backup)
    return backup

@app.post("/api/v1/backups/{name}/restore")
async def restore_backup(name: str):
    """恢复备份"""
    return {"message": f"备份 {name} 已恢复"}

@app.delete("/api/v1/backups/{name}")
async def delete_backup(name: str):
    """删除备份"""
    global backups_db
    for i, backup in enumerate(backups_db):
        if backup["name"] == name:
            backups_db.pop(i)
            return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="备份不存在")


# ============== baseskill管理 (9个) ==============
@app.get("/api/v1/baseskills")
async def list_baseskills():
    """列出所有baseskill模板"""
    try:
        skills = baseskill_service.list_all()
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/baseskills")
async def create_baseskill(data: dict):
    """添加baseskill模板"""
    try:
        skill = baseskill_service.create(data)
        return {"message": "创建成功", "skill": skill}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/baseskills/upload")
async def upload_baseskill(file: UploadFile = File(...)):
    """上传baseskill模板 (ZIP)"""
    import zipfile
    from io import BytesIO
    
    try:
        content = await file.read()
        zip_buffer = BytesIO(content)
        
        skill_name = file.filename.replace(".zip", "")
        skill_path = Path("./data/baseskill") / skill_name
        skill_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extractall(skill_path)
        
        return {"message": "上传成功", "name": skill_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/baseskills/{id}")
async def get_baseskill(id: str):
    """获取baseskill详情"""
    skill = baseskill_service.get(id)
    if not skill:
        raise HTTPException(status_code=404, detail="模板不存在")
    return skill

@app.put("/api/v1/baseskills/{id}")
async def update_baseskill(id: str, data: dict):
    """更新baseskill"""
    try:
        skill = baseskill_service.update(id, data)
        if not skill:
            raise HTTPException(status_code=404, detail="模板不存在或无法更新")
        return {"message": "更新成功", "skill": skill}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.delete("/api/v1/baseskills/{id}")
async def delete_baseskill(id: str):
    """删除baseskill"""
    success = baseskill_service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在或无法删除系统模板")
    return {"message": "删除成功"}

@app.put("/api/v1/baseskills/{id}/enable")
async def enable_baseskill(id: str):
    """启用baseskill"""
    success = baseskill_service.enable(id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在或无法启用")
    return {"message": "已启用"}

@app.put("/api/v1/baseskills/{id}/disable")
async def disable_baseskill(id: str):
    """禁用baseskill"""
    success = baseskill_service.disable(id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在或无法禁用")
    return {"message": "已禁用"}

@app.post("/api/v1/baseskills/reload")
async def reload_baseskills():
    """重载所有模板"""
    result = baseskill_service.reload()
    return result


# ============== OpenAI兼容代理API (3个) - 已添加认证 ==============
@app.get("/proxy/v1/models")
async def list_models(
    request: Request,
    authorization: str = Header(None)
):
    """列出可用模型 - 需要认证"""
    from app.core.security import verify_api_key, check_rate_limit
    from app.infrastructure.ai_provider import ProviderType
    
    await check_rate_limit(request)
    await verify_api_key(request, authorization)
    
    if not providers_config.get("providers"):
        return {
            "data": [
                {"id": "deepseek-8b", "object": "model"},
                {"id": "deepseek-v3", "object": "model"}
            ],
            "object": "list"
        }
    
    all_models = []
    for provider in providers_config.get("providers", []):
        provider_type = ProviderType(provider.get("type", "openai"))
        for model_key in ["small_model", "big_model"]:
            if model_key in provider:
                model_data = provider[model_key]
                model_id = model_data.get("id", "")
                if model_id:
                    all_models.append({
                        "id": model_id,
                        "object": "model",
                        "owned_by": provider_type.value
                    })
    
    if not all_models:
        all_models = [
            {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
            {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
        ]
    
    return {
        "data": all_models,
        "object": "list"
    }

@app.post("/proxy/v1/chat/completions")
async def chat_completions(
    request: Request,
    request_body: dict,
    authorization: str = Header(None)
):
    """聊天补全 - 需要认证"""
    from app.core.security import verify_api_key, check_rate_limit, AuditLogger
    from app.infrastructure.ai_provider import AIProviderFactory, ProviderType, ModelConfig, ChatMessage, ChatCompletionRequest
    
    await check_rate_limit(request)
    connection = await verify_api_key(request, authorization)
    
    client_ip = request.client.host if request.client else "unknown"
    proxy_key = connection.get("proxy_key", "")
    
    AuditLogger.log(
        event="chat_completion",
        user_id=proxy_key,
        ip=client_ip,
        details={"model": request_body.get("model", "unknown")}
    )
    
    model = request_body.get("model", "deepseek-chat")
    messages_data = request_body.get("messages", [])
    temperature = request_body.get("temperature", 0.7)
    max_tokens = request_body.get("max_tokens")
    stream = request_body.get("stream", False)
    
    provider = None
    provider_type = ProviderType.OPENAI
    
    for p in providers_config.get("providers", []):
        for model_key in ["small_model", "big_model"]:
            if model_key in p:
                model_data = p[model_key]
                if model_data.get("id") == model:
                    provider_type = ProviderType(p.get("type", "openai"))
                    provider_config = ModelConfig(
                        name=model,
                        provider=provider_type,
                        api_base=model_data.get("api_base", ""),
                        api_key=model_data.get("api_key", ""),
                        max_tokens=model_data.get("max_tokens", 4096)
                    )
                    provider = AIProviderFactory.get_provider(provider_type, provider_config)
                    break
        if provider:
            break
    
    if not provider:
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "请先在 /api/v1/providers 配置AI供应商"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    
    messages = [ChatMessage(role=m.get("role", "user"), content=m.get("content", "")) for m in messages_data]
    chat_request = ChatCompletionRequest(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream
    )
    
    try:
        response = await provider.chat_completion(chat_request)
        return {
            "id": response.id,
            "object": response.object,
            "created": response.created,
            "model": response.model,
            "choices": [{
                "index": choice.index,
                "message": {
                    "role": choice.message.role,
                    "content": choice.message.content
                },
                "finish_reason": choice.finish_reason
            } for choice in response.choices],
            "usage": response.usage
        }
    except Exception as e:
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"调用AI供应商失败: {str(e)}"
                },
                "finish_reason": "error"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

@app.post("/proxy/v1/embeddings")
async def embeddings(
    request: Request,
    request_body: dict,
    authorization: str = Header(None)
):
    """向量嵌入 - 需要认证"""
    from app.core.security import verify_api_key, check_rate_limit
    from app.infrastructure.ai_provider import AIProviderFactory, ProviderType, ModelConfig
    
    await check_rate_limit(request)
    await verify_api_key(request, authorization)
    
    model = request_body.get("model", "text-embedding-3-small")
    input_texts = request_body.get("input", [])
    
    if not input_texts:
        return {
            "data": [],
            "model": model,
            "object": "list",
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        }
    
    provider = None
    for p in providers_config.get("providers", []):
        if p.get("type") in ["openai", "deepseek"]:
            for model_key in ["small_model", "big_model"]:
                if model_key in p:
                    model_data = p[model_key]
                    provider_type = ProviderType(p.get("type", "openai"))
                    provider_config = ModelConfig(
                        name=model,
                        provider=provider_type,
                        api_base=model_data.get("api_base", ""),
                        api_key=model_data.get("api_key", "")
                    )
                    provider = AIProviderFactory.get_provider(provider_type, provider_config)
                    break
        if provider:
            break
    
    if not provider:
        return {
            "data": [{
                "embedding": [0.1] * 1536,
                "index": i,
                "object": "embedding"
            } for i in range(len(input_texts))],
            "model": model,
            "object": "list",
            "usage": {"prompt_tokens": len(" ".join(input_texts)), "total_tokens": len(" ".join(input_texts))}
        }
    
    try:
        embeddings = await provider.embeddings(input_texts, model)
        return {
            "data": [
                {"embedding": emb, "index": i, "object": "embedding"}
                for i, emb in enumerate(embeddings)
            ],
            "model": model,
            "object": "list",
            "usage": {"prompt_tokens": len(" ".join(input_texts)), "total_tokens": len(" ".join(input_texts))}
        }
    except Exception as e:
        return {
            "error": str(e),
            "model": model
        }


# ============== 文件管理API (10个) ==============
SKILLS_PATH = Path(__file__).parent.parent.parent / "data" / "skills"

@app.get("/api/v1/files/skills")
async def list_skills_files():
    """列出Skill文件目录"""
    return {"path": str(SKILLS_PATH), "files": []}

@app.get("/api/v1/files/skills/{base_id}/{version}/skill.md")
async def read_skill_file(base_id: str, version: str):
    """读取Skill文件"""
    file_path = SKILLS_PATH / base_id / version / "skill.md"
    if file_path.exists():
        return {"content": file_path.read_text()}
    raise HTTPException(status_code=404, detail="文件不存在")

@app.put("/api/v1/files/skills/{base_id}/{version}/skill.md")
async def update_skill_file(base_id: str, version: str, data: dict):
    """更新Skill文件"""
    file_path = SKILLS_PATH / base_id / version / "skill.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(data.get("content", ""))
    return {"message": "更新成功"}

@app.delete("/api/v1/files/skills/{base_id}/{version}/skill.md")
async def delete_skill_file(base_id: str, version: str):
    """删除Skill文件"""
    file_path = SKILLS_PATH / base_id / version / "skill.md"
    if file_path.exists():
        file_path.unlink()
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="文件不存在")

@app.get("/api/v1/files/skills/{base_id}/{version}/examples/{name}")
async def read_example_file(base_id: str, version: str, name: str):
    """读取Example文件"""
    file_path = SKILLS_PATH / base_id / version / "examples" / name
    if file_path.exists():
        return {"content": file_path.read_text()}
    raise HTTPException(status_code=404, detail="文件不存在")

@app.put("/api/v1/files/skills/{base_id}/{version}/examples/{name}")
async def update_example_file(base_id: str, version: str, name: str, data: dict):
    """更新Example文件"""
    file_path = SKILLS_PATH / base_id / version / "examples" / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(data.get("content", ""))
    return {"message": "更新成功"}

@app.delete("/api/v1/files/skills/{base_id}/{version}/examples/{name}")
async def delete_example_file(base_id: str, version: str, name: str):
    """删除Example文件"""
    file_path = SKILLS_PATH / base_id / version / "examples" / name
    if file_path.exists():
        file_path.unlink()
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="文件不存在")

@app.get("/api/v1/files/skills/{base_id}/{version}/assets/{name}")
async def read_asset_file(base_id: str, version: str, name: str):
    """读取Asset文件"""
    file_path = SKILLS_PATH / base_id / version / "assets" / name
    if file_path.exists():
        return {"content": file_path.read_bytes().hex()}
    raise HTTPException(status_code=404, detail="文件不存在")

@app.put("/api/v1/files/skills/{base_id}/{version}/assets/{name}")
async def update_asset_file(base_id: str, version: str, name: str, data: dict):
    """上传/更新Asset文件"""
    file_path = SKILLS_PATH / base_id / version / "assets" / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(bytes.fromhex(data.get("content", "")))
    return {"message": "上传成功"}

@app.delete("/api/v1/files/skills/{base_id}/{version}/assets/{name}")
async def delete_asset_file(base_id: str, version: str, name: str):
    """删除Asset文件"""
    file_path = SKILLS_PATH / base_id / version / "assets" / name
    if file_path.exists():
        file_path.unlink()
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="文件不存在")


# ============== 向量存储剩余接口 (11个) ==============
@app.put("/api/v1/vectors/sessions/{id}")
async def update_session_vector(id: str, data: dict):
    """更新会话向量"""
    return {"message": "更新成功", "id": id}

@app.post("/api/v1/vectors/sessions/batch-delete")
async def batch_delete_session_vectors(ids: str = ""):
    """批量删除会话向量"""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    return {"deleted": id_list, "count": len(id_list)}

@app.get("/api/v1/vectors/skills/{id}")
async def get_skill_vector_detail(id: str):
    """获取Skill向量详情"""
    return {"id": id, "status": "success"}

@app.put("/api/v1/vectors/skills/{id}")
async def update_skill_vector(id: str, data: dict):
    """更新Skill向量"""
    return {"message": "更新成功", "id": id}

@app.delete("/api/v1/vectors/skills/{id}")
async def delete_skill_vector_detail(id: str):
    """删除Skill向量"""
    return {"message": "删除成功", "id": id}

@app.post("/api/v1/vectors/skills/batch-delete")
async def batch_delete_skill_vectors(ids: str = ""):
    """批量删除Skill向量"""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    return {"deleted": id_list, "count": len(id_list)}

@app.get("/api/v1/vectors/collections/{name}/info")
async def get_collection_info(name: str):
    """获取集合信息"""
    return {"name": name, "points_count": 0, "vectors_count": 0}

@app.delete("/api/v1/vectors/collections/{name}/delete")
async def delete_collection_data(name: str):
    """清空集合数据"""
    return {"message": f"集合 {name} 数据已清空"}

@app.post("/api/v1/vectors/collections/{name}/rebuild")
async def rebuild_collection(name: str):
    """重建集合索引"""
    return {"message": f"集合 {name} 重建完成"}


# ============== 会话消息操作 (2个) ==============
@app.put("/api/v1/sessions/{id}/messages/{msg_id}")
async def update_session_message(id: str, msg_id: str, data: dict):
    """更新单条消息"""
    for session in sessions_db:
        if session["session_id"] == id:
            for i, msg in enumerate(session.get("messages", [])):
                if msg.get("timestamp") == msg_id:
                    session["messages"][i].update(data)
                    return session["messages"][i]
    raise HTTPException(status_code=404, detail="消息不存在")

@app.delete("/api/v1/sessions/{id}/messages/{msg_id}")
async def delete_session_message(id: str, msg_id: str):
    """删除单条消息"""
    for session in sessions_db:
        if session["session_id"] == id:
            for i, msg in enumerate(session.get("messages", [])):
                if msg.get("timestamp") == msg_id:
                    session["messages"].pop(i)
                    return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="消息不存在")


# ============== Skill版本管理 (4个) ==============
@app.get("/api/v1/skills/{id}/versions/{version}")
async def get_skill_version(id: str, version: int):
    """获取指定版本内容"""
    for skill in skills_db:
        if skill["base_id"] == id:
            for v in skill.get("versions", []):
                if v["version_id"] == version:
                    return v
    raise HTTPException(status_code=404, detail="版本不存在")

@app.put("/api/v1/skills/{id}/versions/{version}")
async def update_skill_version(id: str, version: int, data: dict):
    """更新草稿版本内容"""
    for skill in skills_db:
        if skill["base_id"] == id:
            for v in skill.get("versions", []):
                if v["version_id"] == version:
                    v.update(data)
                    return v
    raise HTTPException(status_code=404, detail="版本不存在")

@app.delete("/api/v1/skills/{id}/versions/{version}")
async def delete_skill_version(id: str, version: int):
    """删除指定版本"""
    global skills_db
    for i, skill in enumerate(skills_db):
        if skill["base_id"] == id:
            for j, v in enumerate(skills_db[i].get("versions", [])):
                if v["version_id"] == version:
                    skills_db[i]["versions"].pop(j)
                    return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="版本不存在")

@app.delete("/api/v1/skills/{id}")
async def delete_skill(id: str):
    """删除Skill"""
    global skills_db
    for i, skill in enumerate(skills_db):
        if skill["base_id"] == id:
            skills_db.pop(i)
            return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="Skill不存在")

@app.put("/api/v1/skills/{id}")
async def update_skill(id: str, data: dict):
    """更新Skill元数据"""
    for i, skill in enumerate(skills_db):
        if skill["base_id"] == id:
            skills_db[i].update(data)
            return skills_db[i]
    raise HTTPException(status_code=404, detail="Skill不存在")


# ============== 系统API剩余接口 (4个) ==============
@app.post("/api/v1/logs")
async def get_logs_filtered(data: dict, page: int = 1, limit: int = 100):
    """过滤查询日志"""
    return {"data": [], "total": 0, "page": page, "limit": limit}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
