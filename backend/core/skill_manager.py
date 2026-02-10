"""
Skill管理器 - 负责Skill的发现、加载、验证、执行、重载
"""

import os
import sys
import time
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .skill_validator import SkillValidator, SkillMetadata
from .exceptions import (
    SkillNotFoundError,
    SkillValidationError,
    SkillExecutionError,
    SkillLoadError
)

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class SkillInfo:
    """Skill信息结构"""
    category: str
    name: str
    metadata: SkillMetadata
    is_custom: bool
    version: str
    file_path: str
    has_py_file: bool
    execute_func: Optional[Callable] = None
    markdown_content: str = ""
    loaded_at: datetime = field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        """获取完整名称 category/name"""
        return f"{self.category}/{self.name}"


@dataclass
class SkillListItem:
    """Skill列表项（用于前端展示）"""
    category: str
    name: str
    description: str
    type: str
    priority: int
    version: str
    is_custom: bool
    has_py_file: bool


class SkillManager:
    """Skill管理器"""
    
    def __init__(self, config_manager=None, skill_base_path: str = "../skill"):
        """
        初始化Skill管理器
        
        Args:
            config_manager: 配置管理器实例
            skill_base_path: Skill根目录路径
        """
        self._skills: Dict[str, SkillInfo] = {}  # full_name -> SkillInfo
        self._config_manager = config_manager
        self._skill_base_path = Path(skill_base_path).resolve()
        self._validator = SkillValidator()
        
        # 加载所有Skills
        self._load_all_skills()
        logger.info(f"Skill管理器初始化完成，共加载 {len(self._skills)} 个Skill")
    
    def _load_all_skills(self):
        """遍历skill/system/和skill/custom/目录加载所有Skill"""
        # 系统Skill
        system_path = self._skill_base_path / "system"
        if system_path.exists():
            self._load_skills_from_dir(system_path, is_custom=False)
        
        # 自定义Skill
        custom_path = self._skill_base_path / "custom"
        if custom_path.exists():
            self._load_skills_from_dir(custom_path, is_custom=True)
    
    def _load_skills_from_dir(self, base_dir: Path, is_custom: bool):
        """
        从目录加载Skills
        
        Args:
            base_dir: 基础目录（system或custom）
            is_custom: 是否为自定义Skill
        """
        # 遍历所有子目录查找SKILL.md
        for skill_md in base_dir.rglob("SKILL.md"):
            try:
                self._load_skill_from_file(skill_md, is_custom)
            except Exception as e:
                logger.warning(f"加载Skill失败 {skill_md}: {e}")
    
    def _load_skill_from_file(self, file_path: Path, is_custom: bool):
        """
        从文件加载单个Skill
        
        Args:
            file_path: SKILL.md文件路径
            is_custom: 是否为自定义Skill
        """
        # 读取文件内容
        content = file_path.read_text(encoding='utf-8')
        
        # 解析并验证
        try:
            metadata, markdown_content = self._validator.validate_skill_file(
                content,
                category=None,
                name=None
            )
        except SkillValidationError:
            # 重新抛出带路径信息
            relative_path = file_path.relative_to(self._skill_base_path)
            parts = list(relative_path.parts)
            category = parts[0] if parts else "unknown"
            name = metadata.name if hasattr(metadata, 'name') else file_path.parent.name
            raise SkillLoadError(
                message=f"Skill文件格式错误: {file_path}",
                category=category,
                name=name,
                file_path=str(file_path)
            )
        
        # 从路径推断category和version
        relative_path = file_path.relative_to(self._skill_base_path)
        parts = list(relative_path.parts)
        
        # 格式: system/category/v1/name/SKILL.md 或 custom/category/v1/name/SKILL.md
        if len(parts) >= 4:
            category = parts[1]  # router, knowledge等
            version = parts[2]   # v1
            name = parts[3]      # Skill目录名
        else:
            # 简化为直接使用metadata中的name
            category = parts[1] if len(parts) > 1 else "unknown"
            version = "v1"
            name = metadata.name
        
        # 检查是否有execute.py
        execute_py_path = file_path.parent / "execute.py"
        has_py_file = execute_py_path.exists()
        
        # 动态导入execute.py（如果存在）
        execute_func = None
        if has_py_file:
            execute_func = self._load_execute_function(execute_py_path, name)
        
        # 创建SkillInfo
        skill_info = SkillInfo(
            category=category,
            name=name,
            metadata=metadata,
            is_custom=is_custom,
            version=version,
            file_path=str(file_path),
            has_py_file=has_py_file,
            execute_func=execute_func,
            markdown_content=markdown_content
        )
        
        # 存储到缓存
        self._skills[skill_info.full_name] = skill_info
        logger.debug(f"已加载Skill: {skill_info.full_name} (type={metadata.type})")
    
    def _load_execute_function(self, file_path: Path, skill_name: str) -> Optional[Callable]:
        """
        动态加载execute.py中的execute函数
        
        Args:
            file_path: execute.py路径
            skill_name: Skill名称
            
        Returns:
            execute函数或None
        """
        try:
            # 创建模块规范
            module_name = f"skill_{skill_name}_{file_path.parent.name}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            
            # 添加到sys.modules以防止重复导入
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 获取execute函数
            if hasattr(module, 'execute'):
                return module.execute
            else:
                logger.warning(f"execute.py缺少execute函数: {file_path}")
                return None
        except Exception as e:
            logger.warning(f"加载execute.py失败 {file_path}: {e}")
            return None
    
    def get_skill(self, category: str, name: str) -> Optional[SkillInfo]:
        """
        获取Skill信息
        
        Args:
            category: Skill分类
            name: Skill名称
            
        Returns:
            SkillInfo或None
        """
        full_name = f"{category}/{name}"
        return self._skills.get(full_name)
    
    def get_skill_list(self) -> List[SkillListItem]:
        """
        获取Skill列表（用于前端展示）
        
        Returns:
            Skill列表
        """
        return [
            SkillListItem(
                category=skill.category,
                name=skill.name,
                description=skill.metadata.description,
                type=skill.metadata.type,
                priority=skill.metadata.priority,
                version=skill.version,
                is_custom=skill.is_custom,
                has_py_file=skill.has_py_file
            )
            for skill in self._skills.values()
        ]
    
    async def execute(
        self,
        category: str,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行Skill
        
        Args:
            category: Skill分类
            name: Skill名称
            **kwargs: 输入参数
            
        Returns:
            执行结果字典
            
        Raises:
            SkillNotFoundError: Skill不存在
            SkillValidationError: 输入验证失败
            SkillExecutionError: 执行失败
        """
        # 1. 查找Skill
        skill = self.get_skill(category, name)
        if not skill:
            raise SkillNotFoundError(category, name)
        
        start_time = time.time()
        logger.debug(f"开始执行Skill: {skill.full_name}")
        
        # 2. 验证输入参数
        if skill.metadata.input_schema:
            try:
                self._validator.validate_input(
                    kwargs,
                    skill.metadata.input_schema,
                    category,
                    name
                )
            except Exception as e:
                logger.warning(f"Skill输入验证失败 {skill.full_name}: {e}")
                # 输入验证失败不阻止执行，记录警告
        
        # 3. 执行Skill
        try:
            if skill.execute_func:
                # 调用execute.py中的函数
                if hasattr(skill.execute_func, '__code__') and 'async' in skill.execute_func.__code__.co_flags:
                    result = await skill.execute_func(**kwargs)
                else:
                    result = skill.execute_func(**kwargs)
            else:
                # 没有execute.py，根据type执行默认逻辑
                result = self._execute_default(skill, **kwargs)
            
            # 确保结果是字典
            if not isinstance(result, dict):
                result = {"result": result}
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Skill执行失败 {skill.full_name}: {e}")
            raise SkillExecutionError(
                message=f"Skill执行失败: {e}",
                category=category,
                name=name,
                input_data=kwargs,
                output_data={}
            )
        
        # 4. 验证输出结果
        if skill.metadata.output_schema:
            try:
                self._validator.validate_output(
                    result,
                    skill.metadata.output_schema,
                    category,
                    name
                )
            except Exception as e:
                logger.warning(f"Skill输出验证失败 {skill.full_name}: {e}")
                # 输出验证失败不阻止返回结果，记录警告
        
        # 5. 添加执行元信息
        duration_ms = int((time.time() - start_time) * 1000)
        result["_execution_meta"] = {
            "skill": skill.full_name,
            "type": skill.metadata.type,
            "duration_ms": duration_ms,
            "executed_at": datetime.now().isoformat()
        }
        
        logger.debug(f"Skill执行完成: {skill.full_name}, 耗时{duration_ms}ms")
        return result
    
    def _execute_default(self, skill: SkillInfo, **kwargs) -> Dict[str, Any]:
        """
        默认执行逻辑（当没有execute.py时）
        
        Args:
            skill: Skill信息
            **kwargs: 输入参数
            
        Returns:
            默认执行结果
        """
        skill_type = skill.metadata.type
        
        if skill_type == "rule-based":
            # 规则型Skill：从markdown中解析规则
            return self._execute_rule_based(skill, **kwargs)
        elif skill_type == "llm-based":
            # LLM型Skill：需要外部服务调用
            return {
                "status": "pending",
                "message": f"LLM-based Skill需要通过外部服务调用",
                "skill_type": skill_type
            }
        else:
            # 混合型或其他
            return {
                "status": "not_implemented",
                "message": f"Skill类型 {skill_type} 需要实现execute.py",
                "skill_type": skill_type
            }
    
    def _execute_rule_based(self, skill: SkillInfo, **kwargs) -> Dict[str, Any]:
        """
        执行基于规则的Skill
        
        Args:
            skill: Skill信息
            **kwargs: 输入参数
            
        Returns:
            规则匹配结果
        """
        # 简单的关键词匹配逻辑
        user_input = kwargs.get("user_input", "")
        
        # 从metadata的rules中查找匹配
        if skill.metadata.rules:
            for rule in skill.metadata.rules:
                keywords = rule.get("keywords", [])
                if any(kw in user_input for kw in keywords):
                    return {
                        "matched": True,
                        "rule": rule.get("name", "unknown"),
                        "target": rule.get("target"),
                        "confidence": rule.get("confidence", 1.0)
                    }
        
        return {"matched": False, "target": None}
    
    def reload_skill(self, category: str, name: str) -> bool:
        """
        重载单个Skill
        
        Args:
            category: Skill分类
            name: Skill名称
            
        Returns:
            是否重载成功
        """
        full_name = f"{category}/{name}"
        skill = self._skills.get(full_name)
        
        if not skill:
            logger.warning(f"重载Skill失败，未找到: {full_name}")
            return False
        
        try:
            file_path = Path(skill.file_path)
            is_custom = skill.is_custom
            
            # 从缓存移除
            del self._skills[full_name]
            
            # 重新加载
            self._load_skill_from_file(file_path, is_custom)
            
            logger.info(f"Skill重载成功: {full_name}")
            return True
        except Exception as e:
            logger.error(f"Skill重载失败 {full_name}: {e}")
            return False
    
    def reload_all(self) -> Dict[str, int]:
        """
        重载所有Skill
        
        Returns:
            统计信息 {"success": 成功数, "failed": 失败数, "total": 总数}
        """
        # 保存当前列表
        old_skills = list(self._skills.values())
        
        # 清空缓存
        self._skills.clear()
        
        success = 0
        failed = 0
        
        # 重新加载
        for skill in old_skills:
            try:
                self._load_skill_from_file(Path(skill.file_path), skill.is_custom)
                success += 1
            except Exception as e:
                logger.error(f"重载Skill失败 {skill.full_name}: {e}")
                failed += 1
        
        # 查找新增的Skill
        self._load_all_skills()
        
        total = len(self._skills)
        logger.info(f"重载完成: 成功{success}, 失败{failed}, 总计{total}")
        
        return {
            "success": success,
            "failed": failed,
            "total": total
        }
    
    def get_skill_content(self, category: str, name: str) -> Optional[str]:
        """
        获取Skill原始内容
        
        Args:
            category: Skill分类
            name: Skill名称
            
        Returns:
            SKILL.md内容或None
        """
        skill = self.get_skill(category, name)
        if not skill:
            return None
        
        try:
            with open(skill.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取Skill文件失败 {skill.file_path}: {e}")
            return None
    
    def save_skill_content(
        self,
        category: str,
        name: str,
        content: str,
        is_custom: bool = True
    ) -> bool:
        """
        保存Skill内容（仅支持custom目录）
        
        Args:
            category: Skill分类
            name: Skill名称
            content: 新的SKILL.md内容
            is_custom: 是否为自定义Skill
            
        Returns:
            是否保存成功
        """
        if not is_custom:
            logger.error("不能修改系统Skill")
            return False
        
        try:
            # 验证新内容
            metadata, _ = self._validator.validate_skill_file(content)
            
            # 构建保存路径
            skill_dir = self._skill_base_path / "custom" / category / "v1" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            file_path = skill_dir / "SKILL.md"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 重新加载
            full_name = f"{category}/{name}"
            if full_name in self._skills:
                self.reload_skill(category, name)
            else:
                self._load_skill_from_file(file_path, is_custom=True)
            
            logger.info(f"Skill保存成功: {full_name}")
            return True
        except Exception as e:
            logger.error(f"保存Skill失败: {e}")
            return False
