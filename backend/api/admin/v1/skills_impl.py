"""
Skill业务逻辑实现
"""

import os
import re
import yaml
import json
import glob
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any

SKILL_ROOT = "./skills"

def scan_skill_versions(category, skill_type, skill_name):
    versions = []
    skill_path = os.path.join(SKILL_ROOT, skill_type, category)
    if not os.path.exists(skill_path):
        return versions
    version_pattern = os.path.join(skill_path, "v*")
    for version_dir in glob.glob(version_pattern):
        if os.path.isdir(version_dir):
            version_name = os.path.basename(version_dir)
            if version_name.startswith("v"):
                skill_file = os.path.join(version_dir, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    stat = os.stat(skill_file)
                    versions.append({
                        "version": version_name,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
    def version_key(v):
        match = re.match(r"v(\d+)", v["version"])
        return int(match.group(1)) if match else 0
    return sorted(versions, key=version_key)
