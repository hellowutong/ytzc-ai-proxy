<template>
  <el-dialog
    v-model="visible"
    :title="`编辑 Skill: ${skillName} (${currentVersion})`"
    width="900px"
    destroy-on-close
    class="skill-editor-dialog"
    fullscreen
  >
    <!-- 校验状态栏 -->
    <div class="validation-status" :class="validationStatusClass">
      <el-icon v-if="validationStatus === 'pending'"><Loading /></el-icon>
      <el-icon v-else-if="validationStatus === 'valid'"><CircleCheck /></el-icon>
      <el-icon v-else-if="validationStatus === 'invalid'"><CircleClose /></el-icon>
      <el-icon v-else-if="validationStatus === 'warning'"><Warning /></el-icon>
      <span>{{ validationStatusText }}</span>
      <el-button 
        v-if="validationErrors.length > 0" 
        link 
        type="primary" 
        @click="showValidationDetails"
      >
        查看详情
      </el-button>
    </div>

    <el-row :gutter="20" class="editor-row">
      <!-- Editor -->
      <el-col :span="12">
        <div class="editor-section">
          <div class="section-header">
            <h4>SKILL.md 内容</h4>
            <div class="editor-actions">
              <el-select v-model="currentVersion" size="small" style="width: 100px; margin-right: 8px;">
                <el-option 
                  v-for="v in availableVersions" 
                  :key="v" 
                  :label="v" 
                  :value="v" 
                />
                <el-option divided value="__new__">+ 新增版本</el-option>
              </el-select>
              <el-button size="small" @click="validateContent" :loading="validating">
                ✓ 校验
              </el-button>
            </div>
          </div>
          <div ref="editorContainer" class="monaco-container"></div>
        </div>
      </el-col>

      <!-- Preview -->
      <el-col :span="12">
        <div class="preview-section">
          <h4>实时预览</h4>
          <div class="preview-content" v-html="renderedContent"></div>
        </div>
      </el-col>
    </el-row>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-button @click="handleSwitchVersion" v-if="availableVersions.length > 1">
            切换版本
          </el-button>
          <el-button type="danger" link @click="handleDeleteVersion" v-if="canDeleteVersion">
            删除此版本
          </el-button>
        </div>
        <div class="footer-right">
          <el-button @click="visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSave"
            :disabled="!canSave"
            :title="saveButtonTitle"
          >
            💾 {{ saveButtonText }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>

  <!-- 校验详情对话框 -->
  <el-dialog
    v-model="showValidationDialog"
    title="校验结果"
    width="600px"
    class="validation-dialog"
  >
    <div v-if="validationErrors.length > 0" class="validation-section">
      <h4 class="error-title">
        <el-icon><CircleClose /></el-icon>
        错误 ({{ validationErrors.length }})
      </h4>
      <div 
        v-for="(error, index) in validationErrors" 
        :key="index"
        class="validation-item error"
        @click="goToErrorLine(error.line, error.column)"
      >
        <div class="error-location">第 {{ error.line }} 行</div>
        <div class="error-message">{{ error.message }}</div>
        <div v-if="error.field" class="error-field">字段: {{ error.field }}</div>
      </div>
    </div>

    <div v-if="validationWarnings.length > 0" class="validation-section">
      <h4 class="warning-title">
        <el-icon><Warning /></el-icon>
        警告 ({{ validationWarnings.length }})
      </h4>
      <div 
        v-for="(warning, index) in validationWarnings" 
        :key="index"
        class="validation-item warning"
      >
        <div class="warning-location">第 {{ warning.line }} 行</div>
        <div class="warning-message">{{ warning.message }}</div>
        <div v-if="warning.suggestion" class="warning-suggestion">
          建议: {{ warning.suggestion }}
        </div>
      </div>
    </div>

    <div v-if="validationErrors.length === 0 && validationWarnings.length === 0" class="validation-success">
      <el-icon :size="48" color="#67C23A"><CircleCheck /></el-icon>
      <p>校验通过，没有发现错误或警告</p>
    </div>

    <template #footer>
      <el-button @click="showValidationDialog = false">关闭</el-button>
      <el-button type="primary" @click="handleFixErrors" v-if="validationErrors.length > 0">
        自动修复
      </el-button>
    </template>
  </el-dialog>

  <!-- 新增版本对话框 -->
  <el-dialog
    v-model="showNewVersionDialog"
    title="新增版本"
    width="400px"
  >
    <el-form label-width="100px">
      <el-form-item label="新版本号">
        <el-input v-model="newVersionInput" placeholder="如: v2, v3" />
      </el-form-item>
      <el-form-item label="复制来源">
        <el-radio-group v-model="copyFromVersion">
          <el-radio label="current">当前版本 ({{ currentVersion }})</el-radio>
          <el-radio v-for="v in otherVersions" :key="v" :label="v">{{ v }}</el-radio>
          <el-radio label="blank">空白模板</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showNewVersionDialog = false">取消</el-button>
      <el-button type="primary" @click="handleCreateNewVersion" :disabled="!newVersionInput">
        创建
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as monaco from 'monaco-editor'
import { marked } from 'marked'

interface ValidationError {
  line: number
  column: number
  field?: string
  message: string
}

interface ValidationWarning {
  line: number
  message: string
  suggestion?: string
}

const props = defineProps<{
  modelValue: boolean
  category: string | undefined
  skill: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', data: { content: string; version: string; isNewVersion: boolean }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const editorContainer = ref<HTMLDivElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const defaultContent = `---
name: ${props.skill?.name || 'skill_name'}
description: Skill描述
type: rule-based
priority: 50
version: "1.0.0"
input_schema:
  type: object
  properties:
    query:
      type: string
output_schema:
  type: object
  properties:
    result:
      type: string
---

# Skill 说明

在这里编写 Skill 的详细说明...

## 输入

- query: 查询字符串

## 输出

- result: 处理结果

## 示例

\`\`\`yaml
input:
  query: "示例查询"
output:
  result: "示例结果"
\`\`\`
`

const content = ref(defaultContent)
const renderedContent = computed(() => {
  // Extract content after frontmatter
  const parts = content.value.split('---')
  if (parts.length >= 3) {
    return marked(parts.slice(2).join('---'))
  }
  return marked(content.value)
})

watch(visible, async (val) => {
  if (val) {
    await nextTick()
    initEditor()
  } else {
    disposeEditor()
  }
})

const initEditor = () => {
  if (!editorContainer.value || editor) return
  
  editor = monaco.editor.create(editorContainer.value, {
    value: content.value,
    language: 'markdown',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    automaticLayout: true,
    wordWrap: 'on'
  })
  
  editor.onDidChangeModelContent(() => {
    content.value = editor?.getValue() || ''
  })
}

const disposeEditor = () => {
  editor?.dispose()
  editor = null
}

// ============== 状态管理 ==============
const validationStatus = ref<'pending' | 'valid' | 'invalid' | 'warning'>('pending')
const validationErrors = ref<ValidationError[]>([])
const validationWarnings = ref<ValidationWarning[]>([])
const validating = ref(false)
const showValidationDialog = ref(false)
const showNewVersionDialog = ref(false)
const newVersionInput = ref('')
const copyFromVersion = ref('current')
const currentVersion = ref('v1')
const availableVersions = ref<string[]>(['v1'])
const hasContentChanged = ref(false)

const skillName = computed(() => props.skill?.name || 'unnamed')

const otherVersions = computed(() => {
  return availableVersions.value.filter(v => v !== currentVersion.value)
})

const canDeleteVersion = computed(() => {
  return availableVersions.value.length > 1
})

const canSave = computed(() => {
  return validationStatus.value === 'valid' || validationStatus.value === 'warning'
})

const saveButtonText = computed(() => {
  if (validationStatus.value === 'pending') return '💾 保存（请先校验）'
  if (validationStatus.value === 'invalid') return '💾 保存（请修复错误）'
  return '💾 保存'
})

const saveButtonTitle = computed(() => {
  if (validationStatus.value === 'pending') return '必须先点击"校验"按钮通过校验才能保存'
  if (validationStatus.value === 'invalid') return '请修复所有错误后才能保存'
  return '保存当前内容'
})

const validationStatusClass = computed(() => {
  return {
    'status-pending': validationStatus.value === 'pending',
    'status-valid': validationStatus.value === 'valid',
    'status-invalid': validationStatus.value === 'invalid',
    'status-warning': validationStatus.value === 'warning'
  }
})

const validationStatusText = computed(() => {
  switch (validationStatus.value) {
    case 'pending': return '待校验 - 请点击"校验"按钮'
    case 'valid': return '✓ 校验通过，可以保存'
    case 'invalid': return `✗ 有 ${validationErrors.value.length} 个错误需要修复`
    case 'warning': return `⚠ 校验通过，但有 ${validationWarnings.value.length} 个警告`
    default: return ''
  }
})

const validateContent = async () => {
  validating.value = true
  validationStatus.value = 'pending'
  
  try {
    const content = editor?.getValue() || ''
    
    // 调用后端校验API
    const response = await fetch('/admin/ai/v1/skills/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      validationErrors.value = result.data.errors || []
      validationWarnings.value = result.data.warnings || []
      
      if (!result.data.valid) {
        validationStatus.value = 'invalid'
      } else if (validationWarnings.value.length > 0) {
        validationStatus.value = 'warning'
      } else {
        validationStatus.value = 'valid'
      }
      
      hasContentChanged.value = false
    }
  } catch (error) {
    ElMessage.error('校验请求失败')
    validationStatus.value = 'invalid'
  } finally {
    validating.value = false
  }
}

const handleSave = async () => {
  if (!canSave.value) {
    ElMessage.warning('请先通过校验才能保存')
    return
  }
  
  const isNewVersion = newVersionInput.value !== ''
  
  emit('save', {
    content: editor?.getValue() || '',
    version: isNewVersion ? newVersionInput.value : currentVersion.value,
    isNewVersion
  })
}

const showValidationDetails = () => {
  showValidationDialog.value = true
}

const goToErrorLine = (line: number, column: number) => {
  editor?.setPosition({ lineNumber: line, column: column })
  editor?.focus()
  showValidationDialog.value = false
}

const handleFixErrors = () => {
  // 自动修复一些常见错误
  ElMessage.info('自动修复功能开发中...')
}

const handleSwitchVersion = () => {
  // 切换版本逻辑
  console.log('Switch version')
}

const handleDeleteVersion = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除版本 ${currentVersion.value} 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    const response = await fetch(
      `/admin/ai/v1/skills/${props.category}/${skillName.value}/versions/${currentVersion.value}`,
      { method: 'DELETE' }
    )
    
    if (response.ok) {
      ElMessage.success('版本已删除')
      // 刷新版本列表
    }
  } catch {
    // 取消删除
  }
}

const handleCreateNewVersion = async () => {
  if (!newVersionInput.value) return
  
  const response = await fetch(
    `/admin/ai/v1/skills/${props.category}/${skillName.value}/versions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        new_version: newVersionInput.value,
        copy_from_version: copyFromVersion.value === 'blank' ? null : copyFromVersion.value
      })
    }
  )
  
  if (response.ok) {
    ElMessage.success('新版本创建成功')
    availableVersions.value.push(newVersionInput.value)
    currentVersion.value = newVersionInput.value
    showNewVersionDialog.value = false
    newVersionInput.value = ''
  }
}

onUnmounted(() => {
  disposeEditor()
})
</script>

<style scoped>
.skill-editor-dialog :deep(.el-dialog) {
  background: #252526;
  margin: 2vh auto !important;
  height: 96vh;
  display: flex;
  flex-direction: column;
}

.skill-editor-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #3C3C3C;
  margin-right: 0;
  padding: 16px 20px;
}

.skill-editor-dialog :deep(.el-dialog__title) {
  color: #CCCCCC;
}

.skill-editor-dialog :deep(.el-dialog__body) {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

.editor-row {
  height: 100%;
}

.editor-section,
.preview-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-section h4,
.preview-section h4 {
  color: #CCCCCC;
  margin-bottom: 12px;
  font-weight: 500;
}

.monaco-container {
  flex: 1;
  border: 1px solid #3C3C3C;
  border-radius: 4px;
  overflow: hidden;
}

.preview-content {
  flex: 1;
  background: #1E1E1E;
  border: 1px solid #3C3C3C;
  border-radius: 4px;
  padding: 20px;
  overflow-y: auto;
  color: #CCCCCC;
  line-height: 1.8;
}

.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3) {
  color: #CCCCCC;
  margin-top: 24px;
  margin-bottom: 16px;
}

.preview-content :deep(code) {
  background: #2D2D30;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Fira Code', monospace;
}

.preview-content :deep(pre) {
  background: #2D2D30;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-left,
.footer-right {
  display: flex;
  gap: 12px;
}

/* 校验状态栏 */
.validation-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  margin-bottom: 16px;
  border-radius: 4px;
  font-size: 14px;
}

.status-pending {
  background: #2D2D30;
  color: #CCCCCC;
  border: 1px solid #3C3C3C;
}

.status-valid {
  background: #1E3A1E;
  color: #67C23A;
  border: 1px solid #67C23A;
}

.status-invalid {
  background: #3A1E1E;
  color: #F56C6C;
  border: 1px solid #F56C6C;
}

.status-warning {
  background: #3A3A1E;
  color: #E6A23C;
  border: 1px solid #E6A23C;
}

/* Section header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  color: #CCCCCC;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Validation dialog */
.validation-dialog :deep(.el-dialog__body) {
  max-height: 60vh;
  overflow-y: auto;
}

.validation-section {
  margin-bottom: 24px;
}

.error-title,
.warning-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.error-title {
  color: #F56C6C;
}

.warning-title {
  color: #E6A23C;
}

.validation-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.validation-item:hover {
  filter: brightness(1.1);
}

.validation-item.error {
  background: rgba(245, 108, 108, 0.1);
  border-left: 4px solid #F56C6C;
}

.validation-item.warning {
  background: rgba(230, 162, 60, 0.1);
  border-left: 4px solid #E6A23C;
}

.error-location,
.warning-location {
  font-size: 12px;
  color: #858585;
  margin-bottom: 4px;
}

.error-message,
.warning-message {
  font-size: 14px;
  color: #CCCCCC;
  margin-bottom: 4px;
}

.error-field,
.warning-suggestion {
  font-size: 12px;
  color: #858585;
}

.validation-success {
  text-align: center;
  padding: 40px;
  color: #67C23A;
}

.validation-success p {
  margin-top: 16px;
  color: #CCCCCC;
}
</style>
