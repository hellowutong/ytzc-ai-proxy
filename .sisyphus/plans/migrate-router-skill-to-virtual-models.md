# 迁移 router Skill 分类到 virtual_models 设计计划

## TL;DR
将 Skill 管理中的 "router" 分类从全局 Skill 管理迁移到 virtual_models 下，使其作为虚拟模型独立路由配置的一部分。

**范围**: 前端设计 + 后端设计 + API设计
**预计时间**: 30分钟
**风险**: 低

---

## 变更理由

根据 `config_template.yml` 的架构设计：
- router 配置已经完全下沉到 `virtual_models.{model_name}.routing` 下
- 每个虚拟模型独立管理自己的路由配置（关键词路由、Skill路由）
- 全局的 router Skill 分类已过时，不应再显示在 Skill 管理器中

---

## 任务清单

### 1. 更新 docs/frontend_design.md

**修改位置**: 第212-227行（Skill管理器部分）

**当前设计**:
```
▼ Skill分类
  ├─ router (模型路由)          ← 需要移除
  ├─ virtual_models/knowledg (知识库)
  ├─ virtual_models/web_search (联网搜索)
  ├─ knowledge (知识提取)
  ...
```

**新设计**:
```
▼ Skill分类
  ├─ virtual_models/knowledg (知识库)
  ├─ virtual_models/web_search (联网搜索)
  ├─ knowledge (知识提取)
  ├─ rss (RSS处理)
  ├─ audio (音频处理)
  ├─ video (视频处理)
  └─ text (文本处理)
```

**说明**: 
- router 不再作为独立的 Skill 分类
- 路由配置已完全下沉到虚拟模型的 routing 字段中
- 在虚拟模型配置对话框中管理路由

### 2. 更新 docs/backend_design.md

**需要修改**:
- 移除或更新关于 router Skill 的分类描述
- 强调 routing 配置已下沉到 virtual_models
- 更新 model_router.py 的描述

### 3. 更新 docs/api_design.md

**需要修改**:
- Skill 管理相关 API 移除 router 分类
- 保留 `/admin/ai/v1/config/router` 接口（用于虚拟模型的路由配置）
- 更新 Skill 分类枚举值

---

## 执行顺序

1. 更新 frontend_design.md
2. 更新 backend_design.md
3. 更新 api_design.md
4. 手动测试验证

---

## 验收标准

- [ ] Skill 管理器左侧树不再显示 "router" 分类
- [ ] virtual_models 配置中包含 routing 字段
- [ ] 文档描述与 config_template.yml 一致
- [ ] 路由配置功能正常工作

---

## 相关配置参考

config_template.yml 中的 routing 配置位置:
```yaml
ai-gateway:
  virtual_models:
    demo1:
      routing:
        keywords:
          enable: false
          rules:
          - pattern: '@大哥'
            target: big
        skill:
          enabled: true
          version: "v1"
```
