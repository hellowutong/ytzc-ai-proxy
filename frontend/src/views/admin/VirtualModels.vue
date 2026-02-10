<template>
  <div class="virtual-models">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>添加模型
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索模型名称"
        clearable
        style="width: 240px; margin-left: 12px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px; margin-left: 12px;">
        <el-option label="全部" value="all" />
        <el-option label="启用" value="enabled" />
        <el-option label="禁用" value="disabled" />
      </el-select>
    </div>

    <!-- Models Table -->
    <el-card class="table-card" v-loading="modelStore.loading">
      <el-table :data="filteredModels" style="width: 100%">
        <el-table-column prop="name" label="名称" width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="copyToClipboard(row.name)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="proxy_key" label="Proxy Key" width="400">
          <template #default="{ row }">
            <div class="proxy-key-cell">
              <span>{{ maskKey(row.proxy_key) }}</span>
              <el-button link @click="copyToClipboard(row.proxy_key)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="系统URL" width="580">
          <template #default="{ row }">
            <el-link type="info" @click="copyToClipboard(getSystemUrl(row.name))">
              {{ getSystemUrl(row.name) }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column label="当前模型" width="260">
          <template #default="{ row }">
            <div class="current-model-cell">
              <el-tag :type="row.current === 'small' ? 'success' : 'warning'">
                {{ row.current === 'small' ? '小模型' : '大模型' }}
              </el-tag>
              <el-button 
                size="small" 
                @click="handleSwitchModel(row)"
                :disabled="row.force_current"
              >
                切换
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-switch
              v-model="row.use"
              @change="(val: boolean) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button 
              link 
              type="success" 
              @click="testModel(row)"
              :loading="testingModels[row.name]"
            >
              <el-icon><Connection /></el-icon>模型测试
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <ModelDialog
      v-model="showAddDialog"
      :model="editingModel"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, CopyDocument, Connection } from '@element-plus/icons-vue'
import { useModelStore } from '@/stores'
import type { VirtualModel } from '@/types'
import ModelDialog from '@/components/ModelDialog.vue'

const modelStore = useModelStore()
const searchQuery = ref('')
const statusFilter = ref('all')
const showAddDialog = ref(false)
const editingModel = ref<VirtualModel | null>(null)

// 模型测试状态
const testingModels = ref<Record<string, boolean>>({})
const testResults = ref<Record<string, { small: boolean; big: boolean; smallMsg?: string; bigMsg?: string }>>({})

const filteredModels = computed(() => {
  let result = modelStore.models
  
  if (searchQuery.value) {
    result = result.filter(m => 
      m.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (statusFilter.value !== 'all') {
    result = result.filter(m => 
      statusFilter.value === 'enabled' ? m.use : !m.use
    )
  }
  
  return result
})

const maskKey = (key: string) => {
  if (key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

const getSystemUrl = (name: string) => {
  return `http://localhost:8000/proxy/ai/v1/chat/completions?model=${name}`
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const handleStatusChange = async (model: VirtualModel, enabled: boolean) => {
  const success = await modelStore.updateModel(model.name, { use: enabled })
  if (success) {
    ElMessage.success(enabled ? '模型已启用' : '模型已禁用')
  } else {
    model.use = !enabled
    ElMessage.error('操作失败')
  }
}

const handleSwitchModel = async (model: VirtualModel) => {
  const newSize = model.current === 'small' ? 'big' : 'small'
  const success = await modelStore.switchModel(model.name, newSize)
  if (success) {
    ElMessage.success(`已切换到${newSize === 'small' ? '小' : '大'}模型`)
  } else {
    ElMessage.error('切换失败')
  }
}

const handleEdit = (model: VirtualModel) => {
  editingModel.value = { ...model }
  showAddDialog.value = true
}

const handleDelete = async (model: VirtualModel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const success = await modelStore.deleteModel(model.name)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // Cancelled
  }
}

const handleSubmit = async (modelData: Partial<VirtualModel>, originalName?: string) => {
  // 检查名称唯一性
  if (modelData.name) {
    const isDuplicate = modelStore.models.some(m => 
      m.name === modelData.name && 
      m.name !== (originalName || editingModel.value?.name)
    )
    if (isDuplicate) {
      ElMessage.error(`模型名称 "${modelData.name}" 已存在，请使用其他名称`)
      return
    }
  }

  let success
  if (editingModel.value) {
    // 使用原始名称更新（可能名称已变更）
    const targetName = originalName || editingModel.value.name
    success = await modelStore.updateModel(targetName, modelData)
  } else {
    // 创建时检查名称是否已存在
    const isNameExists = modelStore.models.some(m => m.name === modelData.name)
    if (isNameExists) {
      ElMessage.error(`模型名称 "${modelData.name}" 已存在，请使用其他名称`)
      return
    }
    success = await modelStore.createModel(modelData as Omit<VirtualModel, 'proxy_key'>)
  }
  
  if (success) {
    ElMessage.success(editingModel.value ? '更新成功' : '创建成功')
    showAddDialog.value = false
    editingModel.value = null
  } else {
    ElMessage.error(editingModel.value ? '更新失败' : '创建失败')
  }
}

// 测试单个模型连接
const testModelConnection = async (modelConfig: { model: string; api_key: string; base_url: string }): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await fetch('/admin/ai/v1/models/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(modelConfig)
    })
    const result = await response.json()
    if (result.code === 200) {
      return { success: true, message: '连接成功' }
    } else {
      return { success: false, message: result.message || '连接失败' }
    }
  } catch (error) {
    return { success: false, message: '网络错误' }
  }
}

// 测试模型（同时测试大小模型）
const testModel = async (model: VirtualModel) => {
  testingModels.value[model.name] = true
  
  try {
    ElMessage.info(`开始测试模型 "${model.name}"...`)
    
    // 同时测试小模型和大模型
    const [smallResult, bigResult] = await Promise.all([
      testModelConnection(model.small),
      testModelConnection(model.big)
    ])
    
    // 保存测试结果
    testResults.value[model.name] = {
      small: smallResult.success,
      big: bigResult.success,
      smallMsg: smallResult.message,
      bigMsg: bigResult.message
    }
    
    // 显示测试结果
    const smallStatus = smallResult.success ? '✅' : '❌'
    const bigStatus = bigResult.success ? '✅' : '❌'
    
    await ElMessageBox.alert(
      `<div style="line-height: 1.8;">
        <p><strong>模型测试完成 - ${model.name}</strong></p>
        <p>${smallStatus} <strong>小模型</strong> (${model.small.model || '未配置'})</p>
        <p style="margin-left: 24px; color: ${smallResult.success ? '#67c23a' : '#f56c6c'};">${smallResult.message}</p>
        <p>${bigStatus} <strong>大模型</strong> (${model.big.model || '未配置'})</p>
        <p style="margin-left: 24px; color: ${bigResult.success ? '#67c23a' : '#f56c6c'};">${bigResult.message}</p>
      </div>`,
      '模型测试结果',
      {
        confirmButtonText: '确定',
        dangerouslyUseHTMLString: true,
        type: smallResult.success && bigResult.success ? 'success' : smallResult.success || bigResult.success ? 'warning' : 'error'
      }
    )
  } catch (error) {
    ElMessage.error('测试过程发生错误')
  } finally {
    testingModels.value[model.name] = false
  }
}

onMounted(() => {
  modelStore.fetchModels()
})
</script>

<style scoped>
.virtual-models {
  padding: 0;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.table-card {
  background: #252526;
  border: 1px solid #3C3C3C;
}

.proxy-key-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-model-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
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

/* 统一"操作"列和"状态"列表头的背景色 */
:deep(.el-table .el-table__header-wrapper th.el-table__cell),
:deep(.el-table .el-table__fixed-header-wrapper th.el-table__cell) {
  background-color: var(--bg-tertiary) !important;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-hover);
}
</style>
