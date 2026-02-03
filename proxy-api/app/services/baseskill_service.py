import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

BASESKILL_PATH = Path("./baseskill")
CUSTOM_BASESKILL_PATH = Path("./data/baseskill")


class BaseSkillService:
    def __init__(self):
        self.system_path = BASESKILL_PATH
        self.custom_path = CUSTOM_BASESKILL_PATH
        self._cache = {}
        self._enabled_cache = {}

    def _ensure_directories(self):
        self.system_path.mkdir(exist_ok=True)
        self.custom_path.mkdir(parents=True, exist_ok=True)

    def _parse_skill_md(self, content: str) -> Dict:
        result = {"name": "", "description": "", "version": "1.0", "tags": []}
        for line in content.split("\n"):
            if line.startswith("name:"):
                result["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                result["description"] = line.split(":", 1)[1].strip()
            elif line.startswith("version:"):
                result["version"] = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("tags:"):
                tags_str = line.split(":", 1)[1].strip()
                result["tags"] = [t.strip().strip("[]\"'") for t in tags_str.split(",")]
        return result

    def _read_template_file(self, skill_path: Path, filename: str) -> Optional[str]:
        file_path = skill_path / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None

    def _load_skill(self, skill_path: Path, skill_id: str, skill_type: str) -> Optional[Dict]:
        if not skill_path.exists():
            return None

        skill_md_content = self._read_template_file(skill_path, "SKILL.md")
        if not skill_md_content:
            return None

        metadata = self._parse_skill_md(skill_md_content)
        prompt_template = self._read_template_file(skill_path, "prompt-template.md") or ""
        rules_content = self._read_template_file(skill_path, "rules.yaml") or ""

        enabled = skill_id not in self._disabled_set

        return {
            "id": skill_id,
            "name": metadata.get("name", skill_path.name),
            "description": metadata.get("description", ""),
            "version": metadata.get("version", "1.0"),
            "tags": metadata.get("tags", []),
            "type": skill_type,
            "status": "enabled" if enabled else "disabled",
            "enabled": enabled,
            "content": skill_md_content,
            "prompt_template": prompt_template,
            "rules": rules_content,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    @property
    def _disabled_set(self) -> set:
        disabled_file = self.custom_path / ".disabled"
        if disabled_file.exists():
            return set(line.strip() for line in disabled_file.read_text().split("\n") if line.strip())
        return set()

    def _save_disabled_set(self):
        disabled_file = self.custom_path / ".disabled"
        disabled_file.write_text("\n".join(self._disabled_set))

    def list_all(self) -> List[Dict]:
        self._ensure_directories()
        skills = []

        if self.system_path.exists():
            for skill_name in os.listdir(self.system_path):
                skill_path = self.system_path / skill_name
                if skill_path.is_dir():
                    skill_id = f"system-{skill_name}"
                    skill = self._load_skill(skill_path, skill_id, "system")
                    if skill:
                        skills.append(skill)

        if self.custom_path.exists():
            for skill_name in os.listdir(self.custom_path):
                if skill_name.startswith("."):
                    continue
                skill_path = self.custom_path / skill_name
                if skill_path.is_dir():
                    skill_id = f"custom-{skill_name}"
                    skill = self._load_skill(skill_path, skill_id, "custom")
                    if skill:
                        skills.append(skill)

        return skills

    def get(self, skill_id: str) -> Optional[Dict]:
        skills = self.list_all()
        for skill in skills:
            if skill["id"] == skill_id:
                return skill
        return None

    def create(self, data: Dict) -> Dict:
        self._ensure_directories()
        skill_name = data.get("name", f"skill-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        skill_path = self.custom_path / skill_name
        skill_path.mkdir(exist_ok=True)

        skill_md = data.get("skill_md", f"# {skill_name}\n\n## Description\n\n")
        prompt_template = data.get("prompt_template", "")
        rules_yaml = data.get("rules_yaml", "")

        (skill_path / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (skill_path / "prompt-template.md").write_text(prompt_template, encoding="utf-8")
        (skill_path / "rules.yaml").write_text(rules_yaml, encoding="utf-8")

        skill_id = f"custom-{skill_name}"
        return self.get(skill_id)

    def update(self, skill_id: str, data: Dict) -> Optional[Dict]:
        if not skill_id.startswith("custom-"):
            raise ValueError("Only custom baseskills can be updated")

        skill_name = skill_id.replace("custom-", "")
        skill_path = self.custom_path / skill_name
        if not skill_path.exists():
            return None

        if "skill_md" in data:
            (skill_path / "SKILL.md").write_text(data["skill_md"], encoding="utf-8")
        if "prompt_template" in data:
            (skill_path / "prompt-template.md").write_text(data["prompt_template"], encoding="utf-8")
        if "rules_yaml" in data:
            (skill_path / "rules.yaml").write_text(data["rules_yaml"], encoding="utf-8")

        return self.get(skill_id)

    def delete(self, skill_id: str) -> bool:
        if not skill_id.startswith("custom-"):
            return False

        skill_name = skill_id.replace("custom-", "")
        skill_path = self.custom_path / skill_name
        if skill_path.exists():
            shutil.rmtree(skill_path)
            return True
        return False

    def enable(self, skill_id: str) -> bool:
        if not skill_id.startswith("custom-"):
            return False

        disabled = self._disabled_set
        if skill_id in disabled:
            disabled.remove(skill_id)
            self._save_disabled_set()
        return True

    def disable(self, skill_id: str) -> bool:
        if not skill_id.startswith("custom-"):
            return False

        disabled = self._disabled_set
        disabled.add(skill_id)
        self._save_disabled_set()
        return True

    def reload(self) -> Dict:
        self._cache.clear()
        return {"message": "Baseskills reloaded successfully", "count": len(self.list_all())}


service = BaseSkillService()
