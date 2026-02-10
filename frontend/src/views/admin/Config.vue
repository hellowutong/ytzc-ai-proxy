<template>
  <div class="config">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>系统配置 (config.yml)</span>
          <el-button-group>
            <el-button type="primary" @click="saveConfig">
              <el-icon><Check /></el-icon>保存
            </el-button>
            <el-button @click="reloadConfig">
              <el-icon><Refresh /></el-icon>重载
            </el-button>
          </el-button-group>
        </div>
      </template>
      
      <div ref="editorContainer" class="editor-container"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Refresh } from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'
import { useConfigStore } from '@/stores'

const configStore = useConfigStore()
const editorContainer = ref<HTMLDivElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const defaultConfig = `# AI Gateway Configuration
# 注意: 此文件通过UI编辑，请勿直接修改文件

ai-gateway:
  virtual_models: {}
  
  databases:
    mongodb:
      host: localhost
      port: 27017
      database: ai_gateway
    redis:
      host: localhost
      port: 6379
      db: 0
    qdrant:
      host: localhost
      port: 6333
      collection: documents
  
  search:
    searxng:
      enabled: true
      url: http://localhost:8080
    librex:
      enabled: true
      url: http://localhost:8081
    fourget:
      enabled: true
      url: http://localhost:8082
`

onMounted(() => {
  if (editorContainer.value) {
    editor = monaco.editor.create(editorContainer.value, {
      value: configStore.rawYaml || defaultConfig,
      language: 'yaml',
      theme: 'vs-dark',
      minimap: { enabled: false },
      fontSize: 14,
      lineNumbers: 'on',
      roundedSelection: false,
      scrollBeyondLastLine: false,
      readOnly: false,
      automaticLayout: true
    })
  }
})

onUnmounted(() => {
  editor?.dispose()
})

const saveConfig = async () => {
  if (!editor) return
  
  const yaml = editor.getValue()
  const success = await configStore.saveRawYaml(yaml)
  
  if (success) {
    ElMessage.success('配置保存成功')
  } else {
    ElMessage.error('配置保存失败')
  }
}

const reloadConfig = async () => {
  const success = await configStore.reloadConfig()
  
  if (success) {
    await configStore.fetchConfig()
    if (editor) {
      editor.setValue(configStore.rawYaml || defaultConfig)
    }
    ElMessage.success('配置重载成功')
  } else {
    ElMessage.error('配置重载失败')
  }
}
</script>

<style scoped>
.config {
  padding: 0;
  height: calc(100vh - 140px);
}

.config-card {
  background: #252526;
  border: 1px solid #3C3C3C;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-container {
  height: calc(100vh - 240px);
  border: 1px solid #3C3C3C;
  border-radius: 4px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
  color: #CCCCCC;
}

:deep(.el-card__body) {
  height: calc(100% - 60px);
  padding: 12px;
}
</style>
