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
# 使用绝对路径，确保在 Docker 容器中也能正确找到 skills 目录
# 首先尝试 /app/skills (Docker 容器内), 然后尝试相对路径 ./skills (宿主机开发时)
def get_skill_root() -> Path:
    docker_path = Path("/app/skills")
    if docker_path.exists():
        return docker_path.resolve()
    # 如果在 Windows 上运行，尝试项目根目录的 skills
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent
    skills_path = project_root / "skills"
    if skills_path.exists():
        return skills_path
    # 最后尝试相对路径
    return Path("./skills").resolve()

SKILL_ROOT = get_skill_root()

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


class FileNode(BaseModel):
    """文件树节点"""
    name: str
    type: str  # 'file' | 'directory'
    path: str
    editable: bool = True
    is_custom: bool = False  # 标记是否属于 custom skill
    children: Optional[List['FileNode']] = None


class CreateFileRequest(BaseModel):
    """创建文件请求"""
    category: str
    name: str
    version: str = Field(default="v1")
    is_custom: bool = Field(default=True)
    file_name: str
    parent_path: str = Field(default="")  # 相对于 skill 根目录的路径


class CreateFolderRequest(BaseModel):
    """创建文件夹请求"""
    category: str
    name: str
    version: str = Field(default="v1")
    is_custom: bool = Field(default=True)
    folder_name: str
    parent_path: str = Field(default="")


class RenameRequest(BaseModel):
    """重命名请求"""
    category: str
    name: str
    version: str = Field(default="v1")
    is_custom: bool = Field(default=True)
    old_path: str
    new_name: str


class SaveFileRequest(BaseModel):
    """保存文件请求"""
    category: str
    name: str
    version: str = Field(default="v1")
    is_custom: bool = Field(default=True)
    file_path: str
    content: str


class DeleteFileRequest(BaseModel):
    """删除文件/文件夹请求"""
    category: str
    name: str
    version: str = Field(default="v1")
    is_custom: bool = Field(default=True)
    file_path: str


class ValidateFileRequest(BaseModel):
    """校验文件请求"""
    file_path: str
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
    
    # 预先收集所有可用的系统和自定义版本
    all_system_versions = sorted([d.name for d in system_path.iterdir() if d.is_dir() and is_version_directory(d.name)]) if system_path.exists() else ["v1"]
    all_custom_versions = sorted([d.name for d in custom_path.iterdir() if d.is_dir() and is_version_directory(d.name)]) if custom_path.exists() else ["v1"]

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
                        if not existing:
                            skills.append(SkillInfo(
                                name=metadata["name"],
                                is_system=True,
                                current_version=version,
                                all_versions=all_system_versions,  # 使用全局版本列表
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
                        if not existing:
                            skills.append(SkillInfo(
                                name=metadata["name"],
                                is_system=False,
                                current_version=version,
                                all_versions=all_custom_versions,  # 使用全局版本列表
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
async def get_skills_by_category_or_detail(
    category: str, 
    name: Optional[str] = Query(None),
    is_custom: bool = Query(False), 
    version: Optional[str] = Query(None)
):
    """
    获取指定分类下的所有Skills 或 单个Skill详情
    
    - 如果没有 name 参数，返回分类下的所有 Skills 列表
    - 如果有 name 参数，返回特定 Skill 的详情
    """
    # 如果有 name 参数，返回 Skill 详情
    if name:
        try:
            scope = "custom" if is_custom else "system"
            skill_base = SKILL_ROOT / scope / category
            
            if not version:
                # 获取最新版本
                versions = list_versions(skill_base)
                if not versions:
                    return {"code": 404, "message": f"版本目录不存在", "data": None}
                version = versions[-1]
            
            skill_dir = skill_base / version / name
            skill_md = skill_dir / "SKILL.md"
            
            # 目录不存在才返回404
            if not skill_dir.exists():
                return {"code": 404, "message": f"Skill目录不存在: {name}", "data": None}
            
            # 目录存在但SKILL.md不存在，返回空内容
            if not skill_md.exists():
                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "name": name,
                        "category": category,
                        "version": version,
                        "is_custom": is_custom,
                        "description": "",
                        "type": "rule-based",
                        "content": "",
                        "is_new": True
                    }
                }
            
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
    
    # 返回分类下的 Skills 列表
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
    """更新自定义Skill内容 - 如果目录或文件不存在则自动创建"""
    try:
        skill_base = SKILL_ROOT / "custom" / category
        
        if not version:
            versions = list_versions(skill_base)
            if not versions:
                # 如果没有版本目录，创建 v1
                version = "v1"
            else:
                version = versions[-1]
        
        skill_dir = skill_base / version / name
        skill_md = skill_dir / "SKILL.md"
        
        # 自动创建目录（如果不存在）
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入内容（文件不存在会自动创建）
        skill_md.write_text(request.content, encoding='utf-8')
        
        return {"code": 200, "message": "Skill保存成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"保存Skill失败: {str(e)}", "data": None}


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


# ============== Skill 文件管理 API ==============

def build_file_tree(skill_dir: Path, base_path: Path, is_custom: bool = False) -> List[FileNode]:
    """递归构建文件树"""
    nodes = []
    if not skill_dir.exists():
        return nodes
    
    for item in sorted(skill_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
        relative_path = str(item.relative_to(base_path))
        
        if item.is_dir():
            children = build_file_tree(item, base_path, is_custom)
            nodes.append(FileNode(
                name=item.name,
                type="directory",
                path=relative_path,
                editable=True,
                is_custom=is_custom,
                children=children
            ))
        else:
            # 检查文件是否可编辑
            is_editable = item.suffix.lower() in ['.md', '.py']
            nodes.append(FileNode(
                name=item.name,
                type="file",
                path=relative_path,
                editable=is_editable,
                is_custom=is_custom,
                children=None
            ))
    
    return nodes


@router.get("/skill-files")
async def get_skill_files(
    category: str,
    is_custom: bool = Query(default=False)
):
    """获取 Skill 分类文件树（包含所有版本和所有 Skill）"""
    try:
        scope = "custom" if is_custom else "system"
        category_dir = SKILL_ROOT / scope / category
        
        # 收集调试信息
        debug_info = {
            "skill_root": str(SKILL_ROOT),
            "skill_root_exists": SKILL_ROOT.exists(),
            "category_dir": str(category_dir),
            "category_dir_exists": category_dir.exists(),
            "parent_exists": category_dir.parent.exists() if category_dir.parent else False,
        }
        
        # 检查 SKILL_ROOT/system 是否存在
        system_dir = SKILL_ROOT / "system"
        debug_info["system_dir_exists"] = system_dir.exists()
        if system_dir.exists():
            try:
                debug_info["system_items"] = [item.name for item in system_dir.iterdir()]
            except Exception as e:
                debug_info["system_items_error"] = str(e)
        
        if not category_dir.exists():
            return {"code": 404, "message": f"分类目录不存在", "test": "THIS_IS_A_TEST",
            "debug": debug_info, "data": None}
        
        file_tree = build_file_tree(category_dir, category_dir, is_custom=scope=="custom")
        
        return {
            "code": 200,
            "message": "success",
            "test": "THIS_IS_A_TEST",
            "debug": debug_info,
            "data": {
                "category": category,
                "is_custom": is_custom,
                "files": [n.model_dump() for n in file_tree]
            }
        }
    except Exception as e:
        import traceback
        return {"code": 500, "message": f"获取文件树失败: {str(e)}", "data": None, "traceback": traceback.format_exc()}


def parse_file_path(full_path: str) -> tuple:
    """
    解析完整文件路径，提取 version, skill_name, relative_path
    
    格式: v1/default/SKILL.md -> ("v1", "default", "SKILL.md")
    格式: v2/myskill/references/api.md -> ("v2", "myskill", "references/api.md")
    """
    parts = full_path.split('/')
    if len(parts) < 2:
        return None, None, None
    
    version = parts[0]
    skill_name = parts[1]
    relative_path = '/'.join(parts[2:]) if len(parts) > 2 else ''
    
    return version, skill_name, relative_path


@router.get("/skill-files/content")
async def get_file_content(
    category: str,
    file_path: str,
    is_custom: bool = Query(default=False)
):
    """
    读取文件内容
    
    file_path 格式: v1/default/SKILL.md（包含版本和 skill 名称）
    """
    try:
        # 解析完整路径
        version, skill_name, relative_path = parse_file_path(file_path)
        if not version or not skill_name:
            return {"code": 400, "message": f"文件路径格式错误: {file_path}", "data": None}
        
        scope = "custom" if is_custom else "system"
        category_dir = SKILL_ROOT / scope / category
        file_full_path = category_dir / file_path
        
        if not file_full_path.exists():
            return {"code": 404, "message": f"文件不存在: {file_path}", "data": None}
        
        if not file_full_path.is_file():
            return {"code": 400, "message": f"路径不是文件: {file_path}", "data": None}
        
        # 检查路径安全 - 防止路径遍历攻击
        try:
            file_full_path.resolve().relative_to(category_dir.resolve())
        except ValueError:
            return {"code": 403, "message": "非法文件路径", "data": None}
        
        # 检查文件是否为文本文件
        is_text = file_full_path.suffix.lower() in ['.md', '.py', '.txt', '.json', '.yaml', '.yml']
        
        if is_text:
            content = file_full_path.read_text(encoding='utf-8')
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "path": file_path,
                    "content": content,
                    "editable": file_full_path.suffix.lower() in ['.md', '.py'],
                    "type": "text"
                }
            }
        else:
            # 非文本文件返回基本信息
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "path": file_path,
                    "content": "",
                    "editable": False,
                    "type": "binary",
                    "size": file_full_path.stat().st_size
                }
            }
    except Exception as e:
        return {"code": 500, "message": f"读取文件失败: {str(e)}", "data": None}


@router.put("/skill-files/content")
async def save_file_content(request: SaveFileRequest):
    """保存文件内容"""
    try:
        scope = "custom" if request.is_custom else "system"
        skill_dir = SKILL_ROOT / scope / request.category / request.version / request.name
        file_full_path = skill_dir / request.file_path
        
        # 检查路径安全
        try:
            file_full_path.resolve().relative_to(skill_dir.resolve())
        except ValueError:
            return {"code": 403, "message": "非法文件路径", "data": None}
        
        # 只允许编辑 .md 和 .py 文件
        if file_full_path.suffix.lower() not in ['.md', '.py']:
            return {"code": 400, "message": "只能编辑 .md 和 .py 文件", "data": None}
        
        # 创建父目录（如果不存在）
        file_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        file_full_path.write_text(request.content, encoding='utf-8')
        
        return {"code": 200, "message": "文件保存成功", "data": {"path": request.file_path}}
    except Exception as e:
        return {"code": 500, "message": f"保存文件失败: {str(e)}", "data": None}


@router.post("/skill-files/operation")
async def file_operation(operation: str, request: Dict[str, Any]):
    """文件管理操作（创建/重命名）"""
    try:
        category = request.get("category")
        is_custom = request.get("is_custom", True)
        
        scope = "custom" if is_custom else "system"
        category_dir = SKILL_ROOT / scope / category
        
        if operation == "create_file":
            file_name = request.get("file_name")
            parent_path = request.get("parent_path", "")
            
            # 检查文件名合法性
            if not file_name or not file_name.endswith(('.md', '.py')):
                return {"code": 400, "message": "文件名必须以 .md 或 .py 结尾", "data": None}
            
            file_full_path = category_dir / parent_path / file_name
            
            # 检查路径安全
            try:
                file_full_path.resolve().relative_to(category_dir.resolve())
            except ValueError:
                return {"code": 403, "message": "非法文件路径", "data": None}
            
            if file_full_path.exists():
                return {"code": 400, "message": f"文件已存在: {file_name}", "data": None}
            
            # 创建文件
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text("", encoding='utf-8')
            
            return {"code": 200, "message": "文件创建成功", "data": {"path": str(file_full_path.relative_to(category_dir))}}
        
        elif operation == "create_folder":
            folder_name = request.get("folder_name")
            parent_path = request.get("parent_path", "")
            
            if not folder_name:
                return {"code": 400, "message": "文件夹名不能为空", "data": None}
            
            folder_full_path = category_dir / parent_path / folder_name
            
            # 检查路径安全
            try:
                folder_full_path.resolve().relative_to(category_dir.resolve())
            except ValueError:
                return {"code": 403, "message": "非法文件夹路径", "data": None}
            
            if folder_full_path.exists():
                return {"code": 400, "message": f"文件夹已存在: {folder_name}", "data": None}
            
            # 创建文件夹
            folder_full_path.mkdir(parents=True, exist_ok=True)
            
            return {"code": 200, "message": "文件夹创建成功", "data": {"path": str(folder_full_path.relative_to(category_dir))}}
        
        elif operation == "rename":
            old_path = request.get("old_path")
            new_name = request.get("new_name")
            
            if not old_path or not new_name:
                return {"code": 400, "message": "缺少必要参数", "data": None}
            
            old_full_path = category_dir / old_path
            new_full_path = old_full_path.parent / new_name
            
            # 检查路径安全
            try:
                old_full_path.resolve().relative_to(category_dir.resolve())
                new_full_path.resolve().relative_to(category_dir.resolve())
            except ValueError:
                return {"code": 403, "message": "非法文件路径", "data": None}
            
            if not old_full_path.exists():
                return {"code": 404, "message": f"文件或文件夹不存在: {old_path}", "data": None}
            
            if new_full_path.exists():
                return {"code": 400, "message": f"目标名称已存在: {new_name}", "data": None}
            
            # 重命名
            old_full_path.rename(new_full_path)
            
            return {"code": 200, "message": "重命名成功", "data": {"path": str(new_full_path.relative_to(category_dir))}}
        
        else:
            return {"code": 400, "message": f"未知操作: {operation}", "data": None}
    
    except Exception as e:
        return {"code": 500, "message": f"操作失败: {str(e)}", "data": None}


@router.delete("/skill-files")
async def delete_file_or_folder(
    category: str,
    file_path: str,
    is_custom: bool = Query(default=True)
):
    """删除文件或文件夹"""
    try:
        scope = "custom" if is_custom else "system"
        category_dir = SKILL_ROOT / scope / category
        file_full_path = category_dir / file_path
        
        # 检查路径安全
        try:
            file_full_path.resolve().relative_to(category_dir.resolve())
        except ValueError:
            return {"code": 403, "message": "非法文件路径", "data": None}
        
        if not file_full_path.exists():
            return {"code": 404, "message": f"文件或文件夹不存在: {file_path}", "data": None}
        
        # 不允许删除 SKILL.md
        if file_full_path.name == "SKILL.md":
            return {"code": 400, "message": "不能删除 SKILL.md 文件", "data": None}
        
        # 删除
        if file_full_path.is_dir():
            shutil.rmtree(file_full_path)
        else:
            file_full_path.unlink()
        
        return {"code": 200, "message": "删除成功", "data": None}
    except Exception as e:
        return {"code": 500, "message": f"删除失败: {str(e)}", "data": None}


@router.post("/skill-files/validate")
async def validate_file(request: ValidateFileRequest):
    """增强校验文件内容"""
    errors = []
    warnings = []
    
    file_path = request.file_path
    content = request.content
    
    # 根据文件类型进行不同校验
    if file_path.endswith('.md'):
        # Markdown 文件校验 - 特别是 SKILL.md
        if file_path.endswith('SKILL.md'):
            # 检查 YAML frontmatter
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        if frontmatter:
                            # 检查必需字段
                            required_fields = ['name', 'type', 'priority'] 
                            for field in required_fields:
                                if field not in frontmatter:
                                    errors.append({
                                        "line": 1,
                                        "column": 1,
                                        "message": f"缺少必需字段: {field}"
                                    })
                            
                            # 检查 description（警告级别）
                            if 'description' not in frontmatter or not frontmatter['description']:
                                warnings.append({
                                    "line": 1,
                                    "message": "建议添加 description 字段",
                                    "suggestion": "在 YAML frontmatter 中添加 description 字段描述 Skill 功能"
                                })
                            
                            # 检查 JSON Schema 有效性
                            if 'input_schema' in frontmatter:
                                try:
                                    json.dumps(frontmatter['input_schema'])
                                except Exception as e:
                                    errors.append({
                                        "line": 1,
                                        "column": 1,
                                        "message": f"input_schema 格式错误: {str(e)}"
                                    })
                            
                            if 'output_schema' in frontmatter:
                                try:
                                    json.dumps(frontmatter['output_schema'])
                                except Exception as e:
                                    errors.append({
                                        "line": 1,
                                        "column": 1,
                                        "message": f"output_schema 格式错误: {str(e)}"
                                    })
                        else:
                            errors.append({
                                "line": 1,
                                "column": 1,
                                "message": "YAML frontmatter 解析失败"
                            })
                    else:
                        errors.append({
                            "line": 1,
                            "column": 1,
                            "message": "YAML frontmatter 格式错误，缺少结束标记"
                        })
                except yaml.YAMLError as e:
                    errors.append({
                        "line": 1,
                        "column": 1,
                        "message": f"YAML 解析错误: {str(e)}"
                    })
            else:
                warnings.append({
                    "line": 1,
                    "message": "SKILL.md 缺少 YAML frontmatter",
                    "suggestion": "在文件开头添加 YAML frontmatter 定义 Skill 元数据"
                })
    
    elif file_path.endswith('.py'):
        # Python 文件校验 - 语法检查
        try:
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            errors.append({
                "line": e.lineno or 1,
                "column": e.offset or 1,
                "message": f"Python 语法错误: {e.msg}"
            })
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    }

