<template>
  <el-dialog
    v-model="visible"
    title="编辑 Skill"
    width="900px"
    destroy-on-close
    class="skill-editor-dialog"
    fullscreen
  >
    <el-row :gutter="20" class="editor-row">
      <!-- Editor -->
      <el-col :span="12">
        <div class="editor-section">
          <h4>SKILL.md</h4>
          <div ref="editorContainer" class="monaco-container"></div>
        </div>
      </el-col>

      <!-- Preview -->
      <el-col :span="12">
        <div class="preview-section">
          <h4>预览</h4>
          <div class="preview-content" v-html="renderedContent"></div>
        </div>
      </el-col>
    </el-row>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button @click="validateContent">✓ 验证</el-button>
        <el-button type="primary" @click="handleSave">💾 保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as monaco from 'monaco-editor'
import { marked } from 'marked'

const props = defineProps<{
  modelValue: boolean
  category: string | undefined
  name: string | undefined
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', content: string): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const editorContainer = ref<HTMLDivElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const defaultContent = `---
name: ${props.name || 'skill_name'}
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

const validateContent = () => {
  // Simple YAML frontmatter validation
  const text = editor?.getValue() || ''
  const frontmatterMatch = text.match(/^---\n([\s\S]*?)\n---/)
  
  if (!frontmatterMatch) {
    ElMessage.error('未找到YAML frontmatter')
    return false
  }
  
  try {
    // Basic validation - check for required fields
    const frontmatter = frontmatterMatch[1]
    const required = ['name:', 'description:', 'type:', 'version:']
    const missing = required.filter(field => !frontmatter.includes(field))
    
    if (missing.length > 0) {
      ElMessage.error(`缺少必填字段: ${missing.join(', ')}`)
      return false
    }
    
    ElMessage.success('验证通过')
    return true
  } catch (e) {
    ElMessage.error('YAML格式错误')
    return false
  }
}

const handleSave = () => {
  if (!validateContent()) return
  emit('save', editor?.getValue() || '')
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
  justify-content: flex-end;
  gap: 12px;
}
</style>
