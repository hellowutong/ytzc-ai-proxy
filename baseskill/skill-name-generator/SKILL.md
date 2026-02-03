---
name: skill-name-generator
description: 根据功能描述自动生成Skill名称和标识符
version: "1.0"
author: TW AI Saver
tags: [generator, naming, skill, metadata]
---

# Skill 名称生成器

## 使用时机

当需要为新创建的 Skill 生成规范化的名称和标识符时使用此技能。

## 指令

1. **分析功能描述**
   - 提取核心功能关键词
   - 识别主要用途和场景
   - 确定技能类型（generator, processor, analyzer, tool, workflow）

2. **生成名称方案**
   - 中文名称：简洁明了，体现核心功能
   - 英文名称：使用驼峰命名法（CamelCase）
   - 标识符：使用小写字母和连字符（kebab-case）

3. **生成标签集**
   - 主要功能标签
   - 技术栈标签
   - 使用场景标签

4. **验证唯一性**
   - 检查是否与现有Skill名称冲突
   - 验证标识符格式规范

## 约束条件

- 名称长度：中文2-10字，英文3-30字符
- 标识符格式：只能包含小写字母、数字和连字符
- 必须提供至少3个备选方案
- 每个方案需包含完整的中英文名称和标识符

## 输出格式

```yaml
name_suggestions:
  - name_zh: "中文名称"
    name_en: "SkillName"
    identifier: "skill-name"
    description: "一句话功能描述"
    tags: ["tag1", "tag2", "tag3"]
    confidence: 0.95
  - name_zh: "备选名称1"
    name_en: "AltSkillName"
    identifier: "alt-skill-name"
    description: "一句话功能描述"
    tags: ["tag1", "tag2"]
    confidence: 0.85
```
