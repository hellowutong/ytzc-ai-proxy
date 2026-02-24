# 前端设计文档 - frontend

**技术栈**: Vue 3 + Element Plus + TypeScript + Vite  
**主题**: 暗色主题（类似 ChatGPT）  
**部署**: 本地部署，无认证

---

## 1. 页面路由结构

```
/login          # 占位（自动跳转，实际无认证）
/proxy/chat     # WebChat测试页
/admin/         # 后台管理布局
  ├── dashboard              # 看板
  ├── models/                # 虚拟模型管理
  │   └── list
  ├── skills/                # Skill管理器
  │   └── manager
  ├── knowledge/             # 知识库管理
  │   ├── list
  │   ├── config             # 向量/定时器/Skill/主题配置
  ├── media/                 # 媒体处理队列
  │   ├── video
  │   ├── audio
  │   └── text
  ├── rss/                   # RSS订阅管理
  │   └── list
  ├── logs/                  # 日志查询器
  │   ├── system
  │   ├── operation
  │   └── skill
  ├── config/                # 系统配置（config.yml编辑器）
  ├── conversations/         # 对话历史
  └── raw-data/              # 原始数据查看器
      ├── conversations
      ├── media
      └── rss
```

---

## 2. 页面功能详单

### 2.1 WebChat 测试页 (`/proxy/chat`)

**布局**: 三栏布局（左：历史会话 | 中：对话区 | 右：设置抽屉）

#### 左侧边栏
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 新建对话** | 按钮 | 创建新会话，清空上下文 |
| **历史会话列表** | 列表 | 显示最近10个会话，点击切换 |
| **删除图标** | 图标按钮 | 删除对应历史会话 |
| **设置 ⚙️** | 图标按钮 | 打开设置抽屉 |

#### 顶部栏
| 元素 | 类型 | 功能 |
|------|------|------|
| **模型选择下拉框** | 下拉框 | 切换虚拟模型（demo1/demo2/...） |
| **当前模型指示器** | 文本 | 显示当前使用的大/小模型 |
| **清空对话** | 按钮 | 清空当前会话消息 |
| **关闭页面** | 按钮 | 关闭当前页面/标签页 |

#### 对话区域
| 元素 | 类型 | 功能 |
|------|------|------|
| **消息气泡** | 组件 | 用户（右/蓝）/AI（左/灰） |
| **知识引用标注** | 高亮 | 显示引用的知识库内容 |
| **模型切换标记** | 标签 | 显示"已切换到大模型"等 |

#### 输入区
| 元素 | 类型 | 功能 |
|------|------|------|
| **文本输入框** | 文本域 | 支持Shift+Enter换行 |
| **发送按钮** | 按钮 | 发送消息 |
| **停止按钮** | 按钮 | 流式响应时显示，中断生成 |

#### 设置抽屉（右侧滑出）
```
┌─ ⚙️ 设置 ──────────────────┐
│                             │
│ 模型参数                     │
│ • Temperature: [滑块 0-2]   │
│ • Max Tokens: [数字输入]    │
│ • 流式响应: [开关]          │
│                             │
│ 功能开关                     │
│ • 知识库检索: [开关]        │
│ • 联网搜索: [开关]          │
│                             │
│ 显示设置                     │
│ • 暗色主题: [开关]          │
│ • 代码高亮: [开关]          │
│ • 显示思考过程: [开关]      │
│                             │
│ [保存] [重置为默认]         │
└─────────────────────────────┘
```

---

### 2.2 Dashboard 看板 (`/admin/dashboard`)

**布局**: 统计卡片网格 + 快捷操作 + 最近活动列表

#### 统计卡片区（6个卡片）
| 卡片 | 显示内容 | 点击操作 |
|------|----------|----------|
| **虚拟模型数** | 当前模型数量 | 进入模型管理 |
| **今日对话数** | 24小时内对话次数 | 查看详情 |
| **知识库文档** | 向量库文档数量 | 进入知识库 |
| **媒体队列** | 待处理/处理中文件数 | 进入媒体管理 |
| **RSS订阅** | 活跃RSS源数量 | 进入RSS管理 |
| **系统状态** | 各服务健康状态 | 刷新按钮 |

#### 快捷操作区
| 按钮 | 功能 |
|------|------|
| **⚡ 重载配置** | 调用POST /admin/ai/v1/config/reload |
| **🔄 重载Skill** | 调用POST /admin/ai/v1/skills/reload |
| **📝 查看日志** | 跳转到日志页面 |
| **🔧 系统配置** | 跳转到配置页面 |

#### 最近活动列表
| 列 | 内容 |
|---|------|
| 时间 | 操作发生时间 |
| 类型 | config/skill/model/media/rss |
| 操作 | 具体操作描述 |
| 状态 | 成功/失败 |
| 查看 | 跳转到详细日志 |

---

### 2.3 虚拟模型管理 (`/admin/models`)

**布局**: 工具栏 + 表格 + 对话框

#### 列表页工具栏
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 添加模型** | 按钮 | 打开添加对话框 |
| **搜索框** | 输入框 | 按名称筛选模型 |
| **状态筛选** | 下拉框 | 全部/启用/禁用 |

#### 表格列
| 列名 | 类型 | 功能/操作 |
|------|------|-----------|
| **名称** | 可点击文本 | **点击复制**到剪贴板 |
| **Proxy Key** | 掩码文本 | **点击复制**（显示***） |
| **系统URL** | 可点击文本 | **点击复制**到剪贴板 |
| **当前模型** | 文本+按钮 | small/big + **[切换]**按钮 |
| **状态** | 开关 | 启用/禁用 |
| **操作** | 按钮组 | [编辑] [模型测试] [删除] |

#### 添加/编辑对话框

**基础信息区**
| 元素 | 类型 | 说明 |
|------|------|------|
| **虚拟模型名称** | 输入框 | 唯一标识，如demo1 |
| **Proxy Key** | 输入框+按钮 | 显示/隐藏/复制/重新生成 |
| **Base URL** | 输入框 | 可选，模型API基础地址 |
| **当前模型** | 单选按钮组 | small（小模型）/ big（大模型） |
| **强制使用** | 开关 | 是否强制使用当前模型 |
| **流式支持** | 开关 | 是否支持流式返回（SSE） |
| **启用状态** | 开关 | 是否启用该虚拟模型 |
| **关键字模型切换** | 开关 | 启用/禁用关键字模型切换功能 |

**关键字模型切换配置区**（仅在开关开启时显示）
| 元素 | 类型 | 说明 |
|------|------|------|
| **小模型关键词** | Tag输入 | 触发切换到小模型的关键词列表，最多50个，每个最多50字符 |
| **大模型关键词** | Tag输入 | 触发切换到大模型的关键词列表，最多50个，每个最多50字符 |

**小模型配置区**
| 元素 | 类型 | 说明 |
|------|------|------|
| **模型名称** | 输入框 | 如deepseek-ai/DeepSeek-R1 |
| **API Key** | 密码输入框 | sk-xxx |
| **Base URL** | 输入框 | https://api.xxx.com/v1 |
| **🧪 测试连接** | 按钮 | 验证API可访问 |

**大模型配置区**（同上）

**知识库配置区**
| 元素 | 类型 | 说明 |
|------|------|------|
| **启用知识库** | 开关 | 是否启用知识库功能 |
| **共享知识库** | 开关 | 是否使用共享知识库 |
| **系统默认Skill** | 单选按钮组 | 选择版本（v1/v2/v3）或"不使用" |
| **自定义Skill** | 开关+单选 | 是否启用 + 选择版本 |

**联网搜索配置区**
| 元素 | 类型 | 说明 |
|------|------|------|
| **启用联网搜索** | 开关 | 是否启用联网搜索功能 |
| **系统默认Skill** | 单选按钮组 | 选择版本（v1/v2/v3）或"不使用" |
| **自定义Skill** | 开关+单选 | 是否启用 + 选择版本 |
| **搜索目标** | 多选框 | ☑SearXNG ☑LibreX ☑4get |

**对话框按钮**
| 按钮 | 功能 |
|------|------|
| **保存** | 提交表单 |
| **取消** | 关闭对话框 |
| **测试所有连接** | 测试small+big模型连通性 |

---

### 2.4 Skill管理器 (`/admin/skills`)

**布局**: 左侧分类树 + 右侧双区域（系统默认Skills + 自定义Skills）

#### 左侧分类树
```
▼ Skill分类
  ▼ virtual_models (虚拟模型)
    ├─ router (模型路由)
    ├─ knowledge (知识库)
    └─ web_search (联网搜索)
  ├─ knowledge (知识提取)
  ├─ rss (RSS处理)
  ├─ audio (音频处理)
  ├─ video (视频处理)
  └─ text (文本处理)
```

**说明**: 
- router（模型路由）已移动到 virtual_models 分类下作为子节点
- **架构说明**: 虽然每个虚拟模型在配置中都有独立的 `routing` 字段，但为了 Skill 管理的统一性，将 router 作为虚拟模型分类下的子节点进行管理

#### 右侧详情区 - 系统默认Skills（只读）

**区域说明**: 显示该分类下所有系统默认Skill，只读不可编辑

**Skill卡片布局**:
```
┌─────────────────────────────────────────────────────────┐
│ 系统默认 Skills                                          │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│ │ 关键词路由   │  │  意图识别    │  │    ...      │      │
│ │             │  │             │  │             │      │
│ │ 版本: [v1 ▼]│  │ 版本: [v1 ▼]│  │ 版本: [v1 ▼]│      │
│ │             │  │             │  │             │      │
│ │  [查看]     │  │  [查看]     │  │  [查看]     │      │
│ └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**卡片元素**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **Skill名称** | 文本 | 系统Skill名称 |
| **版本选择** | 下拉框 | 选择版本 v1/v2/v3 |
| **查看按钮** | 按钮 | 只读查看SKILL.md（Monaco Editor弹窗） |

#### 右侧详情区 - 自定义Skills（可增删改）

**区域说明**: 显示该分类下所有自定义Skill，支持完整CRUD操作

**头部工具栏**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **[+ 新增Skill]** | 按钮 | 打开新增Skill对话框 |
| **[🔄 重载全部]** | 按钮 | 重载该分类所有Skill |

**Skill卡片布局**:
```
┌─────────────────────────────────────────────────────────┐
│ 自定义 Skills                                   [+ 新增] │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│ │ X_skill  ✏️ │  │ Y_skill  ✏️ │  │ Z_skill  ✏️ │      │
│ │             │  │             │  │             │      │
│ │版本: [v1 ▼] │  │版本: [v2 ▼] │  │版本: [v3 ▼] │      │
│ │             │  │             │  │             │      │
│ │[查看][编辑] │  │[查看][编辑] │  │[查看][编辑] │      │
│ │[删除Skill]  │  │[删除Skill]  │  │[删除Skill]  │      │
│ └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**卡片元素**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **Skill名称** | 文本（可编辑） | 点击✏️图标可修改名称 |
| **版本选择** | 下拉框 | 选择该Skill的版本，支持"+ 新增版本" |
| **查看按钮** | 按钮 | 查看当前版本SKILL.md |
| **编辑按钮** | 按钮 | 打开编辑器修改Skill |
| **删除Skill按钮** | 按钮（危险色） | 删除整个Skill及其所有版本 |

#### 新增Skill对话框

```
┌─────────────────────────────────────────────┐
│ 新增自定义 Skill                             │
├─────────────────────────────────────────────┤
│                                             │
│ Skill名称: [                              ] │
│           如: MyRouter, 优化版路由           │
│                                             │
│ 初始版本: [v1                             ] │
│                                             │
│ 复制来源:                                    │
│   ○ 空白创建                                 │
│   ● 系统默认 v1 (关键词路由)                 │
│   ○ 系统默认 v1 (意图识别)                   │
│   ○ 其他自定义 Skill...                      │
│                                             │
│              [取消]  [创建]                  │
└─────────────────────────────────────────────┘
```

**表单元素**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **Skill名称** | 输入框 | 自定义Skill名称，同一分类下唯一 |
| **初始版本** | 输入框 | 默认v1，可自定义 |
| **复制来源** | 单选组 | 空白创建或复制现有Skill |

#### Skill编辑器对话框（多文件支持）

**布局**: 三栏布局（左侧文件树 | 中间编辑区 | 右侧预览区）

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 编辑 Skill: X_skill (v2)                    [重载] [删除] [关闭]              │
├──────────────┬─────────────────────────────────┬───────────────────────────────┤
│ 文件树       │ 编辑区（多标签）                 │ 预览区                        │
│ 240px        │ flex: 1                         │ flex: 1                       │
│              │                                 │                               │
│ 📁 X_skill/  │ [SKILL.md×] [utils.py×] [+]    │ SKILL.md 预览                 │
│ ├─📄SKILL.md │ ┌─────────────────────────────┐ │ ┌───────────────────────────┐ │
│ ├─📁ref/     │ │ ---                         │ │ │ # Skill 名称              │ │
│ │ ├─📄a.md   │ │ name: X_skill               │ │ │                           │ │
│ │ └─📄b.md   │ │ version: "2.0.0"            │ │ │ 描述内容...               │ │
│ ├─📁scripts/ │ │ type: rule-based            │ │ │                           │ │
│ │ └─📄run.py │ │ priority: 80                │ │ │ ## 输入参数               │ │
│ └─📄utils.py │ │ ---                         │ │ │ - param1: string          │ │
│              │ │                             │ │ │ - param2: number          │ │
│ ──────────── │ │ # Skill 描述                │ │ │                           │ │
│ [+新建文件夹] │ │                             │ │ │ ## 输出格式               │ │
│ [+新建文件]   │ │                             │ │ │ - result: string          │ │
│              │ └─────────────────────────────┘ │ └───────────────────────────┘ │
│              │                                 │                               │
│              │ ⚠️ 警告: description 建议填写    │ [刷新预览]                    │
│              │ [✓ 校验] [💾 保存当前文件]      │                               │
├──────────────┴─────────────────────────────────┴───────────────────────────────┤
│ 版本管理: 当前: v2 | 所有版本: v1, v2, v3 | [切换版本] [新增版本]              │
└────────────────────────────────────────────────────────────────────────────────┘
```

##### 左侧文件树（240px 固定宽度）

**文件树工具栏**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 新建文件夹** | 按钮 | 在选中节点下创建子文件夹
| **+ 新建文件** | 按钮 | 在选中节点下创建 .md 或 .py 文件

**文件树节点图标**:
| 文件类型 | 图标 | 说明 |
|----------|------|------|
| SKILL.md | 📄（高亮） | 必须存在，Skill 定义文件
| *.md | 📄 | Markdown 文件
| *.py | 🐍 | Python 脚本文件
| 文件夹 | 📁/📂 | 展开/折叠状态
| 不可编辑 | 📄（灰色） | 二进制/非文本文件，双击提示不可编辑 |

**右键菜单**:
| 操作 | 文件 | 文件夹 |
|------|------|------|
| 新建文件 | ✓ | ✓ |
| 新建文件夹 | - | ✓ |
| 重命名 | ✓ | ✓ |
| 删除 | ✓ | ✓（非空需确认）|
| 复制路径 | ✓ | ✓ |

**文件树交互**:
- 单击：选中节点，右侧显示文件内容
- 双击：打开文件到新标签页
- 右键：显示操作菜单
- 拖拽：移动文件/文件夹（待实现）

##### 中间编辑区（flex: 1）

**多文件标签页**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **文件标签** | 标签页 | 显示文件名，带关闭按钮
| **修改标记** | 圆点 | 文件已修改但未保存时显示
| **+ 新标签** | 按钮 | 快速新建文件

**编辑器**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **Monaco Editor** | 代码编辑器 | 支持 YAML、Markdown、Python 语法高亮
| **行号** | 行号 | 显示行号，点击定位
| **语法检查** | 波浪线 | 实时语法错误提示

**底部工具栏**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **校验状态** | 状态文本 | 🔍 待校验 / ✅ 已通过 / ❌ 有错误 / ⚠️ 有警告
| **✓ 校验** | 按钮 | 校验当前文件（SKILL.md 校验 YAML frontmatter）
| **💾 保存** | 按钮 | 保存当前文件（每个文件独立保存）|

##### 右侧预览区（flex: 1）

**预览内容**:
| 文件类型 | 预览方式 |
|----------|----------|
| SKILL.md | Markdown 渲染 + 结构化展示
| *.md | Markdown 渲染
| *.py | 语法高亮只读展示
| 非文本 | "此文件类型不支持预览" |

**预览工具栏**:
| 元素 | 类型 | 功能 |
|------|------|------|
| **刷新预览** | 按钮 | 重新渲染预览内容
| **复制内容** | 按钮 | 复制预览内容到剪贴板 |

##### 底部版本管理栏
| 元素 | 类型 | 功能 |
|------|------|------|
| **当前版本** | 文本 | 显示当前编辑的版本
| **所有版本** | 标签列表 | 显示所有版本，点击切换
| **切换版本** | 按钮 | 下拉选择目标版本
| **新增版本** | 按钮 | 创建新版本 |

##### 文件操作流程

**新建文件**:
1. 点击 [新建文件] 按钮或右键菜单
2. 弹出对话框：输入文件名（必须 .md 或 .py 后缀）
3. 选择父目录（默认当前选中节点）
4. 创建成功后自动打开到新标签

**新建文件夹**:
1. 点击 [新建文件夹] 按钮或右键菜单
2. 弹出对话框：输入文件夹名
3. 选择父目录（默认当前选中节点）
4. 创建成功后刷新文件树

**删除文件/文件夹**:
1. 右键菜单选择 [删除]
2. 弹出确认对话框
3. 如果是文件夹且非空，显示包含内容列表并要求二次确认
4. 删除成功后关闭相关标签并刷新文件树

**重命名**:
1. 右键菜单选择 [重命名] 或双击文件名
2. 内联编辑文件名
3. 修改后缀名时警告可能导致的问题
4. 保存成功后更新标签名

##### 强制校验机制

**SKILL.md 校验规则**:
1. 打开编辑器时，[保存] 按钮**禁用**（灰色）
2. 必须点击 [✓ 校验] 并通过后，[保存] 才能变为可用
3. 编辑器内容发生任何修改后，校验状态重置为 "🔍 待校验"，[保存] 再次禁用
4. 校验内容：YAML格式、必填字段(name/version/type/priority/description)、JSON Schema有效性
5. 校验失败时显示详细错误信息和行号，支持"定位到错误行"
6. **描述验证**：description 字段为空时显示 ⚠️ 警告但不阻止保存

**Python 文件校验**:
- 语法检查（使用 Python AST）
- 导入警告（不允许导入危险模块）

---

### 2.5 知识库管理 (`/admin/knowledge`)

**标签页**
```
[文档列表] [向量配置] [定时器] [Skill配置] [主题分类]
```

#### 文档列表标签

**工具栏**
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 上传文档** | 按钮 | 打开上传对话框 |
| **搜索框** | 输入框 | 按文件名/内容搜索 |
| **类型筛选** | 下拉框 | 全部/pdf/txt/doc/jpg |
| **来源筛选** | 下拉框 | 上传/RSS/对话提取 |
| **时间范围** | 日期选择 | 日期范围选择 |

**表格列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **文件名** | 文本 | 文档名称 |
| **类型** | 标签 | pdf/txt/doc/jpg |
| **来源** | 标签 | 上传/RSS/对话提取 |
| **向量化状态** | 状态 | 已向量/待处理/失败 |
| **操作** | 按钮组 | [预览] [重新向量化] [删除] |

**上传对话框**
| 元素 | 类型 | 功能 |
|------|------|------|
| **拖拽上传区** | 拖放区 | 支持pdf/txt/doc/jpg |
| **或选择文件** | 文件选择 | 点击选择文件 |
| **目标虚拟模型** | 下拉框 | 选择关联的模型 |
| **是否共享** | 开关 | 共享知识库开关 |
| **分段大小** | 数字输入 | 默认500 |
| **重叠大小** | 数字输入 | 默认50 |
| **语言** | 下拉框 | zh/en等 |
| **开始上传** | 按钮 | 提交上传 |

#### 向量配置标签
| 元素 | 类型 | 功能 |
|------|------|------|
| **Embedding模型** | 输入框 | 如BAAI/bge-m3 |
| **Base URL** | 输入框 | API地址 |
| **API Key** | 密码输入 | 密钥 |
| **🧪 测试连接** | 按钮 | **测试向量服务连通性** |
| **💾 保存配置** | 按钮 | 保存向量配置 |

#### 定时器配置标签
| 元素 | 类型 | 功能 |
|------|------|------|
| **Cron表达式** | 输入框 | 如*/30 * * * * |
| **启用定时抓取** | 开关 | 开启/关闭定时任务 |
| **💾 保存配置** | 按钮 | 保存定时器配置 |

#### Skill配置标签
| 元素 | 类型 | 功能 |
|------|------|------|
| **知识提取Skill-系统默认** | 下拉+开关 | v1/v2/v3 + 启用 |
| **知识提取Skill-自定义** | 下拉+开关 | v1/v2/v3 + 启用 |
| **主题分类Skill-系统默认** | 下拉+开关 | v1/v2/v3 + 启用 |
| **主题分类Skill-自定义** | 下拉+开关 | v1/v2/v3 + 启用 |
| **💾 保存配置** | 按钮 | 保存Skill配置 |

#### 主题分类标签

**自动分类区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 添加分类** | 按钮 | 添加新的自动分类 |
| **分类列表** | 列表 | 显示现有分类 |
| **主题名** | 输入框 | 如"项目架构" |
| **模式** | 标签输入 | 多个关键词标签 |
| **删除** | 图标 | 删除该分类 |

**自定义分类区**（同上）

**向量检索测试区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **测试查询输入** | 文本域 | 输入测试问题 |
| **相似度阈值** | 滑块 | 0-1，默认0.76 |
| **🔍 检索** | 按钮 | 执行向量检索 |
| **结果列表** | 列表 | 显示匹配的知识片段 |

---

### 2.6 媒体处理队列 (`/admin/media`)

**标签页**
```
[视频处理] [音频处理] [文档处理]
```

#### 视频处理标签

**工具栏**
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 上传视频** | 按钮 | 打开上传对话框 |
| **+ URL下载** | 按钮 | 输入视频URL下载 |
| **搜索框** | 输入框 | 按文件名搜索 |
| **状态筛选** | 下拉框 | 全部/待处理/转录中/已完成/失败 |

**表格列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **文件名** | 文本 | 视频文件名 |
| **大小** | 文本 | 文件大小 |
| **状态** | 状态 | 待处理/转录中/已完成/失败 |
| **进度** | 进度条 | 转录进度 |
| **操作** | 按钮组 | [查看] [重新转录] [删除] |

**上传对话框**
| 元素 | 类型 | 功能 |
|------|------|------|
| **文件选择** | 文件选择 | 选择视频文件 |
| **转录处理器** | 下拉框 | whisper/faster_whisper/whisper_npu |
| **模型** | 下拉框 | base/small/medium/large |
| **语言** | 下拉框 | zh/en等 |
| **自动转录** | 开关 | 上传后自动开始 |
| **开始上传** | 按钮 | 提交上传 |

**URL下载对话框**
| 元素 | 类型 | 功能 |
|------|------|------|
| **视频URL** | 输入框 | 输入下载链接 |
| **处理器/模型/语言** | （同上传） | 转录配置 |
| **开始下载** | 按钮 | 提交下载任务 |

**视频Skill配置区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **系统默认Skill** | 下拉+开关 | v1/v2/v3 + 启用 |
| **自定义Skill** | 下拉+开关 | v1/v2/v3 + 启用 |
| **💾 保存** | 按钮 | 保存Skill配置 |

#### 音频处理标签（同视频，略）

#### 文档处理标签

**工具栏**
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 上传文档** | 按钮 | 上传pdf/doc/txt等 |
| **提取知识开关** | 开关 | 是否自动提取到知识库 |

**表格列**（同视频）

**文档Skill配置区**（同视频）

---

### 2.7 RSS订阅管理 (`/admin/rss`)

**布局**: 订阅源列表 + 文章列表 + 配置

#### 订阅源列表

**工具栏**
| 元素 | 类型 | 功能 |
|------|------|------|
| **+ 添加订阅** | 按钮 | 打开添加对话框 |
| **批量导入** | 按钮 | 导入OPML文件 |
| **搜索框** | 输入框 | 按名称/URL搜索 |
| **状态筛选** | 下拉框 | 全部/启用/禁用 |

**表格列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **名称** | 文本 | 订阅名称 |
| **URL** | 文本 | RSS地址 |
| **更新频率** | 文本 | 30分钟/1小时/6小时/每天 |
| **文章数** | 数字 | 已抓取文章数量 |
| **状态** | 开关 | 启用/禁用 |
| **操作** | 按钮组 | [立即抓取] [编辑] [启用/禁用] [删除] |

**添加/编辑对话框**
| 元素 | 类型 | 功能 |
|------|------|------|
| **订阅名称** | 输入框 | 显示名称 |
| **RSS URL** | 输入框 | 订阅地址 |
| **启用状态** | 开关 | 是否启用 |
| **更新频率** | 下拉框 | 30分钟/1小时/6小时/每天 |
| **保留天数** | 数字输入 | 文章保留时间 |
| **永久保存** | 开关 | 是否永久保存 |
| **关联虚拟模型** | 下拉框 | 提取知识使用的模型 |

**RSS Skill配置区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **系统默认Skill** | 下拉+开关 | v1/v2/v3 + 启用 |
| **自定义Skill** | 下拉+开关 | v1/v2/v3 + 启用 |
| **💾 保存** | 按钮 | 保存Skill配置 |

#### 文章列表（点击订阅源展开）

**抓取说明**: **必须爬取完整内容**，不只是RSS摘要

| 列名 | 类型 | 功能 |
|------|------|------|
| **标题** | 可点击文本 | 文章标题 |
| **发布时间** | 文本 | 发布时间 |
| **原文链接** | 链接 | 外链图标 |
| **抓取状态** | 状态 | 已抓取完整内容/仅摘要/抓取失败 |
| **内容长度** | 数字 | 正文字符数 |
| **操作** | 按钮组 | [查看完整内容] [查看原文] [查看知识] [删除] |

**查看完整内容对话框**
```
┌─ 完整内容 ──────────────────┐
│ 标题: xxx                   │
│ 来源: RSS订阅名称            │
│ 原文链接: [打开原文]         │
│                              │
│ [纯文本] [原始HTML] [Markdown]│
│                              │
│ ┌─────────────────────────┐ │
│ │   正文内容显示区域...    │ │
│ │   (支持代码高亮)         │ │
│ └─────────────────────────┘ │
│                              │
│ [复制] [导出] [关闭]        │
└─────────────────────────────┘
```

---

### 2.8 日志查询器 (`/admin/logs`)

**标签页**
```
[系统日志] [操作日志] [Skill执行日志]
```

#### 系统日志标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **日志级别** | 多选框 | DEBUG/INFO/WARNING/ERROR |
| **时间范围** | 日期选择 | 今天/最近7天/自定义 |
| **关键词搜索** | 输入框 | 搜索日志内容 |
| **自动刷新** | 开关 | 是否实时刷新 |
| **🔄 刷新** | 按钮 | 手动刷新 |
| **📥 导出** | 按钮 | 导出为文件 |

**日志列表**
| 列名 | 类型 | 功能 |
|------|------|------|
| **时间** | 文本 | 日志时间 |
| **级别** | 标签 | DEBUG/INFO/WARNING/ERROR |
| **模块** | 标签 | 来源模块 |
| **消息** | 文本 | 日志内容摘要 |
| **展开** | 图标 | 查看完整日志内容 |

#### 操作日志标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **操作类型** | 多选框 | config/skill/model/media/rss |
| **时间范围** | 日期选择 | 日期范围 |
| **结果筛选** | 下拉框 | 成功/失败 |

**表格列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **时间** | 文本 | 操作时间 |
| **类型** | 标签 | 操作类型 |
| **操作** | 文本 | 操作描述 |
| **结果** | 状态 | 成功/失败 |
| **查看详情** | 按钮 | 查看操作参数和结果 |

#### Skill执行日志标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **Skill分类** | 下拉框 | router/knowledge/... |
| **执行结果** | 下拉框 | 成功/失败/验证错误 |
| **时间范围** | 日期选择 | 日期范围 |

**表格列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **时间** | 文本 | 执行时间 |
| **Skill** | 标签 | Skill分类/名称 |
| **输入** | 文本 | 输入参数摘要 |
| **输出** | 文本 | 输出结果摘要 |
| **耗时** | 文本 | 执行时长 |
| **状态** | 状态 | 成功/失败 |
| **操作** | 按钮组 | [查看详情] [重新执行] |

**详情对话框**
| 元素 | 类型 | 功能 |
|------|------|------|
| **完整输入** | JSON展示 | 格式化显示输入参数 |
| **完整输出** | JSON展示 | 格式化显示输出结果 |
| **错误信息** | 文本 | 失败时显示错误 |
| **调用链** | 时间线 | 显示执行步骤 |

---

### 2.9 系统配置 (`/admin/config`)

**布局**: Monaco Editor + 配置树 + 工具栏

#### 顶部工具栏
| 元素 | 类型 | 功能 |
|------|------|------|
| **语法验证** | 按钮 | 实时验证YAML语法 |
| **Schema验证** | 按钮 | 验证配置结构 |
| **对比** | 按钮 | 显示修改前后差异 |
| **💾 保存** | 按钮 | 保存并触发重载 |
| **重置** | 按钮 | 放弃修改 |
| **从模板恢复** | 危险按钮 | 从config_template.yml恢复（需确认） |

#### 编辑区
| 元素 | 类型 | 功能 |
|------|------|------|
| **Monaco Editor** | 代码编辑器 | YAML格式编辑config.yml |

#### 左侧配置树导航
```
▼ ai-gateway
  ├─ router
  ├─ virtual_models
  │   └─ [各模型...]
  ├─ knowledge
  ├─ rss
  └─ media
      ├─ video
      ├─ audio
      └─ text
```

---

### 2.10 路由配置 (`/admin/config/router`)

**布局**: 卡片式布局，包含四个配置区域

**页面结构**:
```
┌─ 路由配置                                          [保存]   │
├─────────────────────────────────────────────────────────────┤
│  ┌─ 强制模式配置 ──────────────────────────────────────────┐│
│  │  [✓] 启用强制模式                                       ││
│  │  强制目标模型: [small ●] [big ○]                        ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌─ 全局关键词路由 ────────────────────────────────────────┐│
│  │  [✓] 启用关键词路由                                     ││
│  │  关键词规则列表:                                         ││
│  │  ┌──────────────┬────────────┬────────────┬──────────┐  ││
│  │  │ 关键词模式   │ 目标模型   │ 描述       │ 操作     │  ││
│  │  │ @大哥        │ 大模型     │ 切换大模型 │ [编辑]   │  ││
│  │  │ @小弟        │ 小模型     │ 切换小模型 │ [编辑]   │  ││
│  │  └──────────────┴────────────┴────────────┴──────────┘  ││
│  │  [+ 添加关键词规则]                                      ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌─ Skill 路由配置 ────────────────────────────────────────┐│
│  │  [✓] 启用系统默认 Skill 路由                             ││
│  │  版本: [v1 ▼]                                            ││
│  │  [✓] 启用自定义 Skill 路由                               ││
│  │  版本: [v2 ▼]                                            ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌─ 路由测试 ──────────────────────────────────────────────┐│
│  │  测试输入: [请输入测试消息...                    ] [测试] ││
│  │  测试结果:                                               ││
│  │  匹配规则: 全局关键词: @大哥                              ││
│  │  目标模型: 大模型                                         ││
│  │  置信度: 100%                                             ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### 强制模式配置区
| 元素 | 类型 | 功能 |
|------|------|------|
| **启用强制模式** | 开关 | 开启后强制使用指定模型，忽略所有路由规则 |
| **强制目标模型** | 单选按钮组 | 选择 small（小模型）或 big（大模型） |

#### 全局关键词路由区
| 元素 | 类型 | 功能 |
|------|------|------|
| **启用关键词路由** | 开关 | 开启关键词匹配路由功能 |
| **关键词规则表格** | 表格 | 显示所有关键词规则 |
| **关键词模式列** | 输入框 | 编辑关键词模式（如 @大哥） |
| **目标模型列** | 下拉框 | 选择 small 或 big |
| **描述列** | 输入框 | 规则描述（可选） |
| **操作列** | 按钮 | 删除规则 |
| **添加规则按钮** | 按钮 | 添加新的关键词规则 |

#### Skill 路由配置区
| 元素 | 类型 | 功能 |
|------|------|------|
| **启用系统默认 Skill** | 开关 | 开启系统默认 Skill 路由 |
| **系统版本** | 下拉框 | 选择 v1/v2/v3 |
| **启用自定义 Skill** | 开关 | 开启自定义 Skill 路由 |
| **自定义版本** | 下拉框 | 选择 v1/v2/v3 |

#### 路由测试区
| 元素 | 类型 | 功能 |
|------|------|------|
| **测试输入** | 输入框 | 输入测试消息 |
| **测试按钮** | 按钮 | 执行路由测试 |
| **测试结果** | 描述列表 | 显示匹配规则、目标模型、置信度 |

**配置数据结构**:
```yaml
ai-gateway:
  router:
    force: "small"           # 被强制的模型
    enable-force: true       # 是否启用强制模式
    skill:
      enabled: true          # 系统默认 Skill 是否开启
      version: "v1"          # 系统默认 Skill 版本
      custom:
        enabled: true        # 自定义 Skill 是否开启
        version: "v2"        # 自定义 Skill 版本
    keywords:
      enable: false          # 是否开启关键词路由
      rules:                 # 关键词规则列表
        - pattern: "@大哥"   # 输入 @大哥 切换大模型
          target: "big"
        - pattern: "@小弟"   # 输入 @小弟 切换小模型
          target: "small"
```

#### 右侧辅助面板
| 元素 | 类型 | 功能 |
|------|------|------|
| **配置项说明** | 文本 | 悬停提示说明 |
| **有效值范围** | 文本 | 数字的最小/最大值 |
| **示例值** | 代码 | 提供填写示例 |
| **关联文档** | 链接 | 链接到docs/下的文档 |

---

### 2.11 对话历史 (`/admin/conversations`)

**布局**: 筛选区 + 表格 + 详情对话框

#### 筛选区
| 元素 | 类型 | 功能 |
|------|------|------|
| **虚拟模型筛选** | 下拉框 | 选择特定模型 |
| **时间范围** | 日期选择 | 日期范围 |
| **关键词搜索** | 输入框 | 搜索对话内容 |
| **消息数量范围** | 数字输入 | 最少/最多消息数 |
| **有知识库引用** | 开关 | 筛选引用知识的对话 |
| **批量删除按钮** | 按钮 | 删除选中的对话（显示选中数量，未选择时禁用） |

#### 表格列
| 列名 | 类型 | 功能 |
|------|------|------|
| **选择** | 多选框 | 批量选择对话 |
| **会话ID** | 文本 | 会话标识 |
| **虚拟模型** | 标签 | 使用的虚拟模型 |
| **消息数** | 数字 | 对话消息数量 |
| **最后时间** | 文本 | 最后活动时间 |
| **操作** | 按钮组 | [查看] [导出] [删除] |

#### 对话详情对话框
```
┌─ 对话详情 ──────────────────┐
│                              │
│  [用户消息]        14:30:05 │
│  你好，请介绍一下自己       │
│                              │
│  [AI回复]          14:30:08 │
│  你好！我是AI助手...        │
│  [知识库引用: 3条]           │
│                              │
│  [系统]            14:30:08 │
│  模型路由: 小模型→大模型     │
│                              │
│  [用户消息]        14:31:12 │
│  ...                        │
│                              │
│ [关闭] [导出JSON] [导出MD]  │
└─────────────────────────────┘
```

---

### 2.12 原始数据模块 (`/admin/raw-data`)

**标签页**
```
[会话原始数据] [多媒体原始数据] [RSS原始数据]
```

#### 会话原始数据标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **虚拟模型** | 下拉框 | 选择模型 |
| **时间范围** | 日期选择 | 日期范围 |
| **关键词** | 输入框 | 搜索内容 |

**列表列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **时间** | 文本 | 记录时间 |
| **类型** | 标签 | 用户输入/AI回复/路由决策/知识检索 |
| **模型** | 文本 | 使用的模型 |
| **操作** | 按钮 | [查看详情] |

#### 多媒体原始数据标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **类型** | 标签页 | [视频] [音频] [文档] |
| **状态** | 下拉框 | 转录中/已完成/失败 |

**列表列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **文件名** | 文本 | 文件名称 |
| **上传时间** | 文本 | 上传时间 |
| **转录文本长度** | 数字 | 文本长度 |
| **操作** | 按钮组 | [查看原始文本] [查看知识] [查看JSON] |

#### RSS原始数据标签

**筛选区**
| 元素 | 类型 | 功能 |
|------|------|------|
| **订阅源** | 下拉框 | 选择RSS源 |
| **时间范围** | 日期选择 | 日期范围 |

**列表列**
| 列名 | 类型 | 功能 |
|------|------|------|
| **标题** | 可点击文本 | 文章标题 |
| **发布时间** | 文本 | 发布时间 |
| **原文链接** | 链接 | 外链图标 |
| **提取状态** | 状态 | 已提取/待处理/失败 |
| **操作** | 按钮组 | [查看原文] [查看知识] [查看JSON] |

#### 详情查看对话框
| 元素 | 类型 | 功能 |
|------|------|------|
| **JSON格式化展示** | 代码编辑器 | 只读，显示完整原始数据 |
| **复制JSON** | 按钮 | 复制到剪贴板 |
| **关闭** | 按钮 | 关闭对话框 |

---

## 3. 组件清单

### 3.1 布局组件
- `AdminLayout.vue` - 后台管理布局（侧边栏+头部）
- `ProxyLayout.vue` - WebChat布局（简洁）
- `Sidebar.vue` - 侧边导航

### 3.2 公共业务组件
- `ModelSelector.vue` - 模型选择器
- `SkillCard.vue` - Skill卡片展示
- `LogViewer.vue` - 日志查看器
- `FileUploader.vue` - 文件上传组件
- `SkillConfigPanel.vue` - Skill配置面板（下拉+开关）
- `TestConnectionButton.vue` - 测试连接按钮
- `KeywordTagInput.vue` - 关键词标签输入组件（支持添加/删除标签，显示计数）

### 3.3 路由配置组件
- `RouterConfig.vue` - 路由配置主页面
- `ForceModeConfig.vue` - 强制模式配置
- `KeywordRulesConfig.vue` - 关键词规则配置
- `SkillRouterConfig.vue` - Skill 路由配置
- `RouterTester.vue` - 路由测试工具

### 3.4 WebChat专用组件
- `ChatMessage.vue` - 单条消息
- `ChatInput.vue` - 输入框
- `ChatHistory.vue` - 历史记录侧边栏
- `ChatSettings.vue` - 设置抽屉

### 3.5 编辑器组件
- `MonacoEditor.vue` - YAML/Markdown编辑器
- `JsonViewer.vue` - JSON格式化展示
- `MarkdownRenderer.vue` - Markdown渲染


### 3.6 Skill编辑器组件
 `SkillEditorDialog.vue` - Skill编辑器主对话框（三栏布局）
 `SkillFileTree.vue` - 文件树组件（支持右键菜单、图标显示）
 `SkillFileTabs.vue` - 多文件标签页组件
 `SkillPreview.vue` - 预览区组件（Markdown渲染、语法高亮）
 `SkillValidationPanel.vue` - 校验状态面板
 `SkillVersionBar.vue` - 版本管理底部栏
 `CreateFileDialog.vue` - 新建文件对话框
 `CreateFolderDialog.vue` - 新建文件夹对话框
 `RenameDialog.vue` - 重命名对话框
 `DeleteConfirmDialog.vue` - 删除确认对话框（支持显示文件夹内容）

---

## 4. 状态管理（Pinia Stores）

```
stores/
├── config.ts           # 系统配置（config.yml缓存）
├── models.ts           # 虚拟模型列表
├── router.ts           # 路由配置（全局路由规则）
├── skills.ts           # Skill状态和重载
├── conversations.ts    # 对话历史
├── knowledge.ts        # 知识库文档
├── media.ts            # 媒体文件队列
├── rss.ts              # RSS订阅和文章
├── logs.ts             # 日志查询状态
└── user.ts             # 用户设置（主题等）
```

---

## 5. API服务层

```
api/
├── axios.ts            # axios实例配置
├── proxy.ts            # /proxy/ai/v1/* 端点
└── admin.ts            # /admin/ai/v1/* 端点
   ├── config.ts        # 配置管理
   ├── models.ts        # 虚拟模型
   ├── router.ts        # 路由配置
   ├── skills.ts        # Skill管理
   ├── conversations.ts # 对话历史
   ├── knowledge.ts     # 知识库
   ├── media.ts         # 媒体处理
   ├── rss.ts           # RSS订阅
   ├── logs.ts          # 日志查询
   └── raw-data.ts      # 原始数据
```

---

## 6. 开发注意事项

1. **所有页面使用暗色主题**
2. **复制功能使用剪贴板API**
3. **SSE流式响应用于对话**
4. **文件上传使用分片上传（大文件）**
5. **表格支持分页和虚拟滚动（大数据量）**
6. **所有编辑操作需要确认对话框**
7. **错误处理统一使用ElMessage.error**
8. **加载状态使用ElLoading**

---

## 7. 测试策略（TDD + 100%覆盖率）

### 7.1 测试驱动开发（TDD）流程

**必须严格遵循TDD红绿重构循环：**

```
1. 编写测试案例（JSON文件） → 2. 运行测试（失败/红色） → 3. 编写组件/页面 → 4. 运行测试（通过/绿色） → 5. 重构优化
```

**前端TDD开发流程：**
1. **需求分析** - 理解页面/组件功能需求
2. **编写测试案例** - 将测试案例保存到JSON文件（与后端测试保持一致）
3. **生成测试代码** - 根据JSON生成Vitest测试代码
4. **运行测试** - 确保测试失败（红色）
5. **编写组件/页面** - 实现功能使测试通过
6. **运行测试** - 确保测试通过（绿色）
7. **重构优化** - 优化代码结构和性能
8. **覆盖率检查** - 确保100%覆盖（行覆盖、函数覆盖、分支覆盖）

### 7.2 测试案例JSON格式

**文件位置**: `test/frontend/cases/{模块}/{功能}.test.json`

**JSON Schema（与后端保持一致）：**
```json
{
  "test_suite": "VirtualModelManager",
  "description": "虚拟模型管理组件测试套件",
  "author": "developer",
  "created_at": "2026-02-24",
  "test_cases": [
    {
      "id": "TC001",
      "name": "test_render_model_list",
      "description": "测试模型列表正确渲染",
      "category": "unit",
      "priority": "P0",
      "tags": ["component", "rendering", "positive"],
      "component": "VirtualModelManager",
      "preconditions": [
        "API返回3个虚拟模型数据"
      ],
      "inputs": {
        "models": [
          {"name": "demo1", "proxy_key_masked": "sk-xxx...abc", "current": "small", "use": true},
          {"name": "demo2", "proxy_key_masked": "sk-yyy...def", "current": "big", "use": false}
        ]
      },
      "expected": {
        "table_row_count": 2,
        "column_names": ["名称", "Proxy Key", "系统URL", "当前模型", "状态", "操作"],
        "first_row_name": "demo1",
        "first_row_status": "启用"
      },
      "assertions": [
        "expect(wrapper.findAll('.el-table__row')).toHaveLength(2)",
        "expect(wrapper.text()).toContain('demo1')",
        "expect(wrapper.text()).toContain('启用')"
      ]
    },
    {
      "id": "TC002",
      "name": "test_click_copy_proxy_key",
      "description": "测试点击复制Proxy Key",
      "category": "unit",
      "priority": "P0",
      "tags": ["component", "interaction", "positive"],
      "component": "VirtualModelManager",
      "preconditions": [
        "组件已挂载",
        "剪贴板API可用"
      ],
      "inputs": {
        "click_target": "第一行的Proxy Key单元格"
      },
      "actions": [
        {"type": "click", "target": ".proxy-key-cell:first"}
      ],
      "expected": {
        "clipboard_content": "sk-xxxxxxxxxxxxxxxx",
        "el_message_success": "已复制到剪贴板"
      },
      "assertions": [
        "expect(navigator.clipboard.writeText).toHaveBeenCalled()",
        "expect(ElMessage.success).toHaveBeenCalledWith('已复制到剪贴板')"
      ]
    },
    {
      "id": "TC003",
      "name": "test_switch_model_type",
      "description": "测试切换模型类型按钮",
      "category": "unit",
      "priority": "P0",
      "tags": ["component", "interaction", "state"],
      "component": "VirtualModelManager",
      "preconditions": [
        "组件已挂载",
        "第一行模型当前为small"
      ],
      "inputs": {
        "row_index": 0,
        "current_model": "small"
      },
      "actions": [
        {"type": "click", "target": ".switch-model-btn:first"}
      ],
      "expected": {
        "api_call": "PUT /admin/ai/v1/models/demo1",
        "api_payload": {"current": "big"},
        "row_display": "big"
      },
      "assertions": [
        "expect(api.put).toHaveBeenCalledWith('/admin/ai/v1/models/demo1', expect.objectContaining({current: 'big'}))",
        "expect(wrapper.text()).toContain('big')"
      ]
    },
    {
      "id": "TC004",
      "name": "test_form_validation_empty_name",
      "description": "测试添加模型时名称为空的验证",
      "category": "unit",
      "priority": "P1",
      "tags": ["component", "validation", "negative"],
      "component": "VirtualModelDialog",
      "preconditions": [
        "对话框已打开"
      ],
      "inputs": {
        "form_data": {
          "name": "",
          "proxy_key": "sk-test",
          "current": "small"
        }
      },
      "actions": [
        {"type": "fill", "target": "input[name='name']", "value": ""},
        {"type": "click", "target": "button[type='submit']"}
      ],
      "expected": {
        "form_valid": false,
        "error_message": "名称不能为空",
        "api_not_called": true
      },
      "assertions": [
        "expect(wrapper.find('.el-form-item__error').exists()).toBe(true)",
        "expect(wrapper.find('.el-form-item__error').text()).toContain('不能为空')",
        "expect(api.post).not.toHaveBeenCalled()"
      ]
    },
    {
      "id": "TC005",
      "name": "test_skill_config_panel_render",
      "description": "测试Skill配置面板渲染",
      "category": "unit",
      "priority": "P1",
      "tags": ["component", "rendering"],
      "component": "SkillConfigPanel",
      "preconditions": [
        "组件已挂载"
      ],
      "inputs": {
        "skill_type": "knowledge",
        "system_enabled": true,
        "system_version": "v1",
        "custom_enabled": false,
        "custom_version": "v2"
      },
      "expected": {
        "system_switch_on": true,
        "system_version_display": "v1",
        "custom_switch_on": false,
        "custom_version_display": "v2"
      },
      "assertions": [
        "expect(wrapper.find('.system-switch').classes()).toContain('is-checked')",
        "expect(wrapper.find('.system-version').text()).toBe('v1')",
        "expect(wrapper.find('.custom-switch').classes()).not.toContain('is-checked')"
      ]
    },
    {
      "id": "TC006",
      "name": "test_api_error_handling",
      "description": "测试API错误处理",
      "category": "integration",
      "priority": "P0",
      "tags": ["api", "error-handling", "negative"],
      "component": "VirtualModelManager",
      "preconditions": [
        "组件已挂载",
        "API返回500错误"
      ],
      "inputs": {
        "api_status": 500,
        "api_error": "Internal Server Error"
      },
      "expected": {
        "el_message_error": "获取模型列表失败",
        "table_empty": true,
        "loading_false": true
      },
      "assertions": [
        "expect(ElMessage.error).toHaveBeenCalled()",
        "expect(wrapper.find('.el-table__empty-text').exists()).toBe(true)",
        "expect(wrapper.find('.el-loading-mask').exists()).toBe(false)"
      ]
    },
    {
      "id": "TC007",
      "name": "test_chat_message_render_markdown",
      "description": "测试聊天消息Markdown渲染",
      "category": "unit",
      "priority": "P1",
      "tags": ["component", "rendering", "markdown"],
      "component": "ChatMessage",
      "preconditions": [
        "组件已挂载"
      ],
      "inputs": {
        "message": {
          "role": "assistant",
          "content": "```python\nprint('hello')\n```"
        }
      },
      "expected": {
        "code_block_exists": true,
        "language_class": "language-python"
      },
      "assertions": [
        "expect(wrapper.find('pre code').exists()).toBe(true)",
        "expect(wrapper.find('code').classes()).toContain('language-python')"
      ]
    },
    {
      "id": "TC008",
      "name": "test_long_text_rendering_performance",
      "description": "测试长文本渲染性能（边界测试）",
      "category": "performance",
      "priority": "P2",
      "tags": ["component", "performance", "boundary"],
      "component": "LogViewer",
      "preconditions": [
        "组件已挂载"
      ],
      "inputs": {
        "logs": [{"message": "x" * 10000}],  // 1万字符
        "count": 100
      },
      "expected": {
        "render_time_ms": 1000,
        "no_lag": true
      },
      "assertions": [
        "expect(renderTime).toBeLessThan(1000)",
        "expect(wrapper.findAll('.log-item')).toHaveLength(100)"
      ]
    },
    {
      "id": "TC009",
      "name": "test_e2e_add_virtual_model",
      "description": "E2E测试：添加虚拟模型完整流程",
      "category": "e2e",
      "priority": "P0",
      "tags": ["e2e", "workflow", "critical"],
      "preconditions": [
        "已登录（无认证，直接访问）",
        "在虚拟模型管理页面"
      ],
      "inputs": {
        "model_data": {
          "name": "test-model",
          "proxy_key": "sk-newkey123",
          "current": "small"
        }
      },
      "actions": [
        {"type": "click", "target": "[data-testid='add-model-btn']"},
        {"type": "fill", "target": "input[name='name']", "value": "test-model"},
        {"type": "fill", "target": "input[name='proxy_key']", "value": "sk-newkey123"},
        {"type": "select", "target": "select[name='current']", "value": "small"},
        {"type": "click", "target": "button[type='submit']"}
      ],
      "expected": {
        "dialog_closed": true,
        "new_model_in_list": true,
        "success_message": "虚拟模型已创建"
      },
      "assertions": [
        "expect(page.locator('text=test-model')).toBeVisible()",
        "expect(page.locator('.el-message--success')).toContainText('已创建')"
      ]
    },
    {
      "id": "TC010",
      "name": "test_responsive_layout_mobile",
      "description": "测试移动端响应式布局（边界测试）",
      "category": "e2e",
      "priority": "P2",
      "tags": ["e2e", "responsive", "boundary"],
      "preconditions": [
        "在WebChat页面"
      ],
      "inputs": {
        "viewport": {"width": 375, "height": 667}  // iPhone SE
      },
      "expected": {
        "sidebar_hidden": true,
        "input_area_visible": true,
        "no_horizontal_scroll": true
      },
      "assertions": [
        "expect(page.locator('.sidebar')).not.toBeVisible()",
        "expect(page.locator('.chat-input')).toBeVisible()"
      ]
    }
  ]
}
```

### 7.3 测试工具与配置

**测试框架**: Vitest（推荐）或 Jest
**E2E测试**: Playwright（推荐）或 Cypress
**组件测试**: Vue Test Utils + @vue/test-utils

**安装依赖：**
```bash
cd frontend
npm install -D vitest @vue/test-utils jsdom @testing-library/vue
npm install -D playwright @playwright/test
npm install -D @vitest/coverage-v8
```

**vitest.config.ts：**
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './reports/coverage',
      exclude: [
        'node_modules/',
        'test/',
        '*.config.ts',
        'src/main.ts'
      ],
      thresholds: {
        lines: 100,
        functions: 100,
        branches: 100,
        statements: 100
      }
    },
    include: ['test/**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', 'dist']
  }
})
```

**playwright.config.ts：**
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './test/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] }
    }
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173'
  }
})
```

### 7.4 测试类型矩阵

| 测试类型 | 目标覆盖率 | 测试重点 | 工具 | 文件位置 |
|---------|-----------|---------|------|---------|
| **单元测试** | 100% | 组件渲染、props、事件、方法 | Vitest + Vue Test Utils | `test/unit/**/*.test.ts` |
| **组件测试** | 100% | 组件交互、状态变化、插槽 | Vitest + @testing-library/vue | `test/component/**/*.test.ts` |
| **集成测试** | 90% | API调用、Pinia状态管理 | Vitest + MSW | `test/integration/**/*.test.ts` |
| **E2E测试** | 核心流程 | 完整用户流程、跨页面交互 | Playwright | `test/e2e/**/*.spec.ts` |
| **视觉回归测试** | 关键页面 | UI一致性、主题切换 | Playwright + 截图对比 | `test/visual/**/*.spec.ts` |
| **边界测试** | 100% | 空值、超长文本、特殊字符 | Vitest | 在JSON中标记`boundary`标签 |
| **性能测试** | 关键组件 | 渲染时间、大数据量处理 | Vitest + Playwright | `test/performance/**/*.test.ts` |

### 7.5 代码质量配置

**ESLint配置** (`.eslintrc.cjs`)：
```javascript
module.exports = {
  root: true,
  env: {
    node: true,
    'vue/setup-compiler-macros': true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier'
  ],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-vars': 'error',
    'vue/require-default-prop': 'error',
    'vue/require-explicit-emits': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'complexity': ['error', 10],  // 圈复杂度限制
    'max-lines-per-function': ['error', { max: 50 }],
    'max-params': ['error', 4]
  },
  overrides: [
    {
      files: ['test/**/*.{js,ts}'],
      rules: {
        'max-lines-per-function': 'off'
      }
    }
  ]
}
```

**TypeScript严格配置** (`tsconfig.json`)：
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "test/**/*.ts"]
}
```

**代码质量检查脚本** (`scripts/quality-check.sh`)：
```bash
#!/bin/bash
set -e

echo "=== 前端代码质量检查 ==="

echo "1. ESLint检查..."
npm run lint

echo "2. TypeScript类型检查..."
npm run type-check

echo "3. 单元测试..."
npm run test:unit -- --coverage --coverageThreshold='{"global":{"branches":100,"functions":100,"lines":100,"statements":100}}'

echo "4. 组件测试..."
npm run test:component

echo "5. E2E测试..."
npm run test:e2e

echo "=== 所有检查通过 ==="
```

### 7.6 测试案例管理

**测试代码生成器** (`test/generate_tests.ts`)：
```typescript
import fs from 'fs/promises'
import path from 'path'
import { compile } from 'handlebars'

const TEMPLATE = `
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import {{ component }} from '@/components/{{ component }}.vue'
import * as api from '@/api/admin/{{ api_module }}'

// Mock依赖
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

vi.mock('@/api/admin/{{ api_module }}')

describe('{{ test_suite }}', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  {{#each test_cases}}
  it('{{ name }} - {{ description }}', async () => {
    // Arrange
    {{#each inputs}}
    const {{ @key }} = {{{json this}}}
    {{/each}}
    
    {{#if api_mock}}
    // Mock API
    vi.mocked(api.{{ api_mock.method }}).mockResolvedValue({{{json api_mock.response }}})
    {{/if}}
    
    // Act
    const wrapper = mount({{ ../component }})
    
    {{#each actions}}
    {{#if (eq type 'fill')}}
    await wrapper.find('{{ target }}').setValue('{{ value }}')
    {{/if}}
    {{#if (eq type 'click')}}
    await wrapper.find('{{ target }}').trigger('click')
    {{/if}}
    {{#if (eq type 'select')}}
    await wrapper.find('{{ target }}').setValue('{{ value }}')
    {{/if}}
    {{/each}}
    
    await flushPromises()
    
    // Assert
    {{#each assertions}}
    {{ this }}
    {{/each}}
  })
  {{/each}}
})
`

async function generateTests() {
  const casesDir = path.join(__dirname, 'cases')
  const outputDir = path.join(__dirname, 'generated')
  
  await fs.mkdir(outputDir, { recursive: true })
  
  const template = compile(TEMPLATE)
  
  // 递归读取所有JSON测试案例
  async function processDir(dir: string) {
    const entries = await fs.readdir(dir, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      
      if (entry.isDirectory()) {
        await processDir(fullPath)
      } else if (entry.name.endsWith('.test.json')) {
        const content = await fs.readFile(fullPath, 'utf-8')
        const testData = JSON.parse(content)
        
        const output = template(testData)
        const relativePath = path.relative(casesDir, fullPath)
        const outputPath = path.join(outputDir, relativePath.replace('.json', '.ts'))
        
        await fs.mkdir(path.dirname(outputPath), { recursive: true })
        await fs.writeFile(outputPath, output)
        
        console.log(`Generated: ${outputPath}`)
      }
    }
  }
  
  await processDir(casesDir)
}

generateTests().catch(console.error)
```

### 7.7 测试数据管理

**Mock数据** (`test/mocks/`):
```
test/mocks/
├── api/
│   ├── models.ts          # 虚拟模型API mock
│   ├── skills.ts          # Skill API mock
│   ├── conversations.ts   # 对话API mock
│   └── ...
├── data/
│   ├── models.json        # 测试用模型数据
│   ├── skills.json        # 测试用Skill数据
│   └── ...
└── server.ts              # MSW server配置
```

### 7.8 测试执行命令

```bash
# 运行所有单元测试
npm run test:unit

# 运行特定组件测试
npm run test:unit -- test/unit/VirtualModelManager.test.ts

# 运行组件测试
npm run test:component

# 运行集成测试
npm run test:integration

# 运行E2E测试
npm run test:e2e

# 运行特定E2E测试
npm run test:e2e -- tests/e2e/models.spec.ts

# 生成覆盖率报告（必须100%）
npm run test:coverage

# 代码质量检查
npm run lint
npm run type-check

# 完整质量检查（CI用）
npm run quality-check
```

### 7.9 测试案例清单要求

| 模块 | 单元测试 | 组件测试 | E2E测试 | 总计 |
|------|---------|---------|---------|------|
| **WebChat** | 30 | 15 | 10 | 55 |
| **Dashboard** | 20 | 10 | 5 | 35 |
| **虚拟模型管理** | 40 | 20 | 15 | 75 |
| **Skill管理** | 35 | 15 | 10 | 60 |
| **知识库** | 40 | 20 | 12 | 72 |
| **媒体处理** | 30 | 15 | 8 | 53 |
| **RSS管理** | 35 | 15 | 10 | 60 |
| **日志查询** | 25 | 10 | 5 | 40 |
| **系统配置** | 30 | 15 | 8 | 53 |
| **原始数据** | 20 | 10 | 5 | 35 |
| **布局/通用** | 20 | 10 | 5 | 35 |
| **总计** | **325** | **155** | **93** | **573** |

**最低测试案例数**: 573个
**目标测试案例数**: 700+个

### 7.10 与后端测试一致性

**保持一致的约定：**
1. **JSON格式一致** - 使用相同的Schema定义
2. **ID命名规范** - 前端使用`F-TC001`，后端使用`B-TC001`
3. **优先级一致** - P0/P1/P2相同定义
4. **标签一致** - `positive`/`negative`/`boundary`/`performance`
5. **TDD流程一致** - 先写JSON → 再写代码
6. **覆盖率要求一致** - 都必须是100%
7. **案例存储位置** - 都使用`test/{backend,frontend}/cases/`目录

**前后端测试联动：**
- 前端E2E测试依赖于后端API
- 使用相同的测试数据（通过Mock或共享数据文件）
- API契约变更时，前后端测试同时更新

---

**文档版本**: 1.0  
**最后更新**: 2026-02-24  
**状态**: 已完成，待API设计确认
