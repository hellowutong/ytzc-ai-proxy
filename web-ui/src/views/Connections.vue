<template>
  <div class="connections-page">
    <div class="page-header">
      <h2>连接管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加连接
      </el-button>
    </div>

    <el-table :data="connections" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="provider" label="提供商" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.provider }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="base_url" label="API 地址" />
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '活跃' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button-group>
            <el-button size="small" @click="testConnection(row)">
              <el-icon><Connection /></el-icon>
            </el-button>
            <el-button size="small" @click="editConnection(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="deleteConnection(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑连接' : '添加连接'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="连接名称" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择提供商" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Google" value="google" />
            <el-option label="硅基流动" value="siliconflow" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型" prop="model">
          <el-input v-model="form.model" placeholder="gpt-4o" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConnection" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { connectionsApi } from '@/api'

const connections = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  provider: '',
  base_url: '',
  api_key: '',
  model: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

async function loadConnections() {
  loading.value = true
  try {
    connections.value = await connectionsApi.list()
  } catch (error) {
    ElMessage.error('加载连接失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { name: '', provider: '', base_url: '', api_key: '', model: '' })
  dialogVisible.value = true
}

function editConnection(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function saveConnection() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value) {
        await connectionsApi.update(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await connectionsApi.create(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadConnections()
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

async function testConnection(row) {
  try {
    await connectionsApi.test(row.id)
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.error('连接测试失败')
  }
}

async function deleteConnection(row) {
  try {
    await ElMessageBox.confirm('确定删除此连接?', '确认', { type: 'warning' })
    await connectionsApi.delete(row.id)
    ElMessage.success('删除成功')
    loadConnections()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadConnections()
})
</script>

<style lang="scss" scoped>
.connections-page {
  padding: 0;
}
</style>
