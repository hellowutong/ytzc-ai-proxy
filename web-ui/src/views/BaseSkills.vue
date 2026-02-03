<template>
  <div class="baseskills-page">
    <div class="page-header">
      <h2>基础技能模板</h2>
      <div class="header-actions">
        <el-button @click="reloadTemplates" :loading="reloading">
          <el-icon><Refresh /></el-icon>
          重载模板
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="template in templates" :key="template.id">
        <el-card class="template-card" :class="{ disabled: !template.enabled }">
          <template #header>
            <div class="template-header">
              <span>{{ template.name }}</span>
              <el-tag :type="template.enabled ? 'success' : 'info'" size="small">
                {{ template.enabled ? '启用' : '停用' }}
              </el-tag>
            </div>
          </template>
          <p class="template-description">{{ template.description }}</p>
          <div class="template-meta">
            <span>版本: {{ template.version }}</span>
            <span>标签: {{ template.tags?.join(', ') }}</span>
          </div>
          <div class="template-actions">
            <el-button size="small" @click="viewTemplate(template)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button
              size="small"
              :type="template.enabled ? 'warning' : 'success'"
              @click="toggleTemplate(template)"
            >
              {{ template.enabled ? '停用' : '启用' }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-drawer v-model="drawerVisible" title="模板详情" size="60%">
      <div class="template-detail" v-if="currentTemplate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentTemplate.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ currentTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ currentTemplate.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentTemplate.enabled ? 'success' : 'info'">
              {{ currentTemplate.enabled ? '启用' : '停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag v-for="tag in currentTemplate.tags" :key="tag" size="small" style="margin-right: 4px">
              {{ tag }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px;">使用说明</h4>
        <div class="template-content" v-html="currentTemplate.content || '暂无内容'"></div>

        <h4 style="margin: 20px 0 10px;">提示词模板</h4>
        <el-input
          type="textarea"
          :rows="10"
          :model-value="currentTemplate.prompt_template"
          readonly
          class="template-textarea"
        />

        <h4 style="margin: 20px 0 10px;">规则配置</h4>
        <el-input
          type="textarea"
          :rows="6"
          :model-value="currentTemplate.rules"
          readonly
          class="template-textarea"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { baseskillsApi } from '@/api'

const templates = ref([])
const loading = ref(false)
const reloading = ref(false)
const drawerVisible = ref(false)
const currentTemplate = ref(null)

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await baseskillsApi.list()
  } catch (error) {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

async function reloadTemplates() {
  reloading.value = true
  try {
    await baseskillsApi.reload()
    ElMessage.success('模板重载成功')
    loadTemplates()
  } catch (error) {
    ElMessage.error('模板重载失败')
  } finally {
    reloading.value = false
  }
}

function viewTemplate(template) {
  currentTemplate.value = template
  drawerVisible.value = true
}

async function toggleTemplate(template) {
  try {
    if (template.enabled) {
      await baseskillsApi.disable(template.id)
    } else {
      await baseskillsApi.enable(template.id)
    }
    ElMessage.success(`${template.enabled ? '停用' : '启用'}成功`)
    loadTemplates()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style lang="scss" scoped>
.baseskills-page {
  padding: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.template-card {
  margin-bottom: 20px;
  transition: all 0.3s;

  &.disabled {
    opacity: 0.6;
  }

  .template-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .template-description {
    color: var(--text-color-secondary);
    font-size: 14px;
    margin-bottom: 12px;
    min-height: 40px;
  }

  .template-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--text-color-secondary);
    margin-bottom: 16px;
  }

  .template-actions {
    display: flex;
    gap: 8px;
  }
}

.template-detail {
  .template-textarea {
    margin-bottom: 16px;

    :deep(textarea) {
      font-family: 'Consolas', monospace;
      font-size: 12px;
    }
  }
}
</style>
