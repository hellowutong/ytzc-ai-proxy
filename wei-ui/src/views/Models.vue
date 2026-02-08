<template>
  <div class="models-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>虚拟模型管理</span>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col 
          v-for="model in virtualModels" 
          :key="model.id" 
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="6"
          class="model-col"
        >
          <el-card class="model-card" shadow="hover">
            <div class="model-header">
              <el-avatar :size="50" :icon="ChatDotRound" :style="{ backgroundColor: getAvatarColor(model.name) }" />
              <div class="model-title">
                <h3>{{ model.name }}</h3>
                <el-tag size="small" :type="model.enabled ? 'success' : 'info'">
                  {{ model.enabled ? '已启用' : '已禁用' }}
                </el-tag>
              </div>
            </div>
            
            <div class="model-info">
              <p><strong>ID:</strong> {{ model.id }}</p>
              <p><strong>基础模型:</strong> {{ model.base_model || '-' }}</p>
              <p><strong>描述:</strong> {{ model.description || '无描述' }}</p>
              <p><strong>创建时间:</strong> {{ formatTime(model.created_at) }}</p>
            </div>

            <div class="model-actions">
              <el-button type="primary" link @click="editModel(model)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button type="danger" link @click="deleteModel(model)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="!virtualModels.length" description="暂无虚拟模型" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模型' : '添加模型'"
      width="600px"
    >
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型ID" prop="id" v-if="!isEdit">
          <el-input v-model="form.id" placeholder="请输入唯一标识符" />
        </el-form-item>
        <el-form-item label="基础模型" prop="base_model">
          <el-select v-model="form.base_model" placeholder="选择基础模型" style="width: 100%">
            <el-option
              v-for="model in baseModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入模型描述"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Edit, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { request } from '@/api/request'

interface VirtualModel {
  id: string
  name: string
  base_model?: string
  description?: string
  enabled: boolean
  created_at: string
  updated_at: string
  config?: Record<string, any>
}

const virtualModels = ref<VirtualModel[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const baseModels = ref([
  'gpt-4',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'claude-3-opus',
  'claude-3-sonnet',
  'claude-3-haiku'
])

const form = ref<Partial<VirtualModel>>({
  id: '',
  name: '',
  base_model: '',
  description: '',
  enabled: true
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  id: [
    { required: true, message: '请输入模型ID', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]+$/, message: '只能包含小写字母、数字、下划线和横线', trigger: 'blur' }
  ],
  base_model: [
    { required: true, message: '请选择基础模型', trigger: 'change' }
  ]
}

// 模拟数据
const mockModels: VirtualModel[] = [
  {
    id: 'my-gpt4',
    name: '我的GPT-4',
    base_model: 'gpt-4',
    description: '自定义的GPT-4模型，用于日常对话',
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'coding-assistant',
    name: '编程助手',
    base_model: 'claude-3-sonnet',
    description: '专门用于编程辅助的虚拟模型',
    enabled: true,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString()
  }
]

const getAvatarColor = (name: string): string => {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#8E44AD']
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const formatTime = (timestamp: string | undefined): string => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const fetchModels = async () => {
  try {
    // const res = await request.get('/models')
    // virtualModels.value = res.data.data
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 300))
    virtualModels.value = mockModels
  } catch (error) {
    ElMessage.error('获取模型列表失败')
    console.error('Fetch models error:', error)
  }
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    id: '',
    name: '',
    base_model: '',
    description: '',
    enabled: true
  }
  dialogVisible.value = true
}

const editModel = (model: VirtualModel) => {
  isEdit.value = true
  form.value = { ...model }
  dialogVisible.value = true
}

const deleteModel = async (model: VirtualModel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // await request.delete(`/models/${model.id}`)
    virtualModels.value = virtualModels.value.filter(m => m.id !== model.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete model error:', error)
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          // await request.put(`/models/${form.value.id}`, form.value)
          const index = virtualModels.value.findIndex(m => m.id === form.value.id)
          if (index > -1) {
            virtualModels.value[index] = {
              ...virtualModels.value[index],
              ...form.value,
              updated_at: new Date().toISOString()
            } as VirtualModel
          }
          ElMessage.success('更新成功')
        } else {
          // await request.post('/models', form.value)
          const newModel: VirtualModel = {
            ...form.value as VirtualModel,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
          virtualModels.value.push(newModel)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
      } catch (error) {
        ElMessage.error(isEdit.value ? '更新失败' : '添加失败')
        console.error('Submit error:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchModels()
})
</script>

<style scoped lang="scss">
.models-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-col {
  margin-bottom: 20px;
}

.model-card {
  height: 100%;
  
  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    height: calc(100% - 60px);
  }
}

.model-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  
  .model-title {
    h3 {
      margin: 0 0 5px 0;
      font-size: 16px;
    }
  }
}

.model-info {
  flex: 1;
  
  p {
    margin: 8px 0;
    font-size: 14px;
    color: var(--el-text-color-regular);
    
    strong {
      color: var(--el-text-color-primary);
    }
  }
}

.model-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>