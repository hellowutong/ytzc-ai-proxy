"""
Skill管理API - 支持多Skill和多版本管理
"""

import os
import re
import yaml
import json
import glob
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter()
SKILL_ROOT = Path("./skills")

# 版本目录正则匹配模式：v + 数字（如 v1, v2, v10）
VERSION_PATTERN = re.compile(r'^v\d+$')


# ============== 数据模型 ==============

class ValidationError(BaseModel):
    line: int
    column: int
    field: Optional[str] = None
    message: str


class ValidationWarning(BaseModel):
    line: int
    message: str
    suggestion: str


class ValidationResult(BaseModel):
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]


class CreateSkillRequest(BaseModel):
    name: str
    version: str = Field(default="v1")
    copy_from: Optional[Dict[str, str]] = None


class CreateVersionRequest(BaseModel):
    new_version: str
    copy_from_version: Optional[str] = None


class UpdateSkillRequest(BaseModel):
    content: str
    save_mode: str = Field(default="update_current")
    new_version: Optional[str] = None


class ValidateRequest(BaseModel):
    content: str


class SkillInfo(BaseModel):
    """Skill 信息"""
    name: str
    is_system: bool
    current_version: str
    all_versions: List[str]
    description: str
    type: str
    enabled: bool = True


# ============== 辅助函数 ==============

def is_version_directory(name: str) -> bool:
    """检查目录名是否为版本目录（v + 数字格式）"""
    return bool(VERSION_PATTERN.match(name))


def get_skill_directories(category: str) -> tuple:
    """
    获取指定分类下的 system 和 custom skill 目录
    
    Args:
        category: 分类路径，如 'virtual_models/routing' 或 'rss'
    
    Returns:
        (system_path, custom_path) 元组
    """
    system_path = SKILL_ROOT / "system" / category
    custom_path = SKILL_ROOT / "custom" / category
    return system_path, custom_path


def list_versions(skill_path: Path) -> List[str]:
    """列出 skill 目录下的所有版本"""
    versions = []
    if skill_path.exists():
        for item in skill_path.iterdir():
            if item.is_dir() and is_version_directory(item.name):
                versions.append(item.name)
    return sorted(versions, key=lambda x: (len(x), x))


def list_skill_names(version_path: Path) -> List[str]:
    """列出版本目录下的所有 skill 名称"""
    names = []
    if version_path.exists():
        for item in version_path.iterdir():
            if item.is_dir():
                names.append(item.name)
    return sorted(names)


def parse_skill_md(skill_md_path: Path) -> Dict[str, Any]:
    """解析 SKILL.md 文件，提取元数据"""
    metadata = {
        "name": skill_md_path.parent.name,
        "description": "",
        "type": "rule-based",
        "priority": 50,
        "enabled": True
    }
    
    if not skill_md_path.exists():
        return metadata
    
    try:
        content = skill_md_path.read_text(encoding='utf-8')
        
        # 解析 YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if frontmatter:
                    metadata["name"] = frontmatter.get('name', metadata["name"])
                    metadata["description"] = frontmatter.get('description', '')
                    metadata["type"] = frontmatter.get('type', 'rule-based')
                    metadata["priority"] = frontmatter.get('priority', 50)
                    metadata["enabled"] = True
    except Exception as e:
        print(f"解析 SKILL.md 失败: {e}")
    
    return metadata


def get_skills_from_category(category: str) -> List[SkillInfo]:
    """
    获取指定分类下的所有 skills
    
    Args:
        category: 分类路径，如 'virtual_models/routing'
    """
    skills = []
    system_path, custom_path = get_skill_directories(category)
    
    # 收集 system skills
    if system_path.exists():
        for version_dir in system_path.iterdir():
            if version_dir.is_dir() and is_version_directory(version_dir.name):
                version = version_dir.name
                for skill_dir in version_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        metadata = parse_skill_md(skill_md)
                        
                        # 检查是否已存在同名 skill
                        existing = next((s for s in skills if s.name == metadata["name"]), None)
                        if existing:
                            if version not in existing.all_versions:
                                existing.all_versions.append(version)
                        else:
                            skills.append(SkillInfo(
                                name=metadata["name"],
                                is_system=True,
                                current_version=version,
                                all_versions=[version],
                                description=metadata["description"],
                                type=metadata["type"],
                                enabled=metadata["enabled"]
                            ))
    
    # 收集 custom skills
    if custom_path.exists():
        for version_dir in custom_path.iterdir():
            if version_dir.is_dir() and is_version_directory(version_dir.name):
                version = version_dir.name
                for skill_dir in version_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        metadata = parse_skill_md(skill_md)
                        
                        # 检查是否已存在同名 skill
                        existing = next((s for s in skills if s.name == metadata["name"] and not s.is_system), None)
                        if existing:
                            if version not in existing.all_versions:
                                existing.all_versions.append(version)
                        else:
                            skills.append(SkillInfo(
                                name=metadata["name"],
                                is_system=False,
                                current_version=version,
                                all_versions=[version],
                                description=metadata["description"],
                                type=metadata["type"],
                                enabled=metadata["enabled"]
                            ))
    
    # 对 versions 排序
    for skill in skills:
        skill.all_versions = sorted(skill.all_versions, key=lambda x: (len(x), x))
        if skill.all_versions:
            skill.current_version = skill.all_versions[-1]  # 使用最新版本
    
    return skills


# ============== API端点 ==============

@router.get("/skills")
async def get_skills():
    """获取所有Skill分类列表"""
    categories = []
    
    # 扫描 skills/system 目录获取分类
    system_path = SKILL_ROOT / "system"
    if system_path.exists():
        for item in system_path.iterdir():
            if item.is_dir():
                # 检查是否是一级分类（如 rss, knowledge）
                # 或二级分类的父级（如 virtual_models, media）
                sub_categories = []
                has_skills = False
                
                for sub in item.iterdir():
                    if sub.is_dir():
                        if is_version_directory(sub.name):
                            # 直接有版本目录，说明是一级分类
                            has_skills = True
                        else:
                            # 有子分类目录
                            sub_categories.append(sub.name)
                
                if sub_categories:
                    # 有子分类
                    categories.append({
                        "name": item.name,
                        "children": sub_categories
                    })
                elif has_skills:
                    # 一级分类
                    categories.append({
                        "name": item.name,
                        "children": []
                    })
    
    return {"code": 200, "message": "success", "data": {"categories": categories}}


@router.get("/skills/{category:path}")
async def get_skills_by_category(category: str):
    """获取指定分类下的所有Skills（支持多级路径）"""
    try:
        skills = get_skills_from_category(category)
        return {
            "code": 200,
            "message": "success",
            "data": [s.model_dump() for s in skills]
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"加载Skills失败: {str(e)}",
            "data": []
        }


@router.get("/skills/{category:path}/{name}")
async def get_skill_detail(category: str, name: str, is_custom: bool = Query(False), version: Optional[str] = Query(None)):
    """获取Skill详情"""
    try:
        scope = "custom" if is_custom else "system"
        skill_base = SKILL_ROOT / scope / category
        
        if not version:
            # 获取最新版本
            versions = list_versions(skill_base)
            if not versions:
                return {"code": 404, "message": f"Skill不存在: {name}", "data": None}
            version = versions[-1]
        
        skill_dir = skill_base / version / name
        skill_md = skill_dir / "SKILL.md"
        
        if not skill_md.exists():
            return {"code": 404, "message": f"Skill不存在: {name}", "data": None}
        
        content = skill_md.read_text(encoding='utf-8')
        metadata = parse_skill_md(skill_md)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "name": metadata["name"],
                "category": category,
                "version": version,
                "is_custom": is_custom,
                "description": metadata["description"],
                "type": metadata["type"],
                "content": content
            }
        }
    except Exception as e:
        return {"code": 500, "message": f"加载Skill详情失败: {str(e)}", "data": None}


@router.get("/skills/{category:path}/{name}/versions")
async def get_skill_versions(category: str, name: str, is_custom: bool = Query(False)):
    """获取指定Skill的所有可用版本"""
    try:
        scope = "custom" if is_custom else "system"
        skill_base = SKILL_ROOT / scope / category
        
        versions = []
        for version_dir in skill_base.iterdir():
            if version_dir.is_dir() and is_version_directory(version_dir.name):
                skill_dir = version_dir / name
                if skill_dir.exists() and skill_dir.is_dir():
                    versions.append(version_dir.name)
        
        return {
            "code": 200,
            "message": "success",
            "data": {"versions": sorted(versions, key=lambda x: (len(x), x))}
        }
    except Exception as e:
        return {"code": 500, "message": f"获取版本列表失败: {str(e)}", "data": {"versions": []}}


# 特定路由必须放在参数化路由之前！
@router.post("/skills/validate")
async def validate_skill(request: ValidateRequest):
    """校验Skill内容"""
    errors = []
    warnings = []
    
    try:
        # 检查 YAML frontmatter
        if request.content.startswith('---'):
            parts = request.content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if not frontmatter:
                    errors.append(ValidationError(line=1, column=1, message="YAML frontmatter 解析失败"))
                else:
                    # 检查必需字段
                    if 'name' not in frontmatter:
                        warnings.append(ValidationWarning(line=1, message="缺少 name 字段", suggestion="添加 name 字段"))
                    if 'type' not in frontmatter:
                        warnings.append(ValidationWarning(line=1, message="缺少 type 字段", suggestion="添加 type 字段 (rule-based/llm-based/hybrid)"))
            else:
                errors.append(ValidationError(line=1, column=1, message="YAML frontmatter 格式错误"))
        else:
            warnings.append(ValidationWarning(line=1, message="缺少 YAML frontmatter", suggestion="在文件开头添加 YAML frontmatter"))
    except yaml.YAMLError as e:
        errors.append(ValidationError(line=1, column=1, message=f"YAML 解析错误: {str(e)}"))
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "valid": len(errors) == 0,
            "errors": [e.model_dump() for e in errors],
            "warnings": [w.model_dump() for w in warnings]
        }
    }


@router.post("/skills/reload")
async def reload_all_skills():
    """重新加载所有Skills"""
    return {"code": 200, "message": "所有Skill重载成功", "data": None}


@router.post("/skills/{category:path}")
async def create_skill(category: str, request: CreateSkillRequest):
    """创建新的自定义Skill"""
    try:
        skill_base = SKILL_ROOT / "custom" / category / request.version / request.name
        
        if skill_base.exists():
            return {"code": 400, "message": f"Skill已存在: {request.name}", "data": None}
        
        # 创建目录
        skill_base.mkdir(parents=True, exist_ok=True)
        
        # 创建默认 SKILL.md
        default_content = f'''---
name: {request.name}
description: 自定义 Skill
type: rule-based
priority: 50
version: "{request.version}"
input_schema:
  type: object
  properties:
    input:
      type: string
output_schema:
  type: object
  properties:
    result:
      type: string
---

# {request.name}

这是一个新创建的自定义 Skill。

## 使用说明

请在此添加 Skill 的使用说明。

## 规则定义

请在此定义 Skill 的规则。
'''
        
        skill_md = skill_base / "SKILL.md"
        skill_md.write_text(default_content, encoding='utf-8')
        
        return {"code": 200, "message": "Skill创建成功", "data": {"path": str(skill_base)}}
    except Exception as e:
        return {"code": 500, "message": f"创建Skill失败: {str(e)}", "data": None}


@router.post("/skills/{category:path}/{name}/versions")
async def create_version(category: str, name: str, request: CreateVersionRequest):
    """为现有自定义Skill创建新版本"""
    try:
        custom_base = SKILL_ROOT / "custom" / category
        new_version_dir = custom_base / request.new_version / name
        
        if new_version_dir.exists():
            return {"code": 400, "message": f"版本已存在: {request.new_version}", "data": None}
        
        if request.copy_from_version:
            # 从指定版本复制
            source_dir = custom_base / request.copy_from_version / name
            if source_dir.exists():
                shutil.copytree(source_dir, new_version_dir)
            else:
                new_version_dir.mkdir(parents=True, exist_ok=True)
                (new_version_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n# {name}\n", encoding='utf-8')
        else:
            # 创建空版本
            new_version_dir.mkdir(parents=True, exist_ok=True)
            (new_version_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n# {name}\n", encoding='utf-8')
        
        return {"code": 200, "message": "版本创建成功", "data": {"version": request.new_version}}
    except Exception as e:
        return {"code": 500, "message": f"创建版本失败: {str(e)}", "data": None}


@router.put("/skills/{category:path}/{name}")
async def update_skill_content(category: str, name: str, request: UpdateSkillRequest, version: Optional[str] = Query(None)):
    """更新自定义Skill内容"""
    try:
        skill_base = SKILL_ROOT / "custom" / category
        
        if not version:
            versions = list_versions(skill_base)
            if not versions:
                return {"code": 404, "message": f"Skill不存在: {name}", "data": None}
            version = versions[-1]
        
        skill_md = skill_base / version / name / "SKILL.md"
        
        if not skill_md.exists():
            return {"code": 404, "message": f"Skill不存在: {name}", "data": None}
        
        skill_md.write_text(request.content, encoding='utf-8')
        
        return {"code": 200, "message": "Skill更新成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"更新Skill失败: {str(e)}", "data": None}


@router.delete("/skills/{category:path}/{name}")
async def delete_skill(category: str, name: str, is_custom: bool = Query(True)):
    """删除自定义Skill"""
    try:
        if not is_custom:
            return {"code": 400, "message": "不能删除系统Skill", "data": None}
        
        skill_base = SKILL_ROOT / "custom" / category
        
        # 删除所有版本
        deleted = False
        for version_dir in skill_base.iterdir():
            if version_dir.is_dir() and is_version_directory(version_dir.name):
                skill_dir = version_dir / name
                if skill_dir.exists():
                    shutil.rmtree(skill_dir)
                    deleted = True
        
        if not deleted:
            return {"code": 404, "message": f"Skill不存在: {name}", "data": None}
        
        return {"code": 200, "message": "Skill已删除", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除Skill失败: {str(e)}", "data": None}


@router.delete("/skills/{category:path}/{name}/versions/{version}")
async def delete_version(category: str, name: str, version: str):
    """删除指定版本"""
    try:
        skill_dir = SKILL_ROOT / "custom" / category / version / name
        
        if not skill_dir.exists():
            return {"code": 404, "message": f"版本不存在: {version}", "data": None}
        
        shutil.rmtree(skill_dir)
        
        return {"code": 200, "message": "版本已删除", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除版本失败: {str(e)}", "data": None}


@router.post("/skills/{category:path}/{name}/reload")
async def reload_skill(category: str, name: str, version: Optional[str] = Query(None)):
    """重新加载Skill"""
    return {"code": 200, "message": "Skill已重载", "data": None}
