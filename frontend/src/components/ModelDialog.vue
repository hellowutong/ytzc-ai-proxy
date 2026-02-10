<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑模型' : '添加模型'"
    width="700px"
    destroy-on-close
    class="vscode-theme-dialog"
  >
    <el-form :model="form" label-width="140px" class="vscode-form">
      <!-- Basic Info -->
      <el-divider content-position="left" class="vscode-divider">基础信息</el-divider>
      
      <el-form-item label="虚拟模型名称" required>
        <el-input v-model="form.name" placeholder="如: demo1" class="vscode-input" />
        <div v-if="isEdit && form.name !== originalName" class="name-change-warning">
          <el-alert type="warning" :closable="false" show-icon>
            <template #title>
              模型名称将从 "{{ originalName }}" 修改为 "{{ form.name }}"
            </template>
          </el-alert>
        </div>
      </el-form-item>

      <!-- Proxy Key -->
      <el-form-item label="Proxy Key" required>
        <div class="proxy-key-row">
          <el-input
            :model-value="showProxyKey ? form.proxy_key : maskProxyKey(form.proxy_key)"
            placeholder="sk-xxxxxxxxxxxxxxxx"
            readonly
            class="vscode-input proxy-key-input"
          >
            <template #suffix>
              <el-button link @click="toggleProxyKeyVisibility" class="view-btn">
                <el-icon v-if="showProxyKey"><View /></el-icon>
                <el-icon v-else><Hide /></el-icon>
              </el-button>
              <el-button link @click="copyProxyKey" class="copy-btn">
                <el-icon><DocumentCopy /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button type="primary" @click="generateProxyKey" class="generate-btn">
            <el-icon><Key /></el-icon>
            生成
          </el-button>
        </div>
      </el-form-item>

      <el-form-item label="Base URL">
        <el-input v-model="form.base_url" placeholder="https://api.example.com/v1" class="vscode-input" />
      </el-form-item>

      <el-form-item label="启用状态">
        <el-switch v-model="form.use" class="vscode-switch" />
      </el-form-item>

      <el-form-item label="当前模型">
        <div class="model-switch-row">
          <el-radio-group v-model="form.current" class="model-switch-group">
            <el-radio-button label="small">
              <el-icon><Sunny /></el-icon> 小模型
            </el-radio-button>
            <el-radio-button label="big">
              <el-icon><Moon /></el-icon> 大模型
            </el-radio-button>
          </el-radio-group>
          <el-tag :type="form.current === 'small' ? 'success' : 'warning'" class="current-model-tag">
            {{ form.current === 'small' ? form.small.model || '未配置' : form.big.model || '未配置' }}
          </el-tag>
        </div>
      </el-form-item>

      <el-form-item label="强制使用">
        <el-switch v-model="form.force_current" class="vscode-switch" />
      </el-form-item>

      <!-- Small Model -->
      <el-divider content-position="left" class="vscode-divider">小模型配置</el-divider>
      
      <el-form-item label="模型名称">
        <el-input v-model="form.small.model" placeholder="如: deepseek-ai/DeepSeek-R1" class="vscode-input" />
      </el-form-item>
      
      <el-form-item label="API Key">
        <el-input v-model="form.small.api_key" type="password" placeholder="sk-xxx" class="vscode-input" />
      </el-form-item>
      
      <el-form-item label="Base URL">
        <el-input v-model="form.small.base_url" placeholder="https://api.xxx.com/v1" class="vscode-input" />
      </el-form-item>
      
      <el-form-item>
        <el-button @click="testConnection('small')" :loading="testing.small" class="vscode-button">
          <el-icon><Connection /></el-icon>
          测试连接
        </el-button>
        <span v-if="testResults.small" :class="['test-result', testResults.small.status]">
          {{ testResults.small.message }}
        </span>
      </el-form-item>

      <!-- Big Model -->
      <el-divider content-position="left" class="vscode-divider">大模型配置</el-divider>
      
      <el-form-item label="模型名称">
        <el-input v-model="form.big.model" placeholder="如: Qwen/Qwen2.5-72B-Instruct" class="vscode-input" />
      </el-form-item>
      
      <el-form-item label="API Key">
        <el-input v-model="form.big.api_key" type="password" placeholder="sk-xxx" class="vscode-input" />
      </el-form-item>
      
      <el-form-item label="Base URL">
        <el-input v-model="form.big.base_url" placeholder="https://api.xxx.com/v1" class="vscode-input" />
      </el-form-item>
      
      <el-form-item>
        <el-button @click="testConnection('big')" :loading="testing.big" class="vscode-button">
          <el-icon><Connection /></el-icon>
          测试连接
        </el-button>
        <span v-if="testResults.big" :class="['test-result', testResults.big.status]">
          {{ testResults.big.message }}
        </span>
      </el-form-item>

      <!-- Knowledge -->
      <el-divider content-position="left" class="vscode-divider">知识库配置</el-divider>

      <el-form-item label="启用知识库">
        <el-switch v-model="form.knowledge.enabled" class="vscode-switch" />
      </el-form-item>

      <el-form-item label="共享知识库">
        <el-switch v-model="form.knowledge.shared" class="vscode-switch" />
      </el-form-item>

      <!-- 知识库 Skill 选择 -->
      <el-form-item label="系统默认Skill">
        <el-radio-group v-model="form.knowledge.system_default_skill" class="vscode-radio-group" :loading="loadingVersions.knowledge_system">
          <el-radio-button label="">不使用</el-radio-button>
          <el-radio-button 
            v-for="version in knowledgeSystemVersions" 
            :key="version" 
            :label="version"
          >
            系统默认 {{ version }}
          </el-radio-button>
          <el-empty v-if="knowledgeSystemVersions.length === 0 && !loadingVersions.knowledge_system" description="暂无可用版本" :image-size="60" />
        </el-radio-group>
      </el-form-item>

      <el-form-item label="自定义Skill">
        <div class="skill-toggle-row">
          <el-switch v-model="form.knowledge.use_custom" class="vscode-switch" />
          <span class="skill-toggle-label">启用自定义Skill</span>
        </div>
      </el-form-item>

      <el-form-item v-if="form.knowledge.use_custom" label="自定义Skill版本">
        <el-radio-group v-model="form.knowledge.custom_skill" class="vscode-radio-group" :loading="loadingVersions.knowledge_custom">
          <el-radio-button label="">不使用</el-radio-button>
          <el-radio-button 
            v-for="version in knowledgeCustomVersions" 
            :key="version" 
            :label="version"
          >
            {{ version }}
          </el-radio-button>
          <el-empty v-if="knowledgeCustomVersions.length === 0 && !loadingVersions.knowledge_custom" description="暂无可用版本" :image-size="60" />
        </el-radio-group>
      </el-form-item>

      <!-- Web Search -->
      <el-divider content-position="left" class="vscode-divider">联网搜索配置</el-divider>

      <el-form-item label="启用联网搜索">
        <el-switch v-model="form.web_search.enabled" class="vscode-switch" />
      </el-form-item>

      <!-- 联网搜索 Skill 选择 -->
      <el-form-item label="系统默认Skill">
        <el-radio-group v-model="form.web_search.system_default_skill" class="vscode-radio-group" :loading="loadingVersions.websearch_system">
          <el-radio-button label="">不使用</el-radio-button>
          <el-radio-button 
            v-for="version in webSearchSystemVersions" 
            :key="version" 
            :label="version"
          >
            系统默认 {{ version }}
          </el-radio-button>
          <el-empty v-if="webSearchSystemVersions.length === 0 && !loadingVersions.websearch_system" description="暂无可用版本" :image-size="60" />
        </el-radio-group>
      </el-form-item>

      <el-form-item label="自定义Skill">
        <div class="skill-toggle-row">
          <el-switch v-model="form.web_search.use_custom" class="vscode-switch" />
          <span class="skill-toggle-label">启用自定义Skill</span>
        </div>
      </el-form-item>

      <el-form-item v-if="form.web_search.use_custom" label="自定义Skill版本">
        <el-radio-group v-model="form.web_search.custom_skill" class="vscode-radio-group" :loading="loadingVersions.websearch_custom">
          <el-radio-button label="">不使用</el-radio-button>
          <el-radio-button 
            v-for="version in webSearchCustomVersions" 
            :key="version" 
            :label="version"
          >
            {{ version }}
          </el-radio-button>
          <el-empty v-if="webSearchCustomVersions.length === 0 && !loadingVersions.websearch_custom" description="暂无可用版本" :image-size="60" />
        </el-radio-group>
      </el-form-item>

      <el-form-item label="搜索目标">
        <el-checkbox-group v-model="form.web_search.targets" class="vscode-checkbox-group">
          <el-checkbox label="searxng">SearXNG</el-checkbox>
          <el-checkbox label="librex">LibreX</el-checkbox>
          <el-checkbox label="4get">4get</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false" class="vscode-button">取消</el-button>
        <el-button @click="testAllConnections" class="vscode-button">测试所有连接</el-button>
        <el-button type="primary" @click="handleSubmit" class="vscode-button-primary">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElEmpty } from 'element-plus'
import { DocumentCopy, Key, Connection, View, Hide, Sunny, Moon } from '@element-plus/icons-vue'
import type { VirtualModel } from '@/types'

const props = defineProps<{
  modelValue: boolean
  model: VirtualModel | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', value: Partial<VirtualModel>, originalName?: string): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.model)

// 保存原始模型名称，用于检测名称变更
const originalName = ref('')

const defaultForm = {
  name: '',
  proxy_key: '',
  base_url: '',
  current: 'small' as 'small' | 'big',
  force_current: false,
  use: true,
  small: {
    model: '',
    api_key: '',
    base_url: ''
  },
  big: {
    model: '',
    api_key: '',
    base_url: ''
  },
  knowledge: {
    enabled: true,
    shared: false,
    system_default_skill: null as string | null,
    custom_skill: null as string | null,
    use_system_default: true,
    use_custom: false
  },
  web_search: {
    enabled: false,
    system_default_skill: null as string | null,
    custom_skill: null as string | null,
    use_system_default: true,
    use_custom: false,
    targets: ['searxng']
  }
}

const form = ref({ ...defaultForm })

// 测试状态
const testing = ref({
  small: false,
  big: false
})

// 测试结果
const testResults = ref<{
  small?: { status: 'success' | 'error'; message: string } | null
  big?: { status: 'success' | 'error'; message: string } | null
}>({})

// Proxy Key 显示控制
const showProxyKey = ref(false)

// Skill版本列表
const knowledgeSystemVersions = ref<string[]>([])
const knowledgeCustomVersions = ref<string[]>([])
const webSearchSystemVersions = ref<string[]>([])
const webSearchCustomVersions = ref<string[]>([])

// 加载状态
const loadingVersions = ref({
  knowledge_system: false,
  knowledge_custom: false,
  websearch_system: false,
  websearch_custom: false
})

// 获取Skill版本列表
const fetchSkillVersions = async (category: string, isCustom: boolean = false) => {
  const skillType = isCustom ? 'custom' : 'system'
  const loadingKey = isCustom ? 
    (category === 'knowledge' ? 'knowledge_custom' : 'websearch_custom') : 
    (category === 'knowledge' ? 'knowledge_system' : 'websearch_system')

  loadingVersions.value[loadingKey] = true
  try {
    const response = await fetch(`/admin/ai/v1/skills/versions?category=${category}&skill_type=${skillType}`)
    const data = await response.json()
    if (data.code === 200 && data.data) {
      const versions = data.data.versions || []
      if (category === 'knowledge') {
        if (isCustom) {
          knowledgeCustomVersions.value = versions
        } else {
          knowledgeSystemVersions.value = versions
        }
      } else if (category === 'web_search') {
        if (isCustom) {
          webSearchCustomVersions.value = versions
        } else {
          webSearchSystemVersions.value = versions
        }
      }
    }
  } catch (error) {
    console.error(`获取${category} ${isCustom ? '自定义' : '系统'}Skill版本失败:`, error)
  } finally {
    loadingVersions.value[loadingKey] = false
  }
}

// 加载所有Skill版本
const loadAllSkillVersions = async () => {
  // 知识库系统Skill
  await fetchSkillVersions('knowledge', false)
  // 知识库自定义Skill
  await fetchSkillVersions('knowledge', true)
  // 联网搜索系统Skill
  await fetchSkillVersions('web_search', false)
  // 联网搜索自定义Skill
  await fetchSkillVersions('web_search', true)
}

// 脱敏 Proxy Key
const maskProxyKey = (key: string): string => {
  if (!key || key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

// 切换 Proxy Key 显示/隐藏
const toggleProxyKeyVisibility = () => {
  showProxyKey.value = !showProxyKey.value
}

// 生成随机Proxy Key
function generateRandomKey(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = 'sk-'
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

watch(() => props.model, async (newModel) => {
  if (newModel) {
    form.value = {
      ...defaultForm,
      ...JSON.parse(JSON.stringify(newModel))
    }
    // 保存原始名称
    originalName.value = newModel.name || ''
    // 如果没有proxy_key，生成一个
    if (!form.value.proxy_key) {
      form.value.proxy_key = generateRandomKey()
    }
  } else {
    form.value = { 
      ...defaultForm,
      proxy_key: generateRandomKey()
    }
    originalName.value = ''
  }
  // 加载Skill版本列表
  await loadAllSkillVersions()
}, { immediate: true })

// 生成Proxy Key
const generateProxyKey = () => {
  form.value.proxy_key = generateRandomKey()
  ElMessage.success('Proxy Key 已生成')
}

// 复制Proxy Key
const copyProxyKey = () => {
  if (!form.value.proxy_key) {
    ElMessage.warning('Proxy Key 为空')
    return
  }
  navigator.clipboard.writeText(form.value.proxy_key)
    .then(() => ElMessage.success('Proxy Key 已复制'))
    .catch(() => ElMessage.error('复制失败'))
}

// 测试连接
const testConnection = async (type: 'small' | 'big') => {
  const config = form.value[type]
  if (!config.model || !config.api_key || !config.base_url) {
    ElMessage.warning('请填写完整的模型配置信息')
    return
  }

  testing.value[type] = true
  testResults.value[type] = null
  
  try {
    // 真实的API测试
    const response = await fetch(`${config.base_url}/models`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${config.api_key}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      // 检查模型是否在列表中
      const models = data.data || []
      const hasModel = models.some((m: any) => m.id === config.model || m.model === config.model)
      
      if (hasModel) {
        testResults.value[type] = {
          status: 'success',
          message: `连接成功，模型可用`
        }
        ElMessage.success(`${type === 'small' ? '小' : '大'}模型连接成功`)
      } else {
        testResults.value[type] = {
          status: 'success',
          message: `连接成功，但模型不在列表中`
        }
        ElMessage.warning(`${type === 'small' ? '小' : '大'}模型连接成功，但找不到指定模型`)
      }
    } else {
      const errorData = await response.json().catch(() => ({}))
      testResults.value[type] = {
        status: 'error',
        message: `连接失败: ${errorData.error?.message || response.statusText}`
      }
      ElMessage.error(`${type === 'small' ? '小' : '大'}模型连接失败: ${errorData.error?.message || response.statusText}`)
    }
  } catch (error: any) {
    testResults.value[type] = {
      status: 'error',
      message: `连接错误: ${error.message}`
    }
    ElMessage.error(`${type === 'small' ? '小' : '大'}模型连接错误: ${error.message}`)
  } finally {
    testing.value[type] = false
  }
}

const testAllConnections = async () => {
  await testConnection('small')
  await testConnection('big')
}

const handleSubmit = () => {
  if (!form.value.name) {
    ElMessage.warning('请输入虚拟模型名称')
    return
  }
  if (!form.value.proxy_key) {
    ElMessage.warning('请生成Proxy Key')
    return
  }
  // 编辑模式下传递原始名称，用于后端识别是哪个模型
  if (isEdit.value && originalName.value) {
    emit('submit', { ...form.value }, originalName.value)
  } else {
    emit('submit', { ...form.value })
  }
}
</script>

<style scoped>
/* GitHub 主题配色 - 与左侧菜单栏一致 */
.vscode-theme-dialog :deep(.el-dialog) {
  background: #252526;
  border: 1px solid #3C3C3C;
}

.vscode-theme-dialog :deep(.el-dialog__header) {
  background: #1E1E1E;
  border-bottom: 1px solid #3C3C3C;
  margin-right: 0;
  padding: 15px 20px;
}

.vscode-theme-dialog :deep(.el-dialog__title) {
  color: #c9d1d9;
  font-size: 16px;
  font-weight: 600;
}

.vscode-theme-dialog :deep(.el-dialog__body) {
  background: #252526;
  color: #c9d1d9;
  max-height: 60vh;
  overflow-y: auto;
}

.vscode-theme-dialog :deep(.el-dialog__footer) {
  background: #1E1E1E;
  border-top: 1px solid #3C3C3C;
}

/* 表单项标签 */
.vscode-form :deep(.el-form-item__label) {
  color: #858585;
}

/* 输入框 - 白色背景 */
.vscode-input :deep(.el-input__wrapper) {
  background: #ffffff;
  box-shadow: 0 0 0 1px #d1d5da inset;
}

.vscode-input :deep(.el-input__inner) {
  background: transparent;
  color: #24292e;
}

.vscode-input :deep(.el-input__inner::placeholder) {
  color: #6e7781;
}

/* Proxy Key 行 */
.proxy-key-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.proxy-key-input {
  flex: 1;
}

.copy-btn {
  color: #858585;
}

.copy-btn:hover,
.view-btn:hover {
  color: #007acc;
}

.generate-btn {
  background: #007acc;
  border-color: #007acc;
}

.generate-btn:hover {
  background: #1177bb;
  border-color: #1177bb;
}

/* 分隔线 */
.vscode-divider :deep(.el-divider__text) {
  background: #252526;
  color: #858585;
}

/* 按钮 */
.vscode-button {
  background: #2D2D30;
  border-color: #3C3C3C;
  color: #c9d1d9;
}

.vscode-button:hover {
  background: #3C3C3C;
  border-color: #858585;
  color: #ffffff;
}

.vscode-button-primary {
  background: #238636;
  border-color: #238636;
  color: #ffffff;
}

.vscode-button-primary:hover {
  background: #2ea043;
  border-color: #2ea043;
}

/* 单选按钮组 */
.vscode-radio-group :deep(.el-radio-button__inner) {
  background: #2D2D30;
  border-color: #3C3C3C;
  color: #858585;
}

.vscode-radio-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #007ACC;
  border-color: #007ACC;
  color: #ffffff;
}

/* 开关 */
.vscode-switch :deep(.el-switch__core) {
  background: #3C3C3C;
  border-color: #3C3C3C;
}

.vscode-switch.is-checked :deep(.el-switch__core) {
  background: #007ACC;
  border-color: #007ACC;
}

/* 复选框 */
.vscode-checkbox-group :deep(.el-checkbox__input) .el-checkbox__inner {
  background: #2D2D30;
  border-color: #3C3C3C;
}

.vscode-checkbox-group :deep(.el-checkbox__input.is-checked) .el-checkbox__inner {
  background: #007ACC;
  border-color: #007ACC;
}

.vscode-checkbox-group :deep(.el-checkbox__label) {
  color: #858585;
}

/* Skill 切换行 */
.skill-toggle-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skill-toggle-label {
  color: #858585;
  font-size: 14px;
}

/* 测试结果 */
.test-result {
  margin-left: 10px;
  font-size: 13px;
}

.test-result.success {
  color: #3fb950;
}

.test-result.error {
  color: #f85149;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 名称变更警告 */
.name-change-warning {
  margin-top: 8px;
}

.name-change-warning :deep(.el-alert) {
  padding: 8px 12px;
}

.name-change-warning :deep(.el-alert__title) {
  font-size: 12px;
  line-height: 1.4;
}

/* 模型切换行 */
.model-switch-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-switch-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
}

.model-switch-group :deep(.el-icon) {
  font-size: 14px;
}
</style>
