"""
Config API endpoints for read-only configuration viewing.

Provides endpoints for:
- Viewing current configuration tree
- Getting specific config sections
- Config metadata and template information
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from core.config_manager import get_config_manager
from models.base import ResponseBase

router = APIRouter(prefix="/config", tags=["config"])


class ConfigNodeResponse(BaseModel):
    """Configuration node response."""
    key: str
    path: str
    value: Any
    type: str
    children: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    editable: bool = False
    modifiable: bool = False


class ConfigTreeResponse(BaseModel):
    """Configuration tree response."""
    success: bool = True
    message: str = ""
    tree_data: Dict[str, Any] = Field(default_factory=dict, alias="data")

    model_config = ConfigDict(populate_by_name=True)


@router.get("", response_model=ConfigTreeResponse)
async def get_config_tree():
    """
    Get complete configuration tree.
    
    Returns the full configuration as a tree structure with metadata.
    """
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        def build_tree(key: str, value: Any, path: str = "") -> Dict[str, Any]:
            """Build tree node recursively."""
            current_path = f"{path}.{key}" if path else key

            node: Dict[str, Any] = {
                "key": key,
                "path": current_path,
                "type": type(value).__name__,
            }

            if isinstance(value, dict):
                node["value"] = None
                node["children"] = [
                    build_tree(k, v, current_path)
                    for k, v in value.items()
                ]
                # Only virtual_models allows full CRUD
                node["modifiable"] = key == "virtual_models"
            else:
                node["value"] = value
                node["children"] = None
                # Values can be edited for all nodes
                node["modifiable"] = True

            # All config is editable via config.yml
            node["editable"] = True

            return node
        
        # Build tree from root
        tree = {
            "key": "root",
            "path": "",
            "type": "dict",
            "children": [build_tree(k, v) for k, v in config.items()],
            "modifiable": False,
            "editable": True
        }
        
        return ConfigTreeResponse(
            success=True,
            message="Configuration retrieved successfully",
            data={
                "tree": tree,
                "config_path": str(config_manager.config_path),
                "total_nodes": count_nodes(config)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


def count_nodes(obj: Any) -> int:
    """Count total configuration nodes."""
    if not isinstance(obj, dict):
        return 1
    return 1 + sum(count_nodes(v) for v in obj.values())


@router.get("/section/{section_path:path}", response_model=ResponseBase)
async def get_config_section(section_path: str):
    """
    Get a specific configuration section by path.
    
    Path should use dot notation (e.g., "ai-gateway.virtual_models")
    """
    try:
        config_manager = get_config_manager()
        value = config_manager.get(section_path)
        
        if value is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Configuration section not found: {section_path}"
            )
        
        return ResponseBase(
            success=True,
            message=f"Configuration section '{section_path}' retrieved",
            data={
                "path": section_path,
                "value": value,
                "type": type(value).__name__
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config section: {str(e)}")


@router.get("/virtual-models", response_model=ResponseBase)
async def get_virtual_models():
    """
    Get all virtual models configuration.
    
    Returns the complete virtual_models section which supports full CRUD.
    """
    try:
        config_manager = get_config_manager()
        models = config_manager.get_virtual_models()
        
        return ResponseBase(
            success=True,
            message="Virtual models retrieved successfully",
            data={
                "models": models,
                "count": len(models),
                "modifiable": True  # virtual_models supports full CRUD
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get virtual models: {str(e)}")


@router.get("/databases", response_model=ResponseBase)
async def get_database_config():
    """Get all database configurations."""
    try:
        config_manager = get_config_manager()
        
        return ResponseBase(
            success=True,
            message="Database configurations retrieved",
            data={
                "mongodb": config_manager.get_database_config("mongodb"),
                "redis": config_manager.get_database_config("redis"),
                "qdrant": config_manager.get_database_config("qdrant")
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database config: {str(e)}")


@router.get("/app", response_model=ResponseBase)
async def get_app_config():
    """Get application configuration."""
    try:
        config_manager = get_config_manager()
        config = config_manager.get_app_config()

        return ResponseBase(
            success=True,
            message="Application configuration retrieved",
            data=config
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get app config: {str(e)}")


@router.get("/proxy-url", response_model=ResponseBase)
async def get_proxy_url():
    """
    Get the proxy URL for client connections.

    Returns the backend host and port combined with /proxy/v1 path.
    This is used by the frontend to auto-fill the base_url field.
    """
    try:
        config_manager = get_config_manager()
        app_config = config_manager.get_app_config()

        host = app_config.get("host", "localhost")
        port = app_config.get("port", 8000)

        # Determine if we need http or https
        # For now, use http by default (can be enhanced to detect protocol)
        proxy_url = f"http://{host}:{port}/proxy/v1"

        return ResponseBase(
            success=True,
            message="Proxy URL retrieved",
            data={
                "proxy_url": proxy_url,
                "host": host,
                "port": port
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proxy URL: {str(e)}")


class SkillInfo(BaseModel):
    """Skill information."""
    id: str
    name: str
    category: str
    enabled: bool
    version: str
    has_custom: bool
    custom_version: Optional[str] = None


class SkillListResponse(BaseModel):
    """Response for skill list."""
    success: bool = True
    message: str = ""
    skills: List[SkillInfo] = Field(default_factory=list, alias="data")

    model_config = ConfigDict(populate_by_name=True)


@router.get("/skills", response_model=SkillListResponse)
async def get_skills():
    """
    Get all available skills from configuration.

    Returns skills configured in various sections including:
    - Router skills (ai-gateway.router.skill)
    - Knowledge skills (ai-gateway.knowledge.skill)
    - RSS skills (ai-gateway.rss.skill)
    - Media skills
    - Text skills
    """
    try:
        config_manager = get_config_manager()
        skills: List[SkillInfo] = []

        # Router skill
        router_skill = config_manager.get("ai-gateway.router.skill")
        if router_skill:
            skills.append(SkillInfo(
                id="router",
                name="Router Skill",
                category="router",
                enabled=router_skill.get("enabled", False),
                version=router_skill.get("version", "v1"),
                has_custom=router_skill.get("custom", {}).get("enabled", False),
                custom_version=router_skill.get("custom", {}).get("version")
            ))

        # Knowledge skill
        knowledge_skill = config_manager.get("ai-gateway.knowledge.skill")
        if knowledge_skill:
            skills.append(SkillInfo(
                id="knowledge",
                name="Knowledge Base Skill",
                category="knowledge",
                enabled=knowledge_skill.get("enabled", False),
                version=knowledge_skill.get("version", "v1"),
                has_custom=knowledge_skill.get("custom", {}).get("enabled", False),
                custom_version=knowledge_skill.get("custom", {}).get("version")
            ))

        # RSS skill
        rss_skill = config_manager.get("ai-gateway.rss.skill")
        if rss_skill:
            skills.append(SkillInfo(
                id="rss",
                name="RSS Skill",
                category="rss",
                enabled=rss_skill.get("enabled", False),
                version=rss_skill.get("version", "v1"),
                has_custom=rss_skill.get("custom", {}).get("enabled", False),
                custom_version=rss_skill.get("custom", {}).get("version")
            ))

        # Media skill
        media_skill = config_manager.get("ai-gateway.media.skill")
        if media_skill:
            skills.append(SkillInfo(
                id="media",
                name="Media Processing Skill",
                category="media",
                enabled=media_skill.get("enabled", False),
                version=media_skill.get("version", "v1"),
                has_custom=media_skill.get("custom", {}).get("enabled", False),
                custom_version=media_skill.get("custom", {}).get("version")
            ))

        # Text skill
        text_skill = config_manager.get("ai-gateway.text.skill")
        if text_skill:
            skills.append(SkillInfo(
                id="text",
                name="Text Processing Skill",
                category="text",
                enabled=text_skill.get("enabled", False),
                version=text_skill.get("version", "v1"),
                has_custom=text_skill.get("custom", {}).get("enabled", False),
                custom_version=text_skill.get("custom", {}).get("version")
            ))

        return SkillListResponse(
            success=True,
            message=f"Retrieved {len(skills)} skills",
            data=skills
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skills: {str(e)}")


class SearchTargetInfo(BaseModel):
    """Search target information."""
    id: str
    name: str
    enabled: bool
    description: Optional[str] = None


class SearchTargetListResponse(BaseModel):
    """Response for search target list."""
    success: bool = True
    message: str = ""
    targets: List[SearchTargetInfo] = Field(default_factory=list, alias="data")

    model_config = ConfigDict(populate_by_name=True)


@router.get("/search-targets", response_model=SearchTargetListResponse)
async def get_search_targets():
    """
    Get search targets from config.yml.

    Returns only the search targets that are actually configured in web_search section.
    Targets with null configuration are NOT included.
    """
    try:
        config_manager = get_config_manager()
        targets: List[SearchTargetInfo] = []

        # Get web_search config from config.yml
        web_search = config_manager.get("web_search") or {}

        # Define all known search targets with their metadata
        known_targets = {
            "searxng": {
                "name": "SearXNG",
                "description": "Privacy-respecting metasearch engine"
            },
            "LibreX": {
                "name": "LibreX",
                "description": "Privacy-preserving search engine"
            },
            "4get": {
                "name": "4get",
                "description": "Minimalist search engine"
            },
            "brave": {
                "name": "Brave Search",
                "description": "Privacy-focused search with independent index"
            },
            "google": {
                "name": "Google",
                "description": "Google web search"
            },
            "duckduckgo": {
                "name": "DuckDuckGo",
                "description": "Privacy-respecting search engine"
            }
        }

        # Only return targets that have real configuration (not null or empty)
        for target_id, target_info in known_targets.items():
            target_config = web_search.get(target_id)
            # Only include if config is a non-empty dict (has actual configuration)
            if isinstance(target_config, dict) and target_config:
                targets.append(SearchTargetInfo(
                    id=target_id,
                    name=target_info["name"],
                    enabled=True,
                    description=target_info["description"]
                ))

        return SearchTargetListResponse(
            success=True,
            message=f"Retrieved {len(targets)} search targets from config.yml",
            data=targets
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search targets: {str(e)}")
