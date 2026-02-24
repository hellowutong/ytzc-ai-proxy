<template>
  <el-dialog
    v-model="visible"
    :title="`[${skillType}] Skill 编辑器: ${skillName}`"
    fullscreen
    class="skill-editor-dialog"
    :close-on-click-modal="false"
    destroy-on-close
    @opened="initLayout"
  >
    <div class="editor-layout">
      <!-- Left: File Tree -->
      <div class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="sidebar-header">
          <span>资源管理器</span>
        </div>
        <div class="tree-container">
          <el-tree
            ref="fileTreeRef"
            :data="fileTree"
            node-key="path"
            :props="{ label: 'name', children: 'children', isLeaf: 'leaf' }"
            highlight-current
            :expand-on-click-node="false"
            @node-click="handleNodeClick"
            @node-contextmenu="handleContextMenu"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node" :class="{ 'is-disabled': isNodeDisabled(data) }">
                <el-icon v-if="data.type === 'directory'" class="node-icon"><Folder /></el-icon>
                <el-icon v-else class="node-icon"><Document /></el-icon>
                <span class="node-label">{{ node.label }}</span>
                <span v-if="data.is_dirty" class="dirty-dot">•</span>
              </span>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- Middle: Editor -->
      <div class="editor-main">
        <div class="editor-tabs" v-if="openFiles.length > 0">
          <div 
            v-for="file in openFiles" 
            :key="file.path"
            class="tab-item"
            :class="{ active: activeFilePath === file.path, dirty: file.isDirty }"
            @click="switchFile(file.path)"
            @contextmenu.prevent="handleTabContextMenu($event, file)"
          >
            <span class="tab-icon">
              <el-icon v-if="file.name.endsWith('.md')"><Reading /></el-icon>
              <el-icon v-else-if="file.name.endsWith('.py')"><Operation /></el-icon>
              <el-icon v-else-if="file.name.endsWith('.json')"><Connection /></el-icon>
              <el-icon v-else><Document /></el-icon>
            </span>
            <span class="tab-name">{{ file.name }}</span>
            <span class="tab-close" @click.stop="closeFile(file.path)">
              <el-icon><Close /></el-icon>
            </span>
          </div>
        </div>
        
        <div class="editor-content-area" v-show="openFiles.length > 0">
          <div ref="editorContainer" class="monaco-container"></div>
        </div>

        <div class="empty-editor" v-if="openFiles.length === 0">
          <div class="empty-state">
            <el-icon :size="64"><Edit /></el-icon>
            <p>选择文件开始编辑</p>
            <p class="sub-text">支持 Markdown, Python, JSON, YAML 等格式</p>
          </div>
        </div>
      </div>

      <!-- Right: Preview (Conditional) -->
      <div class="preview-panel" v-if="showPreview && activeFileIsMarkdown">
        <div class="panel-header">
          <span>Markdown 预览</span>
          <div class="actions">
             <el-button link size="small" @click="togglePreview"><el-icon><Close /></el-icon></el-button>
          </div>
        </div>
        <div class="preview-content markdown-body" v-html="previewContent"></div>
      </div>
    </div>

    <template #footer>
      <div class="status-bar">
        <div class="left-status">
          <el-tag size="small" effect="dark" class="version-tag">
            <el-icon><PriceTag /></el-icon> {{ currentVersion }}
          </el-tag>
          <span v-if="activeFilePath" class="file-path">{{ activeFilePath }}</span>
          <span v-if="isSaving" class="saving-status"><el-icon class="is-loading"><Loading /></el-icon> 保存中...</span>
        </div>
        <div class="right-actions">
           <el-button-group>
             <el-button size="small" @click="handleVersionManage">版本管理</el-button>
             <el-button size="small" @click="validateCurrentFile" :loading="isValidating" v-if="props.mode === 'edit'">语法检测</el-button>
             <el-button size="small" @click="togglePreview" v-if="activeFileIsMarkdown">
               {{ showPreview ? '关闭预览' : '打开预览' }}
             </el-button>
             <el-button size="small" type="primary" @click="saveCurrentFile" :disabled="!isCurrentDirty" v-if="props.mode === 'edit'">
               保存 (Ctrl+S)
             </el-button>
           </el-button-group>
        </div>
      </div>
    </template>

    <!-- Context Menus -->
    <div v-show="contextMenu.visible && props.mode === 'edit'" class="context-menu" :style="{ top: contextMenu.top + 'px', left: contextMenu.left + 'px' }">
      <div class="menu-item" @click="openCreateDialog('file', contextMenu.node)">新建文件</div>
      <div class="menu-item" @click="openCreateDialog('folder', contextMenu.node)">新建文件夹</div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="handleRename(contextMenu.node)">重命名</div>
      <div class="menu-item delete" @click="handleDelete(contextMenu.node)">删除</div>
    </div>

    <!-- Dialogs -->
    <el-dialog v-model="createDialog.visible" :title="createDialog.type === 'file' ? '新建文件' : '新建文件夹'" width="400px">
      <el-form @submit.prevent="confirmCreate">
        <el-form-item label="名称">
          <el-input v-model="createDialog.name" ref="createInputRef" placeholder="请输入名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="versionDialog.visible" title="版本管理" width="500px">
      <el-table :data="availableVersions.map(v => ({ version: v }))" style="width: 100%">
        <el-table-column prop="version" label="版本号" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button link type="primary" @click="switchVersion(scope.row.version)" :disabled="scope.row.version === currentVersion">
              {{ scope.row.version === currentVersion ? '当前' : '切换' }}
            </el-button>
            <el-button link type="danger" @click="deleteVersion(scope.row.version)" :disabled="scope.row.version === currentVersion">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="new-version-form">
        <h4>创建新版本</h4>
        <el-input v-model="versionDialog.newVersion" placeholder="新版本号 (例如 v2)" class="input-with-select">
          <template #append>
            <el-button @click="createNewVersion">创建</el-button>
          </template>
        </el-input>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, reactive, markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Folder, DocumentAdd, FolderAdd, Refresh, 
  Close, Edit, Reading, Operation, Connection, PriceTag, Loading 
} from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'
import { marked } from 'marked'
import { 
  getSkillFiles, getFileContent, saveFileContent, 
  createFile, createFolder, renameItem, deleteFile,
  type FileNode
} from '../api/admin/skills'

const props = defineProps<{
  modelValue: boolean
  category: string
  skill: any
  mode?: 'view' | 'edit'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'refresh'): void
  (e: 'save', data: { content: string; version: string; isNewVersion: boolean }): void
}>()

// Layout
const sidebarWidth = ref(240)
const previewWidth = ref(400)
const showPreview = ref(true)

// State
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const fileTree = ref<FileNode[]>([])
const currentVersion = ref('v1')
const availableVersions = ref<string[]>([])
const openFiles = ref<Array<{ path: string, name: string, content: string, is_custom: boolean, isDirty: boolean }>>([])
const activeFilePath = ref<string>('')
const isSaving = ref(false)
const isValidating = ref(false)
const fileTreeRef = ref()

// 极其重要的隔离：Monaco 对象绝不能进入 Vue 的响应式系统，否则会锁死主线程
const monacoModels = new Map<string, monaco.editor.ITextModel>()
const monacoDisposables = new Map<string, monaco.IDisposable>()

// Editor
const editorContainer = ref<HTMLElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

// Context Menu
const contextMenu = reactive({
  visible: false,
  top: 0,
  left: 0,
  node: null as any
})

// Dialogs
const createDialog = reactive({
  visible: false,
  type: 'file' as 'file' | 'folder',
  name: '',
  parentPath: '',
  is_custom: true
})
const createInputRef = ref()

const versionDialog = reactive({
  visible: false,
  newVersion: ''
})

// Computed
const isViewMode = computed(() => props.mode === 'view')
const skillName = computed(() => props.skill?.name || '')
const skillType = computed(() => props.skill?.is_system ? "系统默认" : "自定义")
const activeFile = computed(() => openFiles.value.find(f => f.path === activeFilePath.value))
const isCurrentDirty = computed(() => activeFile.value?.isDirty || false)
const activeFileIsMarkdown = computed(() => activeFile.value?.name.toLowerCase().endsWith('.md'))

const previewContent = computed(() => {
  if (!activeFile.value || !activeFileIsMarkdown.value) return ''
  try {
    return marked(activeFile.value.content)
  } catch (e) {
    return 'Markdown error'
  }
})

// Watchers
watch(visible, async (val) => {
  if (val) {
    currentVersion.value = props.skill?.current_version || 'v1'
    availableVersions.value = props.skill?.all_versions || ['v1']
    await nextTick()
    await refreshTree()
    initEditor()
    
    // 自动定位并展开当前 Skill 目录
    if (props.skill) {
      const targetPath = `${currentVersion.value}/${props.skill.name}`
      console.log('[SkillEditor] Auto-locating skill path:', targetPath)
      
      // 延迟确保树组件已加载数据并渲染
      setTimeout(() => {
        if (fileTreeRef.value) {
          // 1. 展开目标节点及其父节点
          const node = fileTreeRef.value.getNode(targetPath)
          if (node) {
            // 展开当前节点及其所有父节点
            let curr = node
            while (curr) {
              curr.expanded = true
              curr = curr.parent
            }
            
            // 2. 高亮选中的节点
            fileTreeRef.value.setCurrentKey(targetPath)
            
            // 3. 自动尝试打开 SKILL.md
            const skillMdPath = `${targetPath}/SKILL.md`
            const skillMdNode = fileTreeRef.value.getNode(skillMdPath)
            if (skillMdNode) {
              openFile(skillMdNode.data)
            }
          }
        }
      }, 300)
    }
  } else {
    // Cleanup
    monacoDisposables.forEach(d => d.dispose())
    monacoModels.forEach(m => m.dispose())
    monacoDisposables.clear()
    monacoModels.clear()
    openFiles.value = []
    activeFilePath.value = ''
    if (editor) {
      editor.dispose()
      editor = null
    }
  }
})

watch(activeFilePath, (newPath) => {
  if (!editor || !newPath) return
  const model = monacoModels.get(newPath)
  if (model) {
    editor.setModel(model)
    editor.focus()
  }
})

// Methods
const initLayout = () => {}

const initEditor = () => {
  if (!editorContainer.value || editor) return
  
  // 使用 markRaw 确保 editor 本身也不被代理
  editor = markRaw(monaco.editor.create(editorContainer.value, {
    value: '',
    language: 'plaintext',
    theme: 'vs-dark',
    automaticLayout: true,
    readOnly: props.mode === 'view',
    minimap: { enabled: false },
    fontSize: 14,
    scrollBeyondLastLine: false,
    wordWrap: 'on'
  }))

  // Add save command
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
    saveCurrentFile()
  })
}

const refreshTree = async () => {
  if (!props.category || !props.skill) return
  try {
    const isCustom = !props.skill.is_system
    const data = await getSkillFiles(props.category, isCustom)
    if (data && data.files) {
      // 1. 过滤：只保留当前选中的版本目录 (例如只显示 v2)
      const filtered = data.files.filter(vNode => vNode.name === currentVersion.value)
      filtered.forEach(vNode => {
        if (vNode.children) {
          const skillFolders = vNode.children.filter(sNode => sNode.name === props.skill.name)
          if (skillFolders.length === 0) {
            vNode.children = [{
              name: props.skill.name,
              type: 'directory',
              path: `${vNode.name}/${props.skill.name}`,
              editable: true,
              is_custom: isCustom,
              children: []
            }]
          } else {
            vNode.children = skillFolders
          }
        }
      })
      fileTree.value = filtered
    } else {
      fileTree.value = []
    }
  } catch (error) {
    console.error('[SkillEditor] Load tree error:', error)
    ElMessage.error('加载文件树失败')
  }
}
const handleNodeClick = async (data: FileNode) => {
  // 在隔离视图下，所有能看到的节点都是可操作的，除非是版本根目录
  if (data.type === 'directory' && data.path === currentVersion.value) return
  if (data.type === 'file') {
    await openFile(data)
  }
}

// 检查节点是否禁用
const isNodeDisabled = (data: FileNode) => {
  if (!props.skill) return true
  // 版本根目录不允许右键菜单操作（如重命名版本），只允许在其下的 Skill 目录操作
  return data.path === currentVersion.value
}

const openFile = async (node: FileNode) => {
  if (openFiles.value.find(f => f.path === node.path)) {
    activeFilePath.value = node.path
    return
  }

  try {
    console.log('[SkillEditor] Loading file:', node.path)
    const isCustom = node.is_custom !== undefined ? node.is_custom : !props.skill?.is_system
    const res = await getFileContent(props.category, node.path, isCustom)
    
    if (!res) {
      ElMessage.error('无法读取文件内容')
      return
    }
    
    let language = 'plaintext'
    if (node.name.endsWith('.md')) language = 'markdown'
    else if (node.name.endsWith('.py')) language = 'python'
    else if (node.name.endsWith('.json')) language = 'json'

    const uri = monaco.Uri.parse('file:///' + node.path)
    const model = markRaw(monaco.editor.createModel(res.content || '', language, uri))
    
    const path = node.path
    const disposable = markRaw(model.onDidChangeContent(() => {
      const file = openFiles.value.find(f => f.path === path)
      if (file) {
        file.content = model.getValue()
        file.isDirty = true
      }
    }))

    monacoModels.set(path, model)
    monacoDisposables.set(path, disposable)

    openFiles.value.push({
      path: path,
      name: node.name,
      content: res.content || '',
      is_custom: isCustom,
      isDirty: false
    })
    
    nextTick(() => {
      activeFilePath.value = path
    })
  } catch (error) {
    console.error('[SkillEditor] Open file error:', error)
    ElMessage.error('打开文件失败')
  }
}

const closeFile = (path: string) => {
  const index = openFiles.value.findIndex(f => f.path === path)
  if (index === -1) return
  
  const file = openFiles.value[index]
  const model = monacoModels.get(path)
  const disposable = monacoDisposables.get(path)
  if (disposable) disposable.dispose()
  if (model) model.dispose()
  monacoModels.delete(path)
  monacoDisposables.delete(path)
  
  if (file.isDirty) {
    ElMessageBox.confirm('文件未保存，确定要关闭吗？', '提示', {
      confirmButtonText: '关闭',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      openFiles.value.splice(index, 1)
      if (activeFilePath.value === path) {
        activeFilePath.value = openFiles.value.length > 0 ? openFiles.value[openFiles.value.length - 1].path : ''
      }
    }).catch(() => {})
  } else {
    openFiles.value.splice(index, 1)
    if (activeFilePath.value === path) {
      activeFilePath.value = openFiles.value.length > 0 ? openFiles.value[openFiles.value.length - 1].path : ''
    }
  }
}

const switchFile = (path: string) => {
  activeFilePath.value = path
}

const saveCurrentFile = async () => {
  if (!activeFile.value) return
  isSaving.value = true
  try {
    // 这里的 isCustom 逻辑需要和 openFile 保持一致，最好从 meta 信息中获取
    // 简化处理：先尝试当前 skill 类型
    const isCustom = activeFile.value.is_custom
    await saveFileContent({
      category: props.category,
      file_path: activeFile.value.path,
      content: activeFile.value.content,
      is_custom: isCustom
    })
    activeFile.value.isDirty = false
    ElMessage.success("保存成功")
  } catch (error) {
    ElMessage.error("保存失败")
  } finally {
    isSaving.value = false
  }
}

const togglePreview = () => {
  showPreview.value = !showPreview.value
}

const validateCurrentFile = async () => {
  if (!activeFile.value) return
  isValidating.value = true
  try {
    const res = await validateFile(activeFile.value.path, activeFile.value.content)
    if (res.valid) {
      if (res.warnings.length > 0) {
        ElMessage.warning({
          message: `校验通过，但有 ${res.warnings.length} 个建议`,
          duration: 5000
        })
      } else {
        ElMessage.success("校验通过")
      }
    } else {
      const firstError = res.errors[0]
      ElMessage.error(`校验失败: ${firstError.message} (行 ${firstError.line})`)
    }
  } catch (error) {
    ElMessage.error("校验请求失败")
  } finally {
    isValidating.value = false
  }
}

const handleContextMenu = (event: MouseEvent, data: FileNode) => {
  if (isNodeDisabled(data) || props.mode === 'view') return
  event.preventDefault()
  contextMenu.visible = true
  contextMenu.top = event.clientY
  contextMenu.left = event.clientX
  contextMenu.node = data
  document.addEventListener('click', closeContextMenu)
}

const closeContextMenu = () => {
  contextMenu.visible = false
  document.removeEventListener('click', closeContextMenu)
}

const handleTabContextMenu = (event: MouseEvent, file: any) => {}

const openCreateDialog = (type: 'file' | 'folder', node?: FileNode) => {
  createDialog.type = type
  createDialog.visible = true
  createDialog.name = ''
  if (node) {
    createDialog.parentPath = node.type === 'directory' ? node.path : node.path.split('/').slice(0, -1).join('/')
    createDialog.is_custom = node.is_custom !== undefined ? node.is_custom : !props.skill?.is_system
  } else {
    createDialog.parentPath = ''
    createDialog.is_custom = !props.skill?.is_system
  }
  nextTick(() => {
    createInputRef.value?.focus()
  })
}

const confirmCreate = async () => {
  if (!createDialog.name) return
  try {
    const isCustom = createDialog.is_custom
    if (createDialog.type === "file") {
      await createFile({
        category: props.category,
        file_name: createDialog.name,
        parent_path: createDialog.parentPath,
        is_custom: isCustom
      })
    } else {
      await createFolder({
        category: props.category,
        folder_name: createDialog.name,
        parent_path: createDialog.parentPath,
        is_custom: isCustom
      })
    }
    createDialog.visible = false
    refreshTree()
    ElMessage.success("创建成功")
  } catch (error: any) {
    ElMessage.error(error.message || "创建失败")
  }
}

const handleRename = (node: FileNode) => {
  ElMessageBox.prompt('请输入新名称', '重命名', {
    inputValue: node.name,
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(async ({ value }) => {
    if (!value || value === node.name) return
    try {
      const isCustom = node.is_custom !== undefined ? node.is_custom : !props.skill?.is_system
      await renameItem({
        category: props.category,
        old_path: node.path,
        new_name: value,
        is_custom: isCustom
      })
      refreshTree()
    } catch (error: any) {
      ElMessage.error(error.message || '重命名失败')
    }
  })
}

const handleDelete = (node: FileNode) => {
  ElMessageBox.confirm(`确定要删除 ${node.name} 吗？`, '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      const isCustom = node.is_custom !== undefined ? node.is_custom : !props.skill?.is_system
      await deleteFile(props.category, node.path, isCustom)
      closeFile(node.path)
      refreshTree()
      ElMessage.success('删除成功')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleVersionManage = () => {
  versionDialog.visible = true
}

const handleVersionChange = (val: string) => {
  openFiles.value.forEach(f => {
      const m = monacoModels.get(f.path)
      if (m) m.dispose()
      const d = monacoDisposables.get(f.path)
      if (d) d.dispose()
  })
  monacoModels.clear()
  monacoDisposables.clear()
  openFiles.value = []
  activeFilePath.value = ''
  refreshTree()
}

const switchVersion = (ver: string) => {
  currentVersion.value = ver
  handleVersionChange(ver)
  versionDialog.visible = false
}

const createNewVersion = async () => {
  ElMessage.info('创建版本功能需后端支持')
}

const deleteVersion = async (ver: string) => {
  ElMessage.info('删除版本功能需后端支持')
}
</script>

<style scoped>
.skill-editor-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: 70vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}
.editor-layout {
  height: calc(70vh - 60px);
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  background: #252526;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 10px 16px;
  font-size: 18px;
  font-weight: bold;
  color: #bbb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #252526;
}
.tree-container {
  flex: 1;
  overflow-y: auto;
}
.custom-tree-node {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 13px;
  width: 100%;
}
.custom-tree-node.is-disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none; /* 防止点击，但由于 handledNodeClick 也有拦截，这层是双保险 */
}
.node-icon {
  color: #c5c5c5;
}
.dirty-dot {
  margin-left: auto;
  font-size: 48px;
  line-height: 1;
  color: #e6a23c;
}
:deep(.el-tree) {
  background: transparent;
  color: #ccc;
}
:deep(.el-tree-node__content:hover) {
  background-color: #2a2d2e;
}
:deep(.el-tree-node:focus > .el-tree-node__content) {
  background-color: #37373d;
}
.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  min-width: 0;
}
.editor-tabs {
  display: flex;
  background: #252526;
  overflow-x: auto;
  height: 35px;
}
.tab-item {
  display: flex;
  align-items: center;
  padding: 0 10px;
  background: #2d2d2d;
  color: #969696;
  border-right: 1px solid #1e1e1e;
  cursor: pointer;
  min-width: 120px;
  max-width: 200px;
  font-size: 13px;
  user-select: none;
}
.tab-item.active {
  background: #1e1e1e;
  color: #fff;
  border-top: 1px solid #007acc;
}
.tab-item.dirty .tab-name::before {
  content: '●';
  font-size: 8px;
  margin-right: 4px;
  color: #fff;
}
.tab-icon {
  margin-right: 6px;
  display: flex;
  align-items: center;
}
.tab-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tab-close {
  margin-left: 6px;
  opacity: 0;
  border-radius: 3px;
  padding: 2px;
}
.tab-item:hover .tab-close {
  opacity: 1;
}
.tab-close:hover {
  background: #444;
}
.editor-content-area {
  flex: 1;
  position: relative;
}
.monaco-container {
  min-height: 800px;
  width: 100%;
}
.empty-editor {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
}
.empty-state {
  text-align: center;
}
.empty-state .el-icon {
  margin-bottom: 16px;
  color: #333;
}
.sub-text {
  font-size: 18px;
  color: #444;
  margin-top: 8px;
}
.preview-panel {
  flex: 1;
  background: #1e1e1e;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
}
.panel-header {
  height: 35px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #252526;
  color: #bbb;
  font-size: 18px;
  font-weight: bold;
}
.preview-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  color: #ccc;
}
.status-bar {
  height: 60px;
  background: #007acc;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 36px;
  font-size: 12px;
}
.skill-editor-dialog :deep(.el-dialog__footer) {
  padding: 0;
}
.left-status {
  display: flex;
  align-items: center;
  gap: 24px;
}
.version-tag {
  height: 40px;
  padding: 0 16px;
  border: none;
  background: rgba(255,255,255,0.15);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.version-tag:hover {
  background: rgba(255,255,255,0.25);
  transform: translateY(-2px);
}
.version-tag :deep(.el-tag__content) {
  display: flex;
  align-items: center;
  gap: 8px;
}
.version-tag :deep(.el-icon) {
  font-size: 18px;
  display: flex;
  align-items: center;
}
.right-actions {
  display: flex;
  align-items: center;
}
.right-actions .el-button {
  padding: 4px 10px;
  height: 30px;
  font-size: 15px;
  background: transparent;
  border: none;
  color: #fff;
}
.right-actions .el-button:hover {
  background: rgba(255,255,255,0.1);
}
.context-menu {
  position: fixed;
  background: #252526;
  border: 1px solid #454545;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  z-index: 9999;
  min-width: 160px;
  padding: 4px 0;
}
.menu-item {
  padding: 6px 16px;
  cursor: pointer;
  color: #ccc;
  font-size: 13px;
}
.menu-item:hover {
  background: #094771;
  color: #fff;
}
.menu-divider {
  height: 1px;
  background: #454545;
  margin: 4px 0;
}
.menu-item.delete:hover {
  background: #8b0000;
}
.markdown-body {
  font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;
  font-size: 18px;
  line-height: 1.6;
}
.markdown-body :deep(h1), .markdown-body :deep(h2) {
  border-bottom: 1px solid #333;
  padding-bottom: 0.3em;
}
.markdown-body :deep(code) {
  background-color: rgba(110,118,129,0.4);
  border-radius: 6px;
  padding: 0.2em 0.4em;
}
.markdown-body :deep(pre) {
  background-color: #161b22;
  padding: 16px;
  border-radius: 6px;
  overflow: auto;
}
</style>
