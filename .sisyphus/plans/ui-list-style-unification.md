# UI 样式统一计划 - 列表组件标准化

## 目标
以"知识库"->"文档列表"为标准，统一所有后台列表页面的样式。

## 分析结果

### 当前问题

1. **Dashboard.vue 包含覆盖性样式**（行 489-521）：
   - 自定义 `:deep(.el-tag--success)`、`:deep(.el-tag--danger)`、`:deep(.el-tag--warning)`
   - 自定义 `:deep(.el-button--primary)`
   - 这些样式会覆盖 `dark-blue-theme.css` 中的统一主题样式

2. **各页面按钮和标签使用情况对比**：

| 页面 | 标签 | 按钮 | 状态 |
|------|------|------|------|
| **Knowledge.vue（标准）** | `<el-tag>`、`<el-tag type="success/warning">` | `<el-button link>`、`<el-button link type="primary/danger">` | ✅ |
| VirtualModels.vue | `<el-tag type="success/warning">` | `<el-button link type="primary/danger">` + 普通按钮 | ⚠️ |
| RSS.vue | `<el-tag type="...">` | `<el-button link>`、`<el-button link type="danger">` | ✅ |
| Conversations.vue | `<el-tag>` | `<el-button link type="primary/danger">` | ✅ |
| Dashboard.vue | `<el-tag type="...">` + size="small" | `<el-button link type="primary">` | ⚠️ 有覆盖样式 |

### 标准样式（基于 Knowledge.vue）

**标签使用方式**：
- 默认状态：`<el-tag>文本</el-tag>`
- 成功状态：`<el-tag type="success">文本</el-tag>`
- 警告状态：`<el-tag type="warning">文本</el-tag>`
- 危险状态：`<el-tag type="danger">文本</el-tag>`
- 信息状态：`<el-tag type="info">文本</el-tag>`

**按钮使用方式**：
- 默认链接：`<el-button link>文本</el-button>`
- 主要链接：`<el-button link type="primary">文本</el-button>`
- 危险链接：`<el-button link type="danger">文本</el-button>`

## 需要执行的任务

### 任务 1：删除 Dashboard.vue 的覆盖样式
**文件**: `frontend/src/views/admin/Dashboard.vue`
**操作**: 删除行 493-521 的所有自定义 `:deep()` 样式

```css
/* 删除以下内容 */
/* VS Code style buttons */
:deep(.el-button--primary) {
  background: var(--vscode-blue);
  border-color: var(--vscode-blue);
}

:deep(.el-button--primary:hover) {
  background: var(--vscode-blue-light);
  border-color: var(--vscode-blue-light);
}

:deep(.el-tag--success) {
  background: rgba(76, 175, 80, 0.2);
  border-color: var(--vscode-green);
  color: var(--vscode-green);
}

:deep(.el-tag--danger) {
  background: rgba(244, 67, 54, 0.2);
  border-color: var(--vscode-red);
  color: var(--vscode-red);
}

:deep(.el-tag--warning) {
  background: rgba(255, 152, 0, 0.2);
  border-color: var(--vscode-yellow);
  color: var(--vscode-yellow);
}
```

同时修改行 490：
```css
/* 修改前 */
color: var(--vscode-text);

/* 修改后 */
color: var(--text-primary);
```

### 任务 2：验证所有页面的悬停效果
确保以下文件的列表悬停使用 `var(--bg-hover)`：
- ✅ Knowledge.vue（已修改）
- ✅ VirtualModels.vue（已修改）
- ✅ RSS.vue（已修改）
- ✅ Conversations.vue（已修改）
- ✅ Dashboard.vue（已修改）
- ✅ MediaList.vue（已修改）
- ✅ LogViewer.vue（已修改）

### 任务 3：验证主题文件中的标签样式
**文件**: `frontend/src/styles/dark-blue-theme.css`
**检查**: 确保包含以下样式（应该已有）：

```css
.app-theme .el-tag--success {
  background-color: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--success-400);
}

.app-theme .el-tag--danger {
  background-color: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--error-400);
}

.app-theme .el-tag--warning {
  background-color: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.3);
  color: var(--warning-400);
}

.app-theme .el-tag--info {
  background-color: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
  color: var(--info-400);
}
```

### 任务 4：验证链接按钮样式
**文件**: `frontend/src/styles/dark-blue-theme.css`
**检查**: 确保包含以下样式（应该已有）：

```css
.app-theme .el-button--text {
  background-color: transparent;
  border-color: transparent;
  color: var(--primary-400);
}

.app-theme .el-button--text:hover {
  background-color: var(--bg-selected);
  color: var(--primary-500);
}
```

### 任务 5：检查 VirtualModels.vue 的"切换"按钮
**文件**: `frontend/src/views/admin/VirtualModels.vue` 行 59-65
**检查**: 当前使用普通按钮 `<el-button size="small">`，确保其样式在主题中正常

## 验证清单

- [ ] Dashboard.vue 不再包含 `:deep(.el-tag--*)` 自定义样式
- [ ] Dashboard.vue 不再包含 `:deep(.el-button--primary)` 自定义样式
- [ ] 所有列表页面的悬停效果一致（使用 `--bg-hover`）
- [ ] 所有标签样式一致（使用主题定义的颜色）
- [ ] 所有链接按钮样式一致
- [ ] 刷新浏览器后视觉表现一致

## 部署步骤

1. 执行上述文件修改
2. 重新构建前端容器：`docker-compose -f docker/docker-compose.yml up -d --build frontend`
3. 刷新浏览器验证效果

## 备注

- 所有修改都应使用 CSS 变量，确保主题一致性
- 不要在任何页面中硬编码颜色值
- 保持 Knowledge.vue 的样式作为标准参考
