"""
Skill管理API
"""

import os
import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Skill根目录 - 相对于backend目录
import pathlib
SKILL_ROOT = str(pathlib.Path(__file__).parent.parent.parent.parent / "skill")


def _scan_skill_versions(category: str, skill_type: str = "system") -> List[str]:
    """
    获取指定分类和类型的可用版本列表

    Args:
        category: Skill分类 (如 router, knowledge, web_search)
        skill_type: skill类型 (system/custom)

    Returns:
        版本列表，按版本号排序 [v1, v2, v3...]
    """
    import glob
    skill_path = os.path.join(SKILL_ROOT, skill_type, category)

    if not os.path.exists(skill_path):
        return []

    versions = set()
    
    # 使用glob查找所有版本目录
    version_pattern = os.path.join(skill_path, "v*")
    for version_dir in glob.glob(version_pattern):
        if os.path.isdir(version_dir):
            version_name = os.path.basename(version_dir)
            if version_name.startswith("v"):
                # 检查版本目录下是否有子目录（技能名称）
                skill_pattern = os.path.join(version_dir, "*", "SKILL.md")
                skill_files = glob.glob(skill_pattern)
                if skill_files:
                    versions.add(version_name)

    # 按版本号排序 (v1, v2, v3..., v10, v11...)
    def version_key(v):
        match = re.match(r"v(\d+)", v)
        return int(match.group(1)) if match else 0

    return sorted(versions, key=version_key)


class Skill(BaseModel):
    id: str
    category: str
    name: str
    type: str  # 'system' or 'custom'
    version: str
    enabled: bool
    description: Optional[str] = ""


# Mock skills data
SKILLS = [
    {"id": "1", "category": "router", "name": "model_router", "type": "system", "version": "v1", "enabled": True, "description": "模型路由决策"},
    {"id": "2", "category": "virtual_models/knowledge", "name": "knowledge_retrieval", "type": "system", "version": "v1", "enabled": True, "description": "知识库检索"},
    {"id": "3", "category": "virtual_models/web_search", "name": "web_search", "type": "system", "version": "v1", "enabled": False, "description": "联网搜索"},
    {"id": "4", "category": "knowledge", "name": "text_extraction", "type": "system", "version": "v1", "enabled": True, "description": "文本知识提取"},
    {"id": "5", "category": "rss", "name": "rss_processor", "type": "system", "version": "v1", "enabled": True, "description": "RSS文章处理"},
    {"id": "6", "category": "audio", "name": "audio_transcription", "type": "system", "version": "v1", "enabled": True, "description": "音频转录"},
    {"id": "7", "category": "video", "name": "video_transcription", "type": "system", "version": "v1", "enabled": True, "description": "视频转录"},
    {"id": "8", "category": "text", "name": "text_parser", "type": "system", "version": "v1", "enabled": True, "description": "文档解析"},
]


@router.get("/skills")
async def get_skills():
    """获取所有Skills"""
    return {
        "code": 200,
        "message": "success",
        "data": SKILLS
    }


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, skill_data: dict):
    """更新Skill配置"""
    for i, skill in enumerate(SKILLS):
        if skill["id"] == skill_id:
            SKILLS[i].update(skill_data)
            return {
                "code": 200,
                "message": "Skill更新成功",
                "data": SKILLS[i]
            }
    
    raise HTTPException(status_code=404, detail="Skill不存在")


@router.get("/skills/{category}/{name}/{skill_type}/content")
async def get_skill_content(category: str, name: str, skill_type: str):
    """获取Skill内容"""
    # Return mock SKILL.md content
    content = f"""---
name: {name}
description: Skill description
type: rule-based
priority: 50
version: "1.0.0"
---

# {name}

This is a {skill_type} skill for {category}.

## Description

Skill description here...

## Usage

Usage instructions...
"""
    
    return {
        "code": 200,
        "message": "success",
        "data": {"content": content}
    }


@router.put("/skills/{category}/{name}/custom/content")
async def save_skill_content(category: str, name: str, body: dict):
    """保存自定义Skill内容"""
    content = body.get("content", "")
    
    # TODO: Save to file system
    
    return {
        "code": 200,
        "message": "Skill保存成功",
        "data": None
    }


@router.post("/skills/{category}/{name}/reload")
async def reload_skill(category: str, name: str):
    """重新加载Skill"""
    return {
        "code": 200,
        "message": f"Skill {category}/{name} 重载成功",
        "data": None
    }


@router.post("/skills/reload")
async def reload_all_skills():
    """重新加载所有Skills"""
    return {
        "code": 200,
        "message": "所有Skill重载成功",
        "data": None
    }


@router.get("/skills/versions")
async def list_skill_versions(category: str, skill_type: str = "system"):
    """
    获取指定分类的可用Skill版本列表

    Query Parameters:
        category: Skill分类 (router, knowledge, web_search)
        skill_type: Skill类型 (system/custom, 默认system)

    Returns:
        可用版本列表
    """
    versions = _scan_skill_versions(category, skill_type)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "category": category,
            "skill_type": skill_type,
            "versions": versions
        }
    }
    return {
        "code": 200,
        "message": "success",
        "data": {
            "category": category,
            "skill_type": skill_type,
            "versions": versions
        }
    }
