"""
自定义异常类 - Skill相关异常定义
"""


class SkillError(Exception):
    """Skill基础异常类"""
    
    def __init__(self, message: str, category: str = None, name: str = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.name = name
    
    def __str__(self):
        if self.category and self.name:
            return f"[{self.category}/{self.name}] {self.message}"
        return self.message


class SkillNotFoundError(SkillError):
    """Skill未找到异常"""
    
    def __init__(self, category: str, name: str):
        super().__init__(
            message=f"Skill未找到: {category}/{name}",
            category=category,
            name=name
        )


class SkillValidationError(SkillError):
    """Skill验证失败异常"""
    
    def __init__(
        self,
        message: str,
        category: str = None,
        name: str = None,
        errors: list = None
    ):
        super().__init__(message, category, name)
        self.errors = errors or []
    
    def __str__(self):
        base = super().__str__()
        if self.errors:
            error_details = "\n".join(f"  - {e}" for e in self.errors)
            return f"{base}\n验证错误详情:\n{error_details}"
        return base


class SkillExecutionError(SkillError):
    """Skill执行失败异常"""
    
    def __init__(
        self,
        message: str,
        category: str = None,
        name: str = None,
        input_data: dict = None,
        output_data: dict = None
    ):
        super().__init__(message, category, name)
        self.input_data = input_data
        self.output_data = output_data


class SkillSchemaError(SkillValidationError):
    """Skill Schema验证失败异常"""
    
    def __init__(
        self,
        message: str,
        category: str = None,
        name: str = None,
        schema_type: str = None,
        validation_errors: list = None
    ):
        super().__init__(message, category, name, validation_errors)
        self.schema_type = schema_type


class SkillLoadError(SkillError):
    """Skill加载失败异常"""
    
    def __init__(
        self,
        message: str,
        category: str = None,
        name: str = None,
        file_path: str = None
    ):
        super().__init__(message, category, name)
        self.file_path = file_path
