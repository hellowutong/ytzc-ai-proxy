"""
TDD 测试 - Skill ZIP 导入/导出功能
测试日期: 2026-02-02
"""
import sys
import os
import zipfile
import tempfile
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from io import BytesIO

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSkillZipExporter:
    """Skill ZIP 导出测试类"""

    @pytest.fixture
    def mock_skill(self):
        """创建模拟 Skill"""
        from app.domain.models.skill import Skill, SkillVersion, SkillStatus
        
        return Skill(
            base_id="test-skill-001",
            active_version_id=1,
            versions=[
                SkillVersion(
                    version_id=1,
                    status=SkillStatus.PUBLISHED,
                    created_at=datetime.utcnow().isoformat(),
                    created_by="test-user",
                    source_session_id="session-001",
                    change_reason="初始版本",
                )
            ],
            created_at=datetime.utcnow().isoformat()
        )

    @pytest.fixture
    def exporter(self):
        """创建导出器实例"""
        from app.services.skill_zip_handler import SkillZipExporter
        return SkillZipExporter()

    def test_exporter_class_exists(self, exporter):
        """测试导出器类存在"""
        assert exporter is not None

    def test_create_zip_structure(self, exporter, mock_skill):
        """测试创建 ZIP 结构"""
        zip_buffer = exporter.create_zip(mock_skill)
        
        assert zip_buffer is not None
        assert isinstance(zip_buffer, BytesIO)
        assert len(zip_buffer.getvalue()) > 0

    def test_zip_contains_required_files(self, exporter, mock_skill):
        """测试 ZIP 包含必需文件"""
        zip_buffer = exporter.create_zip(mock_skill)
        zip_buffer.seek(0)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            
            assert "skill.json" in file_list
            assert any(f.startswith("versions/version_") for f in file_list)
            assert any(f.endswith("metadata.json") for f in file_list)

    def test_skill_json_content(self, exporter, mock_skill):
        """测试 skill.json 内容"""
        zip_buffer = exporter.create_zip(mock_skill)
        zip_buffer.seek(0)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            skill_json = zf.read("skill.json").decode("utf-8")
            
            assert "base_id" in skill_json
            assert "test-skill-001" in skill_json
            assert "versions" in skill_json

    def test_export_with_empty_versions(self, exporter):
        """测试导出空版本 Skill"""
        from app.domain.models.skill import Skill
        
        skill = Skill(
            base_id="empty-skill",
            active_version_id=0,
            versions=[]
        )
        
        zip_buffer = exporter.create_zip(skill)
        
        assert zip_buffer is not None
        assert len(zip_buffer.getvalue()) > 0

    def test_export_custom_prompt_template(self, exporter, mock_skill):
        """测试导出自定义 Prompt 模板"""
        zip_buffer = exporter.create_zip(
            mock_skill,
            include_prompt_template=True
        )
        
        zip_buffer.seek(0)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()
            assert "prompt-template.md" in file_list

    def test_export_with_examples(self, exporter, mock_skill):
        """测试导出包含示例"""
        zip_buffer = exporter.create_zip(
            mock_skill,
            include_examples=True
        )
        
        zip_buffer.seek(0)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            assert "examples.json" in zf.namelist()


class TestSkillZipImporter:
    """Skill ZIP 导入测试类"""

    @pytest.fixture
    def importer(self):
        """创建导入器实例"""
        from app.services.skill_zip_handler import SkillZipImporter
        return SkillZipImporter()

    @pytest.fixture
    def valid_zip_buffer(self):
        """创建有效的 ZIP 文件"""
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            import json
            skill_data = {
                "base_id": "imported-skill",
                "active_version_id": 1,
                "versions": [{
                    "version_id": 1,
                    "status": "draft",
                    "created_at": "2026-02-02T10:00:00",
                    "created_by": "import",
                    "source_session_id": None,
                    "change_reason": "imported"
                }],
                "created_at": "2026-02-02T10:00:00"
            }
            zf.writestr("skill.json", json.dumps(skill_data, ensure_ascii=False))
            zf.writestr("versions/version_1/content.md", "# 导入的技能内容")
        
        buffer.seek(0)
        return buffer

    def test_importer_class_exists(self, importer):
        """测试导入器类存在"""
        assert importer is not None

    def test_validate_valid_zip(self, importer, valid_zip_buffer):
        """测试验证有效 ZIP"""
        is_valid, message = importer.validate_zip(valid_zip_buffer)
        
        assert is_valid is True
        assert "有效" in message or "valid" in message.lower()

    def test_validate_invalid_zip(self, importer):
        """测试验证无效 ZIP"""
        invalid_buffer = BytesIO(b"not a valid zip")
        
        is_valid, message = importer.validate_zip(invalid_buffer)
        
        assert is_valid is False
        assert "无效" in message or "invalid" in message.lower()

    def test_validate_empty_zip(self, importer):
        """测试验证空 ZIP"""
        empty_buffer = BytesIO()
        
        is_valid, message = importer.validate_zip(empty_buffer)
        
        assert is_valid is False

    def test_validate_zip_without_skill_json(self, importer):
        """测试验证缺少 skill.json 的 ZIP"""
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("other_file.txt", "content")
        
        buffer.seek(0)
        is_valid, message = importer.validate_zip(buffer)
        
        assert is_valid is False
        assert "skill.json" in message

    def test_extract_skill_data(self, importer, valid_zip_buffer):
        """测试提取 Skill 数据"""
        skill_data = importer.extract_skill_data(valid_zip_buffer)
        
        assert skill_data is not None
        assert skill_data["base_id"] == "imported-skill"
        assert "versions" in skill_data


class TestSkillZipHandlerIntegration:
    """Skill ZIP 处理集成测试"""

    @pytest.fixture
    def handler(self):
        """创建处理器实例"""
        from app.services.skill_zip_handler import SkillZipHandler
        return SkillZipHandler()

    @pytest.fixture
    def mock_skill(self):
        """创建模拟 Skill"""
        from app.domain.models.skill import Skill, SkillVersion, SkillStatus
        
        return Skill(
            base_id="roundtrip-test",
            active_version_id=1,
            versions=[
                SkillVersion(
                    version_id=1,
                    status=SkillStatus.PUBLISHED,
                    created_at=datetime.utcnow().isoformat(),
                    created_by="test",
                    source_session_id="session-001",
                    change_reason="测试版本",
                )
            ],
            created_at=datetime.utcnow().isoformat()
        )

    def test_roundtrip_export_import(self, handler, mock_skill):
        """测试导出后导入（数据一致性）"""
        # 导出
        zip_buffer = handler.export_skill(mock_skill)
        
        # 导入
        imported_data = handler.import_skill(zip_buffer)
        
        assert imported_data is not None
        assert imported_data["base_id"] == mock_skill.base_id

    def test_export_to_file(self, handler, mock_skill):
        """测试导出到文件"""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            temp_path = f.name
        
        try:
            handler.export_skill_to_file(mock_skill, temp_path)
            
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
            
            # 验证文件是有效的 ZIP
            with zipfile.ZipFile(temp_path, 'r') as zf:
                assert "skill.json" in zf.namelist()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_import_from_file(self, handler, mock_skill):
        """测试从文件导入"""
        # 先导出到文件
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            temp_path = f.name
        
        try:
            handler.export_skill_to_file(mock_skill, temp_path)
            
            # 从文件导入
            imported_data = handler.import_skill_from_file(temp_path)
            
            assert imported_data is not None
            assert imported_data["base_id"] == mock_skill.base_id
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_import_with_repository(self, handler, mock_skill):
        """测试导入并保存到仓库"""
        mock_repository = AsyncMock()
        mock_repository.create = AsyncMock(return_value="new-skill-id")
        mock_repository.get_by_base_id = AsyncMock(return_value=None)
        
        zip_buffer = handler.export_skill(mock_skill)
        
        result = await handler.import_and_save(zip_buffer, mock_repository)
        
        assert result["success"] is True
        assert "skill_id" in result


class TestSkillZipHandlerEdgeCases:
    """Skill ZIP 处理边界条件测试"""

    @pytest.fixture
    def handler(self):
        from app.services.skill_zip_handler import SkillZipHandler
        return SkillZipHandler()

    def test_corrupted_zip_file(self, handler):
        """测试损坏的 ZIP 文件"""
        corrupted_buffer = BytesIO(b"corrupted zip content")
        
        is_valid, message = handler.validate_skill_zip(corrupted_buffer)
        
        assert is_valid is False

    def test_zip_with_invalid_json(self, handler):
        """测试包含无效 JSON 的 ZIP"""
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("skill.json", "not valid json {{{")
        
        buffer.seek(0)
        skill_data = handler.importer.extract_skill_data(buffer)
        
        assert skill_data is None

    def test_empty_base_id(self, handler):
        """测试空 base_id 的 Skill"""
        from app.domain.models.skill import Skill
        
        skill = Skill(
            base_id="",
            active_version_id=0,
            versions=[]
        )
        
        zip_buffer = handler.export_skill(skill)
        
        assert zip_buffer is not None

    def test_special_characters_in_base_id(self, handler):
        """测试 base_id 包含特殊字符"""
        from app.domain.models.skill import Skill
        
        skill = Skill(
            base_id="test-skill_v1.0",
            active_version_id=0,
            versions=[]
        )
        
        zip_buffer = handler.export_skill(skill)
        
        assert zip_buffer is not None
        
        # 验证可以正常导入
        skill_data = handler.importer.extract_skill_data(zip_buffer)
        assert skill_data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
