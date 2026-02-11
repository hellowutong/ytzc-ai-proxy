"""
虚拟模型管理API
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from api.dependencies import get_config_manager
from core.config import ConfigManager

router = APIRouter()

# Config 中的虚拟模型路径
VIRTUAL_MODELS_CONFIG_KEY = "ai-gateway.virtual_models"


class ModelConfig(BaseModel):
    model: str = ""
    api_key: str = ""
    base_url: str = ""


class KnowledgeConfig(BaseModel):
    enabled: bool = True
    shared: bool = False
    system_default_skill: str = "v1"
    custom_skill: str = "v1"
    use_system_default: bool = True
    use_custom: bool = False


class WebSearchConfig(BaseModel):
    enabled: bool = False
    system_default_skill: str = "v1"
    custom_skill: str = "v1"
    use_system_default: bool = True
    use_custom: bool = False
    targets: List[str] = ["searxng"]


class KeywordConfig(BaseModel):
    """关键词模型切换配置"""
    enabled: bool = False
    small_keywords: List[str] = Field(default_factory=list, max_length=50)
    big_keywords: List[str] = Field(default_factory=list, max_length=50)
    
    @field_validator('small_keywords', 'big_keywords')
    @classmethod
    def validate_keywords(cls, v):
        for keyword in v:
            if len(keyword) > 50:
                raise ValueError(f"关键词长度不能超过50字符: {keyword}")
        return v


class KeywordRule(BaseModel):
    """关键词规则"""
    pattern: str
    target: Literal["small", "big"]


class RoutingKeywordsConfig(BaseModel):
    """路由关键词配置"""
    enable: bool = False
    rules: List[KeywordRule] = Field(default_factory=list)


class RoutingSkillConfig(BaseModel):
    """路由Skill配置"""
    enabled: bool = True
    version: str = "v1"
    custom: dict = Field(default_factory=lambda: {"enabled": False, "version": "v2"})


class RoutingConfig(BaseModel):
    """虚拟模型路由配置（替代全局router）"""
    keywords: RoutingKeywordsConfig = Field(default_factory=RoutingKeywordsConfig)
    skill: RoutingSkillConfig = Field(default_factory=RoutingSkillConfig)


class VirtualModel(BaseModel):
    name: str
    proxy_key: str = ""
    current: Literal["small", "big"] = "small"
    force_current: bool = False
    use: bool = True
    small: ModelConfig = Field(default_factory=ModelConfig)
    big: ModelConfig = Field(default_factory=ModelConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)  # 新增：虚拟模型独立路由配置
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    keyword_switching: KeywordConfig = Field(default_factory=KeywordConfig)


def _get_virtual_models_from_config(config_manager: ConfigManager) -> List[dict]:
    """从config.yml读取虚拟模型配置"""
    virtual_models_dict = config_manager.get(VIRTUAL_MODELS_CONFIG_KEY, {})
    models_list = []
    for name, config in virtual_models_dict.items():
        model_data = dict(config)
        model_data["name"] = name
        models_list.append(model_data)
    return models_list


def _save_virtual_models_to_config(config_manager: ConfigManager, models_list: List[dict]) -> bool:
    """保存虚拟模型配置到config.yml"""
    virtual_models_dict = {}
    for model in models_list:
        model_copy = dict(model)
        name = model_copy.pop("name", None)
        if name:
            virtual_models_dict[name] = model_copy
    
    # 使用set方法保存到config.yml
    return config_manager.set(VIRTUAL_MODELS_CONFIG_KEY, virtual_models_dict)


def _update_model_in_config(config_manager: ConfigManager, old_name: str, new_name: str, model_data: dict) -> bool:
    """更新config.yml中的模型配置（支持重命名）"""
    virtual_models_dict = config_manager.get(VIRTUAL_MODELS_CONFIG_KEY, {})
    
    # 如果名称变更，删除旧配置
    if old_name != new_name and old_name in virtual_models_dict:
        del virtual_models_dict[old_name]
    
    # 添加/更新新配置
    model_copy = dict(model_data)
    model_copy.pop("name", None)  # 移除name字段，因为字典key就是name
    virtual_models_dict[new_name] = model_copy
    
    return config_manager.set(VIRTUAL_MODELS_CONFIG_KEY, virtual_models_dict)


@router.get("/virtual-models")
async def get_virtual_models(config_manager: ConfigManager = Depends(get_config_manager)):
    """获取所有虚拟模型"""
    models = _get_virtual_models_from_config(config_manager)
    return {
        "code": 200,
        "message": "success",
        "data": models
    }


@router.post("/virtual-models")
async def create_virtual_model(model: VirtualModel, config_manager: ConfigManager = Depends(get_config_manager)):
    """创建虚拟模型"""
    import secrets
    
    # 从config.yml读取现有模型
    existing_models = _get_virtual_models_from_config(config_manager)
    
    # 检查名称是否已存在
    for m in existing_models:
        if m["name"] == model.name:
            raise HTTPException(
                status_code=400, 
                detail=f"模型名称 '{model.name}' 已存在"
            )
    
    # Generate proxy key
    model.proxy_key = f"sk-{model.name}-{secrets.token_hex(8)}"
    
    # 添加到模型列表
    existing_models.append(model.dict())
    
    # 保存到config.yml
    if not _save_virtual_models_to_config(config_manager, existing_models):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    return {
        "code": 200,
        "message": "模型创建成功",
        "data": model.dict()
    }


@router.put("/virtual-models/{name}")
async def update_virtual_model(name: str, model_data: dict, config_manager: ConfigManager = Depends(get_config_manager)):
    """更新虚拟模型"""
    new_name = model_data.get("name")
    
    # 从config.yml读取现有模型
    existing_models = _get_virtual_models_from_config(config_manager)
    
    # 检查模型是否存在
    model_index = None
    for i, m in enumerate(existing_models):
        if m["name"] == name:
            model_index = i
            break
    
    if model_index is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 如果名称变更，检查新名称是否已存在
    if new_name and new_name != name:
        for m in existing_models:
            if m["name"] == new_name and m["name"] != name:
                raise HTTPException(
                    status_code=400, 
                    detail=f"模型名称 '{new_name}' 已存在"
                )
    
    # 更新模型数据
    existing_models[model_index].update(model_data)
    
    # 保存到config.yml（处理可能的名称变更）
    target_name = new_name if new_name else name
    if not _update_model_in_config(config_manager, name, target_name, existing_models[model_index]):
        raise HTTPException(status_code=500, detail="保存配置失败")
    
    return {
        "code": 200,
        "message": "模型更新成功",
        "data": existing_models[model_index]
    }


@router.delete("/virtual-models/{name}")
async def delete_virtual_model(name: str, config_manager: ConfigManager = Depends(get_config_manager)):
    """删除虚拟模型"""
    # 从config.yml读取现有模型
    existing_models = _get_virtual_models_from_config(config_manager)
    
    original_len = len(existing_models)
    filtered_models = [m for m in existing_models if m["name"] != name]
    
    if len(filtered_models) < original_len:
        # 保存更新后的配置
        if not _save_virtual_models_to_config(config_manager, filtered_models):
            raise HTTPException(status_code=500, detail="保存配置失败")
        
        return {
            "code": 200,
            "message": "模型删除成功",
            "data": None
        }
    
    raise HTTPException(status_code=404, detail="模型不存在")


@router.post("/virtual-models/{name}/switch")
async def switch_model(name: str, body: dict, config_manager: ConfigManager = Depends(get_config_manager)):
    """切换当前模型"""
    target = body.get("target", "small")
    
    # 从config.yml读取现有模型
    existing_models = _get_virtual_models_from_config(config_manager)
    
    for i, m in enumerate(existing_models):
        if m["name"] == name:
            existing_models[i]["current"] = target
            # 保存到config.yml
            if not _update_model_in_config(config_manager, name, name, existing_models[i]):
                raise HTTPException(status_code=500, detail="保存配置失败")
            return {
                "code": 200,
                "message": f"已切换到{'小模型' if target == 'small' else '大模型'}",
                "data": {"current": target}
            }
    
    raise HTTPException(status_code=404, detail="模型不存在")


@router.post("/models/test-connection")
async def test_model_connection(config: ModelConfig):
    """测试模型连接"""
    import httpx
    
    # 检查必要参数
    if not config.model or not config.base_url:
        return {
            "code": 400,
            "message": "模型名称和Base URL不能为空"
        }
    
    try:
        # 尝试调用模型API
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
            
            # 发送一个简单的请求测试连接
            response = await client.post(
                f"{config.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": config.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
            )
            
            if response.status_code == 200:
                return {
                    "code": 200,
                    "message": "连接成功"
                }
            else:
                return {
                    "code": response.status_code,
                    "message": f"连接失败: {response.text}"
                }
                
    except httpx.TimeoutException:
        return {
            "code": 408,
            "message": "连接超时"
        }
    except httpx.ConnectError:
        return {
            "code": 503,
            "message": "无法连接到服务器"
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"连接错误: {str(e)}"
        }
