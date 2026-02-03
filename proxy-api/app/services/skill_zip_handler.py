"""
Skill ZIP 导入/导出处理器
支持将 Skill 打包为 ZIP 文件，以及从 ZIP 文件导入 Skill
"""
import json
import zipfile
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from io import BytesIO
from datetime import datetime

from app.domain.models.skill import Skill, SkillVersion, SkillStatus


class SkillZipExporter:
    """Skill ZIP 导出器"""
    
    def __init__(self, export_path: Optional[str] = None):
        """
        初始化导出器
        
        Args:
            export_path: 导出目录路径（可选）
        """
        self.export_path = Path(export_path) if export_path else None
        self.version_content_template = """# {base_id} - Version {version_id}

## 版本信息
- 版本号: {version_id}
- 状态: {status}
- 创建时间: {created_at}
- 创建者: {created_by}
- 来源会话: {source_session_id}
- 变更原因: {change_reason}

## 内容
{content}
"""
    
    def create_zip(
        self,
        skill: Skill,
        include_prompt_template: bool = False,
        include_examples: bool = False,
        include_assets: bool = False
    ) -> BytesIO:
        """
        创建 Skill 的 ZIP 文件
        
        Args:
            skill: Skill 对象
            include_prompt_template: 是否包含 Prompt 模板
            include_examples: 是否包含示例
            include_assets: 是否包含资源文件
            
        Returns:
            ZIP 文件的 BytesIO 对象
        """
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 写入 skill.json
            skill_data = {
                "base_id": skill.base_id,
                "active_version_id": skill.active_version_id,
                "created_at": skill.created_at,
                "versions": [
                    {
                        "version_id": v.version_id,
                        "status": v.status.value if hasattr(v.status, 'value') else v.status,
                        "created_at": v.created_at,
                        "created_by": v.created_by,
                        "source_session_id": v.source_session_id,
                        "change_reason": v.change_reason
                    }
                    for v in skill.versions
                ]
            }
            zf.writestr("skill.json", json.dumps(skill_data, ensure_ascii=False, indent=2))
            
            # 写入版本文件
            for version in skill.versions:
                version_file = f"versions/version_{version.version_id}/metadata.json"
                version_data = {
                    "version_id": version.version_id,
                    "status": version.status.value if hasattr(version.status, 'value') else version.status,
                    "created_at": version.created_at,
                    "created_by": version.created_by,
                    "source_session_id": version.source_session_id,
                    "change_reason": version.change_reason
                }
                zf.writestr(version_file, json.dumps(version_data, ensure_ascii=False, indent=2))
                
                # 内容文件
                content_file = f"versions/version_{version.version_id}/content.md"
                content = self._generate_version_content(skill.base_id, version)
                zf.writestr(content_file, content)
            
            # 可选：Prompt 模板
            if include_prompt_template:
                prompt_template = self._generate_prompt_template(skill)
                zf.writestr("prompt-template.md", prompt_template)
            
            # 可选：示例
            if include_examples:
                examples_data = self._generate_examples(skill)
                zf.writestr("examples.json", json.dumps(examples_data, ensure_ascii=False, indent=2))
            
            # 可选：资源文件占位
            if include_assets:
                zf.writestr("assets/README.md", "# 资源文件目录\n\n将资源文件放在此目录中")
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def _generate_version_content(self, base_id: str, version: SkillVersion) -> str:
        """生成版本内容文件"""
        status = version.status.value if hasattr(version.status, 'value') else version.status
        source_session = version.source_session_id or "N/A"
        change_reason = version.change_reason or "N/A"
        
        return self.version_content_template.format(
            base_id=base_id,
            version_id=version.version_id,
            status=status,
            created_at=version.created_at,
            created_by=version.created_by,
            source_session_id=source_session,
            change_reason=change_reason,
            content="# 在此添加技能内容..."
        )
    
    def _generate_prompt_template(self, skill: Skill) -> str:
        """生成 Prompt 模板"""
        return f"""# {skill.base_id} - Prompt 模板

## 技能描述
这是一个自动生成的 Skill。

## 使用场景

## 指令

## 示例

"""
    
    def _generate_examples(self, skill: Skill) -> List[Dict]:
        """生成示例数据"""
        return [
            {
                "id": 1,
                "input": "示例输入 1",
                "output": "示例输出 1",
                "description": "第一个示例"
            }
        ]
    
    def export_skill_to_file(
        self,
        skill: Skill,
        file_path: str,
        **kwargs
    ) -> str:
        """
        将 Skill 导出到文件
        
        Args:
            skill: Skill 对象
            file_path: 输出文件路径
            **kwargs: 其他传递给 create_zip 的参数
            
        Returns:
            导出文件的路径
        """
        zip_buffer = self.create_zip(skill, **kwargs)
        
        with open(file_path, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        return file_path


class SkillZipImporter:
    """Skill ZIP 导入器"""
    
    def __init__(self, import_path: Optional[str] = None):
        """
        初始化导入器
        
        Args:
            import_path: 导入目录路径（可选）
        """
        self.import_path = Path(import_path) if import_path else None
        self.required_files = ["skill.json"]
    
    def validate_zip(self, zip_buffer: BytesIO) -> Tuple[bool, str]:
        """
        验证 ZIP 文件有效性
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            (是否有效, 验证消息)
        """
        try:
            zip_buffer.seek(0)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                file_list = zf.namelist()
                
                # 检查必需文件
                for required in self.required_files:
                    if required not in file_list:
                        return False, f"缺少必需文件: {required}"
                
                # 检查 ZIP 完整性
                bad_file = zf.testzip()
                if bad_file is not None:
                    return False, f"ZIP 文件损坏: {bad_file}"
                
                return True, "ZIP 文件有效"
        
        except zipfile.BadZipFile:
            return False, "无效的 ZIP 文件格式"
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    def extract_skill_data(self, zip_buffer: BytesIO) -> Optional[Dict]:
        """
        从 ZIP 文件提取 Skill 数据
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            Skill 数据字典，失败返回 None
        """
        try:
            zip_buffer.seek(0)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                # 读取 skill.json
                skill_json = zf.read("skill.json").decode("utf-8")
                skill_data = json.loads(skill_json)
                
                # 验证必需字段
                if "base_id" not in skill_data:
                    return None
                
                return skill_data
        
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            return None
        except Exception as e:
            print(f"提取数据错误: {e}")
            return None
    
    def import_skill(self, zip_buffer: BytesIO) -> Optional[Dict]:
        """
        导入 Skill
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            导入的 Skill 数据字典
        """
        # 验证
        is_valid, message = self.validate_zip(zip_buffer)
        if not is_valid:
            print(f"验证失败: {message}")
            return None
        
        # 提取数据
        skill_data = self.extract_skill_data(zip_buffer)
        
        return skill_data
    
    def import_skill_from_file(self, file_path: str) -> Optional[Dict]:
        """
        从文件导入 Skill
        
        Args:
            file_path: ZIP 文件路径
            
        Returns:
            导入的 Skill 数据字典
        """
        with open(file_path, 'rb') as f:
            zip_buffer = BytesIO(f.read())
        
        return self.import_skill(zip_buffer)
    
    def extract_version_content(
        self,
        zip_buffer: BytesIO,
        version_id: int
    ) -> Optional[str]:
        """
        提取指定版本的内容
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            version_id: 版本号
            
        Returns:
            版本内容字符串
        """
        try:
            zip_buffer.seek(0)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                content_file = f"versions/version_{version_id}/content.md"
                
                if content_file in zf.namelist():
                    return zf.read(content_file).decode("utf-8")
                
                return None
        
        except Exception:
            return None
    
    def list_versions(self, zip_buffer: BytesIO) -> List[int]:
        """
        列出 ZIP 中的版本
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            版本号列表
        """
        versions = []
        
        try:
            zip_buffer.seek(0)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                for name in zf.namelist():
                    if name.startswith("versions/version_") and name.endswith("/metadata.json"):
                        version_id = name.split("/")[1].replace("version_", "")
                        if version_id.isdigit():
                            versions.append(int(version_id))
        
        except Exception:
            pass
        
        return sorted(versions)


class SkillZipHandler:
    """Skill ZIP 处理器（导出+导入）"""
    
    def __init__(
        self,
        export_path: Optional[str] = None,
        import_path: Optional[str] = None
    ):
        """
        初始化处理器
        
        Args:
            export_path: 导出目录
            import_path: 导入目录
        """
        self.exporter = SkillZipExporter(export_path)
        self.importer = SkillZipImporter(import_path)
    
    def export_skill(
        self,
        skill: Skill,
        **kwargs
    ) -> BytesIO:
        """
        导出 Skill
        
        Args:
            skill: Skill 对象
            **kwargs: 传递给导出器的参数
            
        Returns:
            ZIP 文件的 BytesIO 对象
        """
        return self.exporter.create_zip(skill, **kwargs)
    
    def export_skill_to_file(
        self,
        skill: Skill,
        file_path: str,
        **kwargs
    ) -> str:
        """
        导出 Skill 到文件
        
        Args:
            skill: Skill 对象
            file_path: 输出文件路径
            **kwargs: 传递给导出器的参数
            
        Returns:
            导出文件路径
        """
        return self.exporter.export_skill_to_file(skill, file_path, **kwargs)
    
    def import_skill(self, zip_buffer: BytesIO) -> Optional[Dict]:
        """
        导入 Skill
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            导入的 Skill 数据
        """
        return self.importer.import_skill(zip_buffer)
    
    def import_skill_from_file(self, file_path: str) -> Optional[Dict]:
        """
        从文件导入 Skill
        
        Args:
            file_path: ZIP 文件路径
            
        Returns:
            导入的 Skill 数据
        """
        return self.importer.import_skill_from_file(file_path)
    
    def validate_skill_zip(self, zip_buffer: BytesIO) -> Tuple[bool, str]:
        """
        验证 Skill ZIP 文件
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            
        Returns:
            (是否有效, 消息)
        """
        return self.importer.validate_zip(zip_buffer)
    
    async def import_and_save(
        self,
        zip_buffer: BytesIO,
        repository
    ) -> Dict:
        """
        导入 Skill 并保存到仓库
        
        Args:
            zip_buffer: ZIP 文件的 BytesIO 对象
            repository: Skill 仓储实例
            
        Returns:
            操作结果
        """
        try:
            # 导入数据
            skill_data = self.import_skill(zip_buffer)
            
            if not skill_data:
                return {
                    "success": False,
                    "message": "导入失败：无效的 ZIP 文件"
                }
            
            # 检查是否已存在
            existing = await repository.get_by_base_id(skill_data["base_id"])
            
            if existing:
                return {
                    "success": False,
                    "message": f"Skill '{skill_data['base_id']}' 已存在",
                    "existing_id": existing.get("base_id")
                }
            
            # 保存到仓库
            skill_id = await repository.create(skill_data)
            
            return {
                "success": True,
                "skill_id": skill_id,
                "base_id": skill_data["base_id"],
                "message": "导入成功"
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }
    
    def create_skill_from_data(self, skill_data: Dict) -> Skill:
        """
        从数据创建 Skill 对象
        
        Args:
            skill_data: Skill 数据字典
            
        Returns:
            Skill 对象
        """
        versions = []
        
        for v_data in skill_data.get("versions", []):
            status = v_data.get("status", "draft")
            if isinstance(status, str):
                status = SkillStatus(status)
            
            version = SkillVersion(
                version_id=v_data["version_id"],
                status=status,
                created_at=v_data.get("created_at", datetime.utcnow().isoformat()),
                created_by=v_data.get("created_by", "system"),
                source_session_id=v_data.get("source_session_id"),
                change_reason=v_data.get("change_reason")
            )
            versions.append(version)
        
        return Skill(
            base_id=skill_data["base_id"],
            active_version_id=skill_data.get("active_version_id", 0),
            created_at=skill_data.get("created_at", datetime.utcnow().isoformat()),
            versions=versions
        )


def export_skill_to_zip(skill: Skill, file_path: Optional[str] = None) -> Optional[BytesIO]:
    """
    便捷函数：导出 Skill 为 ZIP
    
    Args:
        skill: Skill 对象
        file_path: 可选的文件路径
        
    Returns:
        ZIP 文件的 BytesIO 对象（如果指定了 file_path 则返回 None）
    """
    handler = SkillZipHandler()
    
    if file_path:
        handler.export_skill_to_file(skill, file_path)
        return None
    
    return handler.export_skill(skill)


def import_skill_from_zip(zip_buffer: BytesIO) -> Optional[Skill]:
    """
    便捷函数：从 ZIP 导入 Skill
    
    Args:
        zip_buffer: ZIP 文件的 BytesIO 对象
        
    Returns:
        Skill 对象，失败返回 None
    """
    handler = SkillZipHandler()
    skill_data = handler.import_skill(zip_buffer)
    
    if skill_data:
        return handler.create_skill_from_data(skill_data)
    
    return None
