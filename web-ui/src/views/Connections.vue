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
      <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip />
      <el-table-column label="代理地址" min-width="200">
        <template #default="{ row }">
          <el-link 
            type="primary" 
            @click="copyToClipboard('http://localhost:8080/proxy/v1/')"
          >
            <span class="proxy-url">http://localhost:8080/proxy/v1/</span>
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="proxy_key" label="Proxy Key" min-width="180" show-overflow-tooltip />
      <el-table-column label="小模型" width="120">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ row.small_model?.name || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="大模型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ row.big_model?.name || '-' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.status"
            active-value="enabled"
            inactive-value="disabled"
            @change="toggleStatus(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-tooltip content="测试连接">
              <el-button size="small" @click="testConnection(row)">
                <el-icon><Connection /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="编辑">
              <el-button size="small" @click="editConnection(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除">
              <el-button size="small" type="danger" @click="deleteConnection(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑连接' : '添加连接'"
      width="750px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如: SiliconFlow DeepSeek" />
        </el-form-item>
        <el-form-item label="Proxy Key" prop="proxy_key">
          <el-input v-model="form.proxy_key" readonly>
            <template #prepend>
              <el-button @click="copyToClipboard(form.proxy_key)" title="复制">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </template>
            <template #append>
              <el-button @click="generateProxyKey" title="重新生成">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="form-tip">点击左侧复制，点击右侧刷新重新生成</div>
        </el-form-item>

        <el-divider content-position="left">
          小模型配置
          <el-tag size="small" type="info" style="margin-left: 10px;">优先使用</el-tag>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="模型名称" prop="small_model.name">
              <el-input v-model="form.small_model.name" placeholder="例如: deepseek-ai/DeepSeek-R1-0528-Qwen3-8B" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="API Base URL" prop="small_model.base_url">
              <el-input v-model="form.small_model.base_url" placeholder="例如: https://api.siliconflow.cn/v1" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="API Key" prop="small_model.api_key">
              <el-input v-model="form.small_model.api_key" type="password" show-password placeholder="sk-..." />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="">
              <el-button 
                type="primary" 
                :loading="testingSmall"
                @click="testProviderModel('small')"
              >
                <el-icon><Connection /></el-icon>
                测试小模型
              </el-button>
              <span v-if="testResults.small" :class="testResults.small.status === 'success' ? 'test-success' : 'test-fail'">
                {{ testResults.small.message }}
              </span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">
          大模型配置
          <el-tag size="small" type="warning" style="margin-left: 10px;">备用</el-tag>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="模型名称" prop="big_model.name">
              <el-input v-model="form.big_model.name" placeholder="例如: deepseek-ai/DeepSeek-V3-0324 (可选)" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="API Base URL" prop="big_model.base_url">
              <el-input v-model="form.big_model.base_url" placeholder="例如: https://api.siliconflow.cn/v1 (可选)" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="API Key" prop="big_model.api_key">
              <el-input v-model="form.big_model.api_key" type="password" show-password placeholder="sk-... (可选)" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="">
              <el-button 
                type="warning" 
                :loading="testingBig"
                :disabled="!form.big_model.name || !form.big_model.base_url"
                @click="testProviderModel('big')"
              >
                <el-icon><Connection /></el-icon>
                测试大模型
              </el-button>
              <span v-if="testResults.big" :class="testResults.big.status === 'success' ? 'test-success' : 'test-fail'">
                {{ testResults.big.message }}
              </span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">客户端调用说明</el-divider>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <div class="proxy-info">
              <p><strong>第三方客户端（如 ChatBox、NextChat）调用配置：</strong></p>
              <ul>
                <li><strong>API 地址：</strong><code>http://localhost:8080/proxy/v1/</code></li>
                <li><strong>模型名称：</strong>填写上面配置的小模型名称，如 <code>{{ form.small_model?.name || '模型名称' }}</code></li>
                <li><strong>Auth 密钥：</strong>填写上面的 Proxy Key</li>
              </ul>
              <p class="tip">提示：代理会自动将请求转发到对应的 AI 提供商</p>
            </div>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="saveConnection" 
          :loading="saving"
          :disabled="!canSave"
        >
          {{ canSave ? '保存' : '请先测试小模型和大模型' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Plus, Edit, Delete, Connection, Refresh, CopyDocument } from '@element-plus/icons-vue'
import { connectionsApi } from '@/api'

const connections = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const testingSmall = ref(false)
const testingBig = ref(false)

const testResults = reactive({
  small: null,
  big: null
})

const canSave = computed(() => {
  if (isEdit.value) return true
  return testResults.small?.status === 'success'
})

const generateProxyKey = () => {
  form.proxy_key = 'tw-' + Array.from({ length: 24 }, () => 
    '0123456789abcdef'[Math.floor(Math.random() * 16)]
  ).join('')
}

const form = reactive({
  name: '',
  proxy_key: '',
  small_model: {
    name: '',
    base_url: '',
    api_key: ''
  },
  big_model: {
    name: '',
    base_url: '',
    api_key: ''
  }
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  'small_model.name': [{ required: true, message: '请输入小模型名称', trigger: 'blur' }],
  'small_model.base_url': [{ required: true, message: '请输入小模型API地址', trigger: 'blur' }],
  'small_model.api_key': [{ required: true, message: '请输入小模型API Key', trigger: 'blur' }]
}

async function testProviderModel(type) {
  const modelConfig = type === 'small' ? form.small_model : form.big_model
  const loadingRef = type === 'small' ? testingSmall : testingBig
  
  if (!modelConfig.name || !modelConfig.base_url || !modelConfig.api_key) {
    ElMessage.warning('请先填写完整的模型配置')
    return
  }
  
  loadingRef.value = true
  testResults[type] = null
  
  try {
    const baseUrl = modelConfig.base_url.replace(/\/$/, '')
    const testUrl = `${baseUrl}/chat/completions`
    
    const response = await fetch(testUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${modelConfig.api_key}`,
        ...(baseUrl.includes('anthropic') ? {
          'x-api-key': modelConfig.api_key,
          'anthropic-version': '2023-06-01'
        } : {})
      },
      body: JSON.stringify({
        model: modelConfig.name,
        messages: [{ role: 'user', content: 'Hi' }],
        max_tokens: 5,
        temperature: 0.1
      })
    })
    
    if (response.ok) {
      testResults[type] = {
        status: 'success',
        message: '✅ 测试成功'
      }
      ElNotification({
        title: `${type === 'small' ? '小模型' : '大模型'} 测试成功`,
        message: `模型: ${modelConfig.name}`,
        type: 'success',
        duration: 3000
      })
    } else {
      const error = await response.text().catch(() => 'Unknown error')
      testResults[type] = {
        status: 'failed',
        message: `❌ ${response.status}: ${error.substring(0, 100)}`
      }
      ElNotification({
        title: `${type === 'small' ? '小模型' : '大模型'} 测试失败`,
        message: `${response.status}: ${error.substring(0, 200)}`,
        type: 'error',
        duration: 5000
      })
    }
  } catch (error) {
    testResults[type] = {
      status: 'failed',
      message: `❌ ${error.message}`
    }
    ElNotification({
      title: `${type === 'small' ? '小模型' : '大模型'} 测试失败`,
      message: error.message,
      type: 'error',
      duration: 5000
    })
  } finally {
    loadingRef.value = false
  }
}

async function loadConnections() {
  loading.value = true
  try {
    const res = await connectionsApi.list()
    connections.value = Array.isArray(res) ? res : (res.data || [])
  } catch (error) {
    ElMessage.error('加载连接失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  testResults.small = null
  testResults.big = null
  Object.assign(form, {
    name: '',
    proxy_key: generateProxyKey(),
    small_model: { name: '', base_url: '', api_key: '' },
    big_model: { name: '', base_url: '', api_key: '' }
  })
  dialogVisible.value = true
}

function editConnection(row) {
  isEdit.value = true
  editingId.value = row.id
  testResults.small = null
  testResults.big = null
  Object.assign(form, {
    name: row.name,
    proxy_key: row.proxy_key,
    small_model: { ...row.small_model },
    big_model: { ...row.big_model }
  })
  dialogVisible.value = true
}

async function saveConnection() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!isEdit.value && testResults.small?.status !== 'success') {
      ElMessage.warning('请先测试小模型，确保配置正确')
      return
    }

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
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

async function testConnection(row) {
  try {
    const result = await connectionsApi.test(row.id)
    
    const small = result.small_model || {}
    const big = result.big_model || {}
    
    ElNotification({
      title: `测试结果: ${result.connection_name}`,
      message: `
        <div style="line-height: 2;">
          <p><strong>代理地址:</strong> ${result.proxy_url}</p>
          <p><strong>小模型:</strong> ${small.model_name || '-'} - ${small.status === 'success' ? '✅' : '❌'}</p>
          <p style="color: ${small.status === 'success' ? '#67c23a' : '#f56c6c'}; margin-left: 20px;">${small.message || ''}</p>
          <p><strong>大模型:</strong> ${big.model_name || '-'} - ${big.status === 'success' ? '✅' : big.status === 'skipped' ? '⏭️' : '❌'}</p>
          <p style="color: ${big.status === 'success' || big.status === 'skipped' ? '#67c23a' : '#f56c6c'}; margin-left: 20px;">${big.message || ''}</p>
        </div>
      `,
      type: small.status === 'success' && (big.status === 'success' || big.status === 'skipped') ? 'success' : 'warning',
      duration: 10000,
      dangerouslyUseHTMLString: true
    })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || error.message || '连接测试失败')
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

function copyToClipboard(text) {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

async function toggleStatus(row) {
  try {
    if (row.status === 'enabled') {
      await connectionsApi.enable(row.id)
      ElMessage.success('已启用')
    } else {
      await connectionsApi.disable(row.id)
      ElMessage.success('已停用')
    }
    loadConnections()
  } catch (error) {
    ElMessage.error('状态切换失败')
    loadConnections()
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

.proxy-url {
  font-family: monospace;
  font-size: 12px;
  color: #409eff;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  margin-top: 4px;
}

.proxy-info {
  font-size: 13px;
  line-height: 1.8;
  
  ul {
    margin: 10px 0;
    padding-left: 20px;
    
    li {
      margin: 5px 0;
    }
  }
  
  code {
    background: #f5f7fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 12px;
  }
}

:deep(.el-divider__text) {
  font-size: 13px;
  color: #606266;
}

:deep(.el-alert__title) {
  font-size: 13px;
}

.test-success {
  color: #67c23a;
  margin-left: 10px;
  font-size: 13px;
}

.test-fail {
  color: #f56c6c;
  margin-left: 10px;
  font-size: 13px;
}
</style>
