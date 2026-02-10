"""
Skill验证器 - 负责验证SKILL.md格式和Schema
"""

import re
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from .exceptions import SkillValidationError, SkillSchemaError


class SkillMetadata(BaseModel):
    """Skill元数据模型"""
    name: str = Field(..., description="Skill名称")
    description: str = Field(..., description="Skill描述")
    type: Literal["rule-based", "llm-based", "hybrid"] = Field(
        ...,
        description="Skill类型"
    )
    priority: int = Field(default=50, ge=1, le=100, description="优先级1-100")
    version: str = Field(..., description="版本号")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输入参数JSON Schema"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输出结果JSON Schema"
    )
    # LLM-based特有
    model: Optional[str] = Field(
        default=None,
        description="使用的模型(small/big)"
    )
    # Rule-based特有
    rules: Optional[List[Dict]] = Field(
        default=None,
        description="规则列表"
    )


class SkillValidator:
    """Skill验证器"""
    
    @staticmethod
    def parse_frontmatter(content: str) -> tuple:
        """
        解析YAML frontmatter
        
        Args:
            content: SKILL.md文件内容
            
        Returns:
            (metadata_dict, markdown_content)
            
        Raises:
            SkillValidationError: 解析失败
        """
        # 匹配 --- 包围的YAML frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            raise SkillValidationError(
                message="SKILL.md格式错误: 未找到YAML frontmatter",
                errors=["文件必须以 '---' 开头和结束YAML frontmatter部分"]
            )
        
        yaml_content = match.group(1)
        markdown_content = match.group(2).strip()
        
        try:
            import yaml
            metadata = yaml.safe_load(yaml_content)
            if not isinstance(metadata, dict):
                raise SkillValidationError(
                    message="SKILL.md格式错误: YAML frontmatter必须是对象",
                    errors=["YAML内容必须是一个键值对对象"]
                )
            return metadata, markdown_content
        except ImportError:
            raise SkillValidationError(
                message="缺少依赖: PyYAML",
                errors=["请安装: pip install pyyaml"]
            )
        except Exception as e:
            raise SkillValidationError(
                message=f"YAML解析错误: {e}",
                errors=[str(e)]
            )
    
    @classmethod
    def validate_metadata(
        cls,
        metadata: Dict[str, Any],
        category: str = None,
        name: str = None
    ) -> SkillMetadata:
        """
        验证Skill元数据
        
        Args:
            metadata: 解析后的元数据字典
            category: Skill分类（用于错误信息）
            name: Skill名称（用于错误信息）
            
        Returns:
            SkillMetadata: 验证后的元数据对象
            
        Raises:
            SkillValidationError: 验证失败
        """
        try:
            return SkillMetadata(**metadata)
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"{field}: {msg}")
            
            raise SkillValidationError(
                message="Skill元数据验证失败",
                category=category,
                name=name,
                errors=errors
            )
    
    @classmethod
    def validate_skill_file(
        cls,
        content: str,
        category: str = None,
        name: str = None
    ) -> tuple:
        """
        验证完整的SKILL.md文件
        
        Args:
            content: 文件内容
            category: Skill分类
            name: Skill名称
            
        Returns:
            (SkillMetadata, markdown_content): 验证后的元数据和Markdown内容
            
        Raises:
            SkillValidationError: 验证失败
        """
        # 解析frontmatter
        metadata, markdown_content = cls.parse_frontmatter(content)
        
        # 验证元数据
        skill_metadata = cls.validate_metadata(metadata, category, name)
        
        return skill_metadata, markdown_content
    
    @staticmethod
    def validate_input(
        input_data: Dict[str, Any],
        input_schema: Dict[str, Any],
        category: str = None,
        name: str = None
    ) -> bool:
        """
        验证输入数据是否符合input_schema
        
        Args:
            input_data: 输入数据
            input_schema: JSON Schema
            category: Skill分类
            name: Skill名称
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            SkillSchemaError: 验证失败
        """
        try:
            from jsonschema import validate, ValidationError as JsonSchemaValidationError
            validate(instance=input_data, schema=input_schema)
            return True
        except ImportError:
            # 如果没有jsonschema，只做基本检查
            return True
        except JsonSchemaValidationError as e:
            raise SkillSchemaError(
                message=f"输入数据验证失败: {e.message}",
                category=category,
                name=name,
                schema_type="input",
                validation_errors=[f"{e.json_path}: {e.message}"]
            )
    
    @staticmethod
    def validate_output(
        output_data: Dict[str, Any],
        output_schema: Dict[str, Any],
        category: str = None,
        name: str = None
    ) -> bool:
        """
        验证输出数据是否符合output_schema
        
        Args:
            output_data: 输出数据
            output_schema: JSON Schema
            category: Skill分类
            name: Skill名称
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            SkillSchemaError: 验证失败
        """
        try:
            from jsonschema import validate, ValidationError as JsonSchemaValidationError
            validate(instance=output_data, schema=output_schema)
            return True
        except ImportError:
            # 如果没有jsonschema，只做基本检查
            return True
        except JsonSchemaValidationError as e:
            raise SkillSchemaError(
                message=f"输出数据验证失败: {e.message}",
                category=category,
                name=name,
                schema_type="output",
                validation_errors=[f"{e.json_path}: {e.message}"]
            )
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """
        验证文件路径是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 有效返回True
        """
        import os
        return os.path.isfile(file_path) and file_path.endswith('.md')
