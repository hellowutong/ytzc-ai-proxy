# Skill 编辑器崩溃修复计划

## 问题描述
前端在打开 `v1/demo/SKILL.md` 时卡死，必须重启 Docker。

## 根本原因

### Bug 1: 错误的 API 参数
- 文件树显示分类下**所有 Skills**（system + custom 混合）
- 但 `getFileContent` 调用使用 `props.skill?.is_system`（对话框打开时固定）
- 当点击不同类型的 Skill 文件时，API 返回 404，但前端没有正确处理

### Bug 2: Monaco Editor 内存泄漏
- `model.onDidChangeContent` 监听器没有正确清理
- 全局 `editor.onDidChangeModelContent` 可能与 Vue 响应式形成循环
- 缺少 null 检查导致 Monaco 内部错误

## 修复内容

### 1. 修复 openFile 函数 (SkillEditorDialog.vue:327-373)

**当前问题代码：**
```typescript
const openFile = async (node: FileNode) => {
  // ... 检查已打开文件 ...
  
  const isCustom = !props.skill?.is_system  // ❌ 固定值，不适用于其他 skill
  const res = await getFileContent(props.category, node.path, isCustom)
  
  if (res) {  // ❌ 没有 else 处理，res 为 null 时静默失败
    // ... 创建模型 ...
    model.onDidChangeContent(() => {  // ❌ 内存泄漏风险
      // ...
    })
  }
}
```

**修复后代码：**
```typescript
const openFile = async (node: FileNode) => {
  // 检查是否已打开
  const existing = openFiles.value.find(f => f.path === node.path)
  if (existing) {
    activeFilePath.value = node.path
    return
  }

  try {
    // 从文件路径提取 skillName (格式: v1/skillName/file.md)
    const pathParts = node.path.split('/')
    const skillName = pathParts.length > 1 ? pathParts[1] : ''
    
    // 先尝试使用当前 skill 的类型
    let isCustom = !props.skill?.is_system
    let res = await getFileContent(props.category, node.path, isCustom)
    
    // 如果失败且是不同 skill，尝试相反类型
    if (!res && skillName !== props.skill?.name) {
      isCustom = !isCustom
      res = await getFileContent(props.category, node.path, isCustom)
    }
    
    // ✅ 明确处理 404 错误
    if (!res) {
      ElMessage.error('文件不存在或无法访问')
      return
    }
    
    // ... 创建模型 ...
    
    // ✅ 保存 disposable 以便后续清理
    const disposable = model.onDidChangeContent(() => {
      const file = openFiles.value.find(f => f.path === node.path)
      if (file && file.model) {
        file.content = file.model.getValue()
        file.isDirty = true
      }
    })

    // ✅ 添加 disposable 到文件对象
    openFiles.value.push({
      path: node.path,
      name: node.name,
      content: res.content || '',
      isDirty: false,
      model: model,
      disposable: disposable  // ✅ 保存引用
    })
    
    activeFilePath.value = node.path
  } catch (error) {
    console.error('打开文件失败:', error)
    ElMessage.error('无法打开文件')
  }
}
```

### 2. 修复 closeFile 函数 - 添加 disposable 清理

在 `closeFile` 函数中添加：
```typescript
const closeFile = (path: string) => {
  const index = openFiles.value.findIndex(f => f.path === path)
  if (index === -1) return
  
  const file = openFiles.value[index]
  
  // ✅ 清理 Monaco 监听器
  if (file.disposable) {
    file.disposable.dispose()
  }
  if (file.model) {
    file.model.dispose()
  }
  
  // ... 原有逻辑 ...
}
```

### 3. 修复组件卸载时的清理

在 `watch(visible, ...)` 的清理逻辑中添加：
```typescript
} else {
  // Cleanup
  openFiles.value.forEach(file => {
    file.disposable?.dispose()
    file.model?.dispose()
  })
  openFiles.value = []
  activeFilePath.value = ''
  if (editor) {
    editor.dispose()
    editor = null
  }
}
```

### 4. 更新类型定义

在 `openFiles` 类型中添加 `disposable`：
```typescript
const openFiles = ref<Array<{
  path: string
  name: string
  content: string
  isDirty: boolean
  model?: monaco.editor.ITextModel
  disposable?: monaco.IDisposable  // ✅ 新增
}>>([])
```

## 修复验证步骤

1. 打开 Skill 编辑器
2. 点击 system skill（如 default）的文件 - 应正常打开
3. 点击 custom skill（如 demo）的文件 - 应正常打开，不卡死
4. 关闭文件标签 - 应正常关闭，无内存泄漏
5. 关闭对话框 - 应清理所有资源

## Docker 部署

修复后需要重新构建前端镜像：
```bash
docker-compose -f docker/docker-compose.yml build --no-cache frontend
docker-compose -f docker/docker-compose.yml up -d frontend
```
