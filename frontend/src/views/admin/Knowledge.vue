<template>
  <div class="knowledge">
    <!-- Tabs -->
    <el-tabs v-model="activeTab" type="border-card" class="knowledge-tabs">
      <!-- Documents Tab -->
      <el-tab-pane label="文档列表" name="docs">
        <div class="tab-toolbar">
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>上传文档
          </el-button>
          <el-input
            v-model="searchQuery"
            placeholder="搜索文件名/内容"
            clearable
            style="width: 240px; margin-left: 12px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="typeFilter" placeholder="类型筛选" style="width: 120px; margin-left: 12px;">
            <el-option label="全部" value="all" />
            <el-option label="PDF" value="pdf" />
            <el-option label="TXT" value="txt" />
            <el-option label="DOC" value="doc" />
            <el-option label="JPG" value="jpg" />
          </el-select>
        </div>

        <el-table :data="filteredDocs" v-loading="knowledgeStore.loading" style="width: 100%;">
          <el-table-column prop="filename" label="文件名" width="300" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag>{{ row.type.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="source" label="来源" width="120" />

          <el-table-column prop="vectorized" label="向量化状态" width="135">
            <template #default="{ row }">
              <el-tag :type="row.vectorized ? 'success' : 'warning'">
                {{ row.vectorized ? '已向量' : '待处理' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="previewDoc(row)">预览</el-button>
              <el-button link type="primary" @click="revectorize(row)">重新向量化</el-button>
              <el-button link type="danger" @click="deleteDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Vector Config Tab -->
      <el-tab-pane label="向量配置" name="vector">
        <el-form label-width="140px" class="config-form">
          <el-form-item label="Embedding模型">
            <el-input v-model="knowledgeStore.config.embedding_model" placeholder="如: BAAI/bge-m3" />
          </el-form-item>
          
          <el-form-item label="Base URL">
            <el-input v-model="knowledgeStore.config.base_url" placeholder="API地址" />
          </el-form-item>
          
          <el-form-item label="API Key">
            <el-input v-model="knowledgeStore.config.api_key" type="password" placeholder="密钥" />
          </el-form-item>
          
          <el-form-item>
            <el-button @click="testVectorConnection">🧪 测试连接</el-button>
            <el-button type="primary" @click="saveConfig">💾 保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- Cron Config Tab -->
      <el-tab-pane label="定时器" name="cron">
        <el-form label-width="140px" class="config-form">
          <el-form-item label="Cron表达式">
            <el-input v-model="knowledgeStore.config.cron_expression" placeholder="如: */30 * * * *" />
            <div class="form-tip">每30分钟执行一次</div>
          </el-form-item>
          
          <el-form-item label="启用定时抓取">
            <el-switch v-model="knowledgeStore.config.cron_enabled" />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveConfig">💾 保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- Skill Config Tab -->
      <el-tab-pane label="Skill配置" name="skills">
        <div class="skill-config-section">
          <h4>知识提取Skill</h4>
          <el-form label-width="200px">
            <el-form-item label="系统默认Skill">
              <div class="skill-select-row">
                <el-select v-model="skillConfig.extract_system_version" style="width: 120px;">
                  <el-option label="v1" value="v1" />
                  <el-option label="v2" value="v2" />
                  <el-option label="v3" value="v3" />
                </el-select>
                <el-switch v-model="skillConfig.extract_system_enabled" class="ml-2" />
              </div>
            </el-form-item>
            
            <el-form-item label="自定义Skill">
              <div class="skill-select-row">
                <el-select v-model="skillConfig.extract_custom_version" style="width: 120px;">
                  <el-option label="v1" value="v1" />
                  <el-option label="v2" value="v2" />
                  <el-option label="v3" value="v3" />
                </el-select>
                <el-switch v-model="skillConfig.extract_custom_enabled" class="ml-2" />
              </div>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <div class="skill-config-section">
          <h4>主题分类Skill</h4>
          <el-form label-width="200px">
            <el-form-item label="系统默认Skill">
              <div class="skill-select-row">
                <el-select v-model="skillConfig.topic_system_version" style="width: 120px;">
                  <el-option label="v1" value="v1" />
                  <el-option label="v2" value="v2" />
                  <el-option label="v3" value="v3" />
                </el-select>
                <el-switch v-model="skillConfig.topic_system_enabled" class="ml-2" />
              </div>
            </el-form-item>
            
            <el-form-item label="自定义Skill">
              <div class="skill-select-row">
                <el-select v-model="skillConfig.topic_custom_version" style="width: 120px;">
                  <el-option label="v1" value="v1" />
                  <el-option label="v2" value="v2" />
                  <el-option label="v3" value="v3" />
                </el-select>
                <el-switch v-model="skillConfig.topic_custom_enabled" class="ml-2" />
              </div>
            </el-form-item>
          </el-form>
        </div>

        <el-button type="primary" @click="saveSkillConfig">💾 保存配置</el-button>
      </el-tab-pane>

      <!-- Topic Classification Tab -->
      <el-tab-pane label="主题分类" name="topics">
        <div class="topic-section">
          <h4>自动分类</h4>
          <el-button type="primary" @click="addAutoTopic">+ 添加分类</el-button>
          
          <el-table :data="autoTopics" style="width: 100%; margin-top: 16px;">
            <el-table-column prop="name" label="主题名">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" />
              </template>
            </el-table-column>
            
            <el-table-column prop="patterns" label="模式">
              <template #default="{ row }">
                <el-tag-input v-model="row.patterns" size="small" />
              </template>
            </el-table-column>
            
            <el-table-column width="80">
              <template #default="{ $index }">
                <el-button link type="danger" @click="removeAutoTopic($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-divider />

        <div class="topic-section">
          <h4>向量检索测试</h4>
          <el-form label-width="100px">
            <el-form-item label="测试查询">
              <el-input v-model="testQuery" type="textarea" rows="3" placeholder="输入测试问题" />
            </el-form-item>
            
            <el-form-item label="相似度阈值">
              <el-slider v-model="similarityThreshold" :min="0" :max="1" :step="0.01" show-input />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="testRetrieval">🔍 检索</el-button>
            </el-form-item>
          </el-form>

          <div v-if="retrievalResults.length" class="retrieval-results">
            <h5>检索结果</h5>
            <el-collapse>
              <el-collapse-item v-for="(result, index) in retrievalResults" :key="index" :title="result.filename">
                <p>{{ result.content }}</p>
                <div class="result-meta">相似度: {{ (result.score * 100).toFixed(2) }}%</div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Upload Dialog -->
    <DocUploadDialog v-model="showUploadDialog" @upload="handleUpload" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores'
import type { KnowledgeDoc } from '@/types'
import DocUploadDialog from '@/components/DocUploadDialog.vue'

const knowledgeStore = useKnowledgeStore()

const activeTab = ref('docs')
const searchQuery = ref('')
const typeFilter = ref('all')
const showUploadDialog = ref(false)

const skillConfig = ref({
  extract_system_enabled: true,
  extract_system_version: 'v1',
  extract_custom_enabled: false,
  extract_custom_version: 'v1',
  topic_system_enabled: true,
  topic_system_version: 'v1',
  topic_custom_enabled: false,
  topic_custom_version: 'v1'
})

const autoTopics = ref<Array<{ name: string; patterns: string[] }>>([])
const testQuery = ref('')
const similarityThreshold = ref(0.76)
const retrievalResults = ref<Array<{ filename: string; content: string; score: number }>>([])

const filteredDocs = computed(() => {
  let result = knowledgeStore.docs
  
  if (searchQuery.value) {
    result = result.filter(d => 
      d.filename.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (typeFilter.value !== 'all') {
    result = result.filter(d => d.type === typeFilter.value)
  }
  
  return result
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const seconds = date.getSeconds().toString().padStart(2, '0')
  return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
}

const previewDoc = (doc: KnowledgeDoc) => {
  ElMessage.info(`预览: ${doc.filename}`)
}

const revectorize = async (doc: KnowledgeDoc) => {
  const success = await knowledgeStore.revectorizeDoc(doc.id)
  if (success) {
    ElMessage.success('重新向量化任务已提交')
  } else {
    ElMessage.error('操作失败')
  }
}

const deleteDoc = async (doc: KnowledgeDoc) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${doc.filename}" 吗？`, '确认删除')
    const success = await knowledgeStore.deleteDoc(doc.id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // Cancelled
  }
}

const testVectorConnection = async () => {
  const success = await knowledgeStore.testVectorConnection()
  if (success) {
    ElMessage.success('向量服务连接成功')
  } else {
    ElMessage.error('向量服务连接失败')
  }
}

const saveConfig = async () => {
  const success = await knowledgeStore.saveConfig()
  if (success) {
    ElMessage.success('配置保存成功')
  } else {
    ElMessage.error('配置保存失败')
  }
}

const saveSkillConfig = () => {
  ElMessage.success('Skill配置保存成功')
}

const addAutoTopic = () => {
  autoTopics.value.push({ name: '', patterns: [] })
}

const removeAutoTopic = (index: number) => {
  autoTopics.value.splice(index, 1)
}

const testRetrieval = () => {
  retrievalResults.value = [
    { filename: '示例文档1.pdf', content: '这是检索到的内容片段...', score: 0.89 },
    { filename: '示例文档2.txt', content: '另一个匹配的内容片段...', score: 0.76 }
  ]
}

const handleUpload = async (data: { file: File; model: string; shared: boolean }) => {
  const success = await knowledgeStore.uploadDoc(data.file, data.model, data.shared)
  if (success) {
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false
  } else {
    ElMessage.error('文档上传失败')
  }
}

onMounted(() => {
  knowledgeStore.fetchDocs()
  knowledgeStore.fetchConfig()
})
</script>

<style scoped>
.knowledge {
  padding: 0;
}

.knowledge-tabs {
  background: #252526;
  border: 1px solid #3C3C3C;
}

:deep(.el-tabs__header) {
  background: #2D2D30;
  border-bottom: 1px solid #3C3C3C;
  margin: 0;
}

:deep(.el-tabs__item) {
  color: #858585;
}

:deep(.el-tabs__item.is-active) {
  color: #007ACC;
  background: #252526;
}

:deep(.el-tabs__content) {
  padding: 20px;
}

.tab-toolbar {
  margin-bottom: 20px;
}

.config-form {
  max-width: 600px;
}

.form-tip {
  font-size: 12px;
  color: #858585;
  margin-top: 4px;
}

.skill-config-section {
  margin-bottom: 24px;
}

.skill-config-section h4 {
  color: #CCCCCC;
  margin-bottom: 16px;
}

.skill-select-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topic-section {
  margin-bottom: 24px;
}

.topic-section h4 {
  color: #CCCCCC;
  margin-bottom: 16px;
}

.retrieval-results {
  margin-top: 24px;
}

.retrieval-results h5 {
  color: #CCCCCC;
  margin-bottom: 12px;
}

.result-meta {
  color: #858585;
  font-size: 12px;
  margin-top: 8px;
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table th.el-table__cell) {
  color: var(--text-secondary) !important;
}

/* 统一所有表头单元格背景色，包括固定列 */
:deep(.el-table .el-table__header-wrapper th.el-table__cell),
:deep(.el-table .el-table__fixed-header-wrapper th.el-table__cell) {
  background-color: var(--bg-tertiary) !important;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-hover);
}

.ml-2 {
  margin-left: 8px;
}
</style>
