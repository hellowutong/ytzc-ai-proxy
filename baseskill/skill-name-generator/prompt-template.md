# Skill 名称生成 - 提示词模板

## 输入内容

```yaml
skill_description: |
  {技能的功能描述、使用场景和核心能力}

context:
  existing_skills: [{现有技能列表，用于避免命名冲突}]
  preferred_language: "{首选语言}"  # zh | en | both
  naming_style: "{命名风格}"  # formal | casual | technical
  include_emoji: {是否包含emoji}  # true | false
```

## 生成要求

1. **核心功能提取**
   - 识别技能的主要功能
   - 提取3-5个关键词
   - 确定技能类别（processor, generator, analyzer, tool, workflow）

2. **命名规范**
   - 中文名称：使用常用词汇，避免生僻字
   - 英文名称：使用行业标准术语
   - 标识符：符合 k8s/naming 规范

3. **标签策略**
   - 功能标签（processor, generator）
   - 技术标签（python, javascript）
   - 场景标签（text, code, data）
   - 复杂度标签（simple, medium, complex）

4. **多样性生成**
   - 方案1：正式名称
   - 方案2：简洁名称
   - 方案3：创意名称
   - 方案4：技术导向名称

## 模板变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `{skill_description}` | 技能功能描述 | "将长文本进行摘要提炼" |
| `{existing_skills}` | 现有技能列表 | ["skill-generator", "vectorizer"] |
| `{preferred_language}` | 首选语言 | "zh" |
| `{naming_style}` | 命名风格 | "formal" |

## 输出格式

```yaml
name_proposal:
  request_description: "{原始功能描述}"
  generated_at: "{生成时间}"
  suggestions:
    - rank: 1
      name_zh: "主推荐名称"
      name_en: "PrimaryName"
      identifier: "primary-name"
      slug: "primary-name"
      description: "一句话描述核心功能"
      tags:
        primary: ["processor"]
        secondary: ["text", "nlp"]
        tech: ["python"]
      category: "processor"
      confidence: 0.95
      rationale: "命名理由说明"
    - rank: 2
      name_zh: "备选名称1"
      name_en: "AltName1"
      identifier: "alt-name-1"
      slug: "alt-name-1"
      description: "一句话描述"
      tags:
        primary: ["processor"]
        secondary: ["text"]
      category: "processor"
      confidence: 0.85
      rationale: "命名理由说明"
    - rank: 3
      name_zh: "备选名称2"
      name_en: "AltName2"
      identifier: "alt-name-2"
      slug: "alt-name-2"
      description: "一句话描述"
      tags:
        primary: ["processor"]
        secondary: ["text"]
      category: "processor"
      confidence: 0.75
      rationale: "命名理由说明"
  conflict_check:
    has_conflicts: false
    conflicts: []
  metadata:
    total_suggestions: 3
    processing_time_ms: 152
```

## 生成示例

```yaml
name_proposal:
  request_description: "将用户输入的长文本进行智能摘要，提取关键信息点"
  generated_at: "2026-02-02T10:30:00Z"
  suggestions:
    - rank: 1
      name_zh: "文本摘要器"
      name_en: "TextSummarizer"
      identifier: "text-summarizer"
      slug: "text-summarizer"
      description: "智能提取文本关键信息"
      tags:
        primary: ["generator"]
        secondary: ["text", "nlp"]
        tech: ["python"]
      category: "generator"
      confidence: 0.95
      rationale: "直接描述功能，通俗易懂"
    - rank: 2
      name_zh: "摘要生成器"
      name_en: "SummaryGenerator"
      identifier: "summary-generator"
      slug: "summary-generator"
      description: "生成文本摘要内容"
      tags:
        primary: ["generator"]
        secondary: ["text"]
      category: "generator"
      confidence: 0.88
      rationale: "强调生成能力"
    - rank: 3
      name_zh: "要点提炼器"
      name_en: "KeyPointExtractor"
      identifier: "key-point-extractor"
      slug: "key-point-extractor"
      description: "提取文本核心要点"
      tags:
        primary: ["processor"]
        secondary: ["text", "analysis"]
      category: "processor"
      confidence: 0.82
      rationale: "强调分析能力"
  conflict_check:
    has_conflicts: false
    conflicts: []
  metadata:
    total_suggestions: 3
    processing_time_ms: 152
```

## 质量检查标准

1. **命名质量**
   - 名称准确反映功能
   - 英文拼写正确
   - 标识符格式规范

2. **标签准确性**
   - 至少包含1个主标签
   - 标签与功能匹配

3. **置信度合理性**
   - 最佳方案置信度 > 0.9
   - 备选方案置信度 > 0.7
   - 置信度差异合理

4. **冲突检测**
   - 检查与现有Skill名称
   - 检查与现有标识符
   - 避免重复命名
