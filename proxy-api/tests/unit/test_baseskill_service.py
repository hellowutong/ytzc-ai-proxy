"""
BaseSkillService 单元测试
"""
import sys
from pathlib import Path
import pytest
import tempfile

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.baseskill_service import BaseSkillService, BASESKILL_PATH, CUSTOM_BASESKILL_PATH  # noqa: E402


class TestBaseSkillService:
    """BaseSkillService 测试类"""

    @pytest.fixture
    def temp_dirs(self):
        """创建临时目录用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system_path = Path(tmpdir) / "baseskill"
            custom_path = Path(tmpdir) / "data" / "baseskill"
            system_path.mkdir(parents=True, exist_ok=True)
            custom_path.mkdir(parents=True, exist_ok=True)
            
            service = BaseSkillService()
            service.system_path = system_path
            service.custom_path = custom_path
            
            yield service, system_path, custom_path

    def test_init(self):
        """测试初始化"""
        service = BaseSkillService()
        assert service.system_path == BASESKILL_PATH
        assert service.custom_path == CUSTOM_BASESKILL_PATH
        assert service._cache == {}
        assert service._enabled_cache == {}

    def test_parse_skill_md_basic(self, temp_dirs):
        """测试解析基本 SKILL.md"""
        service, _, _ = temp_dirs
        
        content = """name: Test Skill
description: A test skill
version: "1.0"
tags: [test, demo]
"""
        result = service._parse_skill_md(content)
        
        assert result["name"] == "Test Skill"
        assert result["description"] == "A test skill"
        assert result["version"] == "1.0"
        assert "test" in result["tags"]
        assert "demo" in result["tags"]

    def test_parse_skill_md_empty(self, temp_dirs):
        """测试解析空的 SKILL.md"""
        service, _, _ = temp_dirs
        
        result = service._parse_skill_md("")
        
        assert result["name"] == ""
        assert result["description"] == ""
        assert result["version"] == "1.0"
        assert result["tags"] == []

    def test_parse_skill_md_partial(self, temp_dirs):
        """测试解析部分 SKILL.md"""
        service, _, _ = temp_dirs
        
        content = """name: Partial Skill
version: "2.0"
"""
        result = service._parse_skill_md(content)
        
        assert result["name"] == "Partial Skill"
        assert result["description"] == ""
        assert result["version"] == "2.0"

    def test_parse_skill_md_with_quotes(self, temp_dirs):
        """测试解析带引号的版本号"""
        service, _, _ = temp_dirs
        
        content = '''name: Quoted Version
version: "3.5.1"
'''
        result = service._parse_skill_md(content)
        
        assert result["version"] == "3.5.1"

    def test_read_template_file_exists(self, temp_dirs):
        """测试读取存在的模板文件"""
        service, system_path, _ = temp_dirs
        
        test_file = system_path / "test.md"
        test_file.write_text("Test content", encoding="utf-8")
        
        result = service._read_template_file(system_path, "test.md")
        
        assert result == "Test content"

    def test_read_template_file_not_exists(self, temp_dirs):
        """测试读取不存在的模板文件"""
        service, system_path, _ = temp_dirs
        
        result = service._read_template_file(system_path, "nonexistent.md")
        
        assert result is None

    def test_read_template_file_empty(self, temp_dirs):
        """测试读取空的模板文件"""
        service, system_path, _ = temp_dirs
        
        empty_file = system_path / "empty.md"
        empty_file.write_text("", encoding="utf-8")
        
        result = service._read_template_file(system_path, "empty.md")
        
        assert result == ""

    def test_disabled_set_empty(self, temp_dirs):
        """测试空的禁用集合"""
        service, _, custom_path = temp_dirs
        
        result = service._disabled_set
        
        assert result == set()

    def test_disabled_set_with_disabled(self, temp_dirs):
        """测试有禁用项的集合"""
        service, _, custom_path = temp_dirs
        
        disabled_file = custom_path / ".disabled"
        disabled_file.write_text("skill-1\nskill-2\n", encoding="utf-8")
        
        result = service._disabled_set
        
        assert "skill-1" in result
        assert "skill-2" in result

    def test_disabled_set_ignores_empty_lines(self, temp_dirs):
        """测试忽略空行"""
        service, _, custom_path = temp_dirs
        
        disabled_file = custom_path / ".disabled"
        disabled_file.write_text("skill-1\n\nskill-2\n  \n", encoding="utf-8")
        
        result = service._disabled_set
        
        assert len(result) == 2

    def test_save_disabled_set(self, temp_dirs):
        """测试保存禁用集合"""
        service, _, custom_path = temp_dirs
        
        disabled_file = custom_path / ".disabled"
        disabled_file.write_text("skill-1\nskill-2\n", encoding="utf-8")
        
        service._save_disabled_set()
        
        assert disabled_file.exists()

    def test_create_skill(self, temp_dirs):
        """测试创建 skill"""
        service, _, custom_path = temp_dirs
        
        data = {
            "name": "new-skill",
            "skill_md": "# New Skill\n\n## Description\n\nTest",
            "prompt_template": "Hello {{name}}",
            "rules_yaml": "rules:\n  - test"
        }
        
        result = service.create(data)
        
        assert result is not None
        assert result["id"] == "custom-new-skill"
        
        skill_path = custom_path / "new-skill"
        assert (skill_path / "SKILL.md").exists()
        assert (skill_path / "prompt-template.md").exists()
        assert (skill_path / "rules.yaml").exists()

    def test_create_skill_with_defaults(self, temp_dirs):
        """测试创建带默认值的 skill"""
        service, _, custom_path = temp_dirs
        
        data = {"name": "minimal-skill"}
        
        result = service.create(data)
        
        assert result is not None
        assert result["prompt_template"] == ""
        assert result["rules"] == ""

    def test_update_skill(self, temp_dirs):
        """测试更新 skill"""
        service, _, custom_path = temp_dirs
        
        skill_path = custom_path / "update-test"
        skill_path.mkdir(parents=True, exist_ok=True)
        (skill_path / "SKILL.md").write_text('name: Original\n', encoding="utf-8")
        (skill_path / "prompt-template.md").write_text('Original template', encoding="utf-8")
        
        data = {"skill_md": 'name: Updated\n', "prompt_template": "Updated template"}
        
        result = service.update("custom-update-test", data)
        
        assert result is not None
        assert (skill_path / "SKILL.md").read_text(encoding="utf-8") == 'name: Updated\n'
        assert (skill_path / "prompt-template.md").read_text(encoding="utf-8") == "Updated template"

    def test_update_system_skill_fails(self, temp_dirs):
        """测试更新系统 skill 失败"""
        service, system_path, _ = temp_dirs
        
        skill_path = system_path / "system-skill"
        skill_path.mkdir(parents=True, exist_ok=True)
        
        with pytest.raises(ValueError):
            service.update("system-system-skill", {"skill_md": "New"})

    def test_update_nonexistent_skill(self, temp_dirs):
        """测试更新不存在的 skill"""
        service, _, _ = temp_dirs
        
        result = service.update("custom-nonexistent", {"skill_md": "New"})
        
        assert result is None

    def test_delete_skill(self, temp_dirs):
        """测试删除 skill"""
        service, _, custom_path = temp_dirs
        
        skill_path = custom_path / "delete-test"
        skill_path.mkdir(parents=True, exist_ok=True)
        (skill_path / "SKILL.md").write_text("Test", encoding="utf-8")
        
        result = service.delete("custom-delete-test")
        
        assert result is True
        assert not skill_path.exists()

    def test_delete_system_skill_fails(self, temp_dirs):
        """测试删除系统 skill 失败"""
        service, system_path, _ = temp_dirs
        
        result = service.delete("system-test")
        
        assert result is False

    def test_delete_nonexistent_skill(self, temp_dirs):
        """测试删除不存在的 skill"""
        service, _, _ = temp_dirs
        
        result = service.delete("custom-nonexistent")
        
        assert result is False

    def test_enable_skill(self, temp_dirs):
        """测试启用 skill"""
        service, _, custom_path = temp_dirs
        
        result = service.enable("custom-test-skill")
        
        assert result is True

    def test_enable_system_skill_fails(self, temp_dirs):
        """测试启用系统 skill 失败"""
        service, _, _ = temp_dirs
        
        result = service.enable("system-test")
        
        assert result is False

    def test_disable_skill(self, temp_dirs):
        """测试禁用 skill"""
        service, _, custom_path = temp_dirs
        
        result = service.disable("custom-test-skill")
        
        assert result is True

    def test_disable_system_skill_fails(self, temp_dirs):
        """测试禁用系统 skill 失败"""
        service, _, _ = temp_dirs
        
        result = service.disable("system-test")
        
        assert result is False

    def test_reload(self, temp_dirs):
        """测试重新加载"""
        service, _, custom_path = temp_dirs
        
        skill_path = custom_path / "reload-test"
        skill_path.mkdir(parents=True, exist_ok=True)
        (skill_path / "SKILL.md").write_text('name: Reload Test\n', encoding="utf-8")
        
        result = service.reload()
        
        assert "message" in result
        assert "count" in result
        assert service._cache == {}

    def test_service_singleton(self):
        """测试服务是单例"""
        from app.services.baseskill_service import service
        assert isinstance(service, BaseSkillService)
