<template>
  <div class="virtual-models-container">
    <!-- Page Header -->
    <div class="page-header">
      <h2>虚拟模型管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建虚拟模型
      </el-button>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-value">{{ stats.total }}</div>
          <div class="stats-label">总模型数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-value success">{{ stats.enabled }}</div>
          <div class="stats-label">已启用</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-value warning">{{ stats.total - stats.enabled }}</div>
          <div class="stats-label">已禁用</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-value info">{{ modelsUsingBigModel }}</div>
          <div class="stats-label">使用大模型</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Models Table -->
    <el-card class="models-table-card">
      <el-table
        :data="models"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="name" label="模型名称" min-width="120" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="viewModelDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="enabled" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="current" label="当前模型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.current === 'big' ? 'warning' : 'info'">
              {{ row.current === 'big' ? '大模型' : '小模型' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="small_model" label="小模型" min-width="180" show-overflow-tooltip />
        <el-table-column prop="big_model" label="大模型" min-width="180" show-overflow-tooltip />

        <el-table-column label="功能" width="150" align="center">
          <template #default="{ row }">
            <div class="feature-tags">
              <el-tag v-if="row.knowledge_enabled" size="small" type="success" effect="plain">知识库</el-tag>
              <el-tag v-if="row.web_search_enabled" size="small" type="primary" effect="plain">搜索</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                size="small" 
                :type="row.enabled ? 'danger' : 'success'"
                @click="toggleModel(row)"
              >
                {{ row.enabled ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" @click="editModel(row)">
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="warning" 
                @click="switchModel(row)"
              >
                切换
              </el-button>
              <el-button size="small" type="danger" @click="confirmDelete(row)">
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑虚拟模型' : '新建虚拟模型'"
      width="950px"
      top="20px"
      destroy-on-close
      class="virtual-model-dialog"
    >
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        label-position="right"
        class="dialog-form"
      >
        <!-- Basic Info -->
        <el-divider>基本信息</el-divider>
        
        <el-form-item label="模型名称" prop="name" v-if="!isEditing">
          <el-input v-model="form.name" placeholder="请输入模型名称（英文，仅字母、数字、下划线、横线）" />
        </el-form-item>

        <el-form-item label="代理Key" prop="proxy_key">
          <el-input
            v-model="form.proxy_key"
            placeholder="客户端调用时使用的API Key"
            :type="showProxyKey ? 'text' : 'password'"
            class="proxy-key-input"
          >
            <template #append>
              <el-button-group>
                <el-button @click="generateProxyKey" title="生成随机Key">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button @click="copyProxyKey" title="复制到剪贴板">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button @click="showProxyKey = !showProxyKey" :title="showProxyKey ? '隐藏' : '显示'">
                  <el-icon v-if="showProxyKey"><View /></el-icon>
                  <el-icon v-else><Hide /></el-icon>
                </el-button>
              </el-button-group>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="基础URL" prop="base_url">
          <el-input 
            v-model="form.base_url" 
            placeholder="例如: http://localhost:8000/proxy/v1"
            @focus="clearBaseUrl('base_url')"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="当前模型" prop="current">
              <el-radio-group v-model="form.current">
                <el-radio label="small">小模型</el-radio>
                <el-radio label="big">大模型</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用模型" prop="use">
              <el-switch v-model="form.use" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- Small Model Config -->
        <el-divider>小模型配置 <el-tag size="small" type="info">主要用于日常 dialog</el-tag></el-divider>
        
        <el-form-item label="模型名称" prop="small.model">
          <el-input v-model="form.small.model" placeholder="例如: deepseek-ai/DeepSeek-R1" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="Base URL">
              <el-input 
                v-model="form.small.base_url" 
                placeholder="例如: https://api.siliconflow.cn/v1"
                @focus="clearBaseUrl('small.base_url')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-button type="primary" plain size="small" @click="testModel('small')" :loading="testing.small">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
          </el-col>
        </el-row>

        <el-form-item label="API Key">
          <el-input v-model="form.small.api_key" placeholder="可选" show-password />
        </el-form-item>

        <el-form-item label="Embedding模型">
          <el-input v-model="form.small.embedding_model" placeholder="可选，用于知识库向量化" />
        </el-form-item>

        <!-- Big Model Config -->
        <el-divider>大模型配置 <el-tag size="small" type="warning">用于复杂推理和代码生成</el-tag></el-divider>
        
        <el-form-item label="模型名称" prop="big.model">
          <el-input v-model="form.big.model" placeholder="例如: Pro/deepseek-ai/DeepSeek-V3" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="Base URL">
              <el-input 
                v-model="form.big.base_url" 
                placeholder="例如: https://api.siliconflow.cn/v1"
                @focus="clearBaseUrl('big.base_url')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-button type="warning" plain size="small" @click="testModel('big')" :loading="testing.big">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
          </el-col>
        </el-row>

        <el-form-item label="API Key">
          <el-input v-model="form.big.api_key" placeholder="可选" show-password />
        </el-form-item>

        <!-- Knowledge Base Config -->
        <el-divider>知识库配置</el-divider>
        
        <el-form-item label="启用知识库">
          <el-switch v-model="form.knowledge.enabled" />
        </el-form-item>

        <template v-if="form.knowledge.enabled">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="共享知识库">
                <el-switch v-model="form.knowledge.shared" />
                <span class="form-tip">启用后所有用户共享知识库</span>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- Knowledge Skill Selection -->
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="系统Skill">
                <el-select v-model="form.knowledge.system_skill" placeholder="选择系统Skill" clearable style="width: 100%">
                  <el-option
                    v-for="skill in knowledgeSystemSkills"
                    :key="skill.id"
                    :label="skill.name"
                    :value="skill.id"
                  >
                    <span>{{ skill.name }}</span>
                    <el-tag size="small" type="info" style="margin-left: 8px;">{{ skill.version }}</el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="自定义Skill">
                <el-select v-model="form.knowledge.custom_skill" placeholder="选择自定义Skill" clearable style="width: 100%">
                  <el-option
                    v-for="skill in knowledgeCustomSkills"
                    :key="skill.id"
                    :label="skill.name"
                    :value="skill.id"
                  >
                    <span>{{ skill.name }}</span>
                    <el-tag size="small" type="warning" style="margin-left: 8px;">{{ skill.custom_version || skill.version }}</el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

            <!-- Knowledge Skill列表 -->
            <el-table
              :data="knowledgeSkills"
              v-if="knowledgeSkills.length > 0"
              size="small"
              border
              style="width: 100%"
            >
              <el-table-column prop="name" label="Skill名称" width="120" />
              <el-table-column prop="version" label="版本" width="80" align="center">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.version }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="enabled" label="启用" width="80" align="center">
                <template #default="{ row }">
                  <el-switch v-model="row.enabled" size="small" @change="updateKnowledgeSkill(row)" />
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-else description="暂无配置的知识库Skill" :image-size="60" style="margin: 10px 0; padding: 10px 0;" />
        </template>

        <!-- Web Search Config -->
        <el-divider style="margin-top: 10px;">联网搜索配置</el-divider>
        
        <el-form-item label="启用搜索">
          <el-switch v-model="form.web_search.enabled" />
        </el-form-item>

        <template v-if="form.web_search.enabled">
            <!-- Web Search Skill Selection -->
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="系统Skill">
                  <el-select v-model="form.web_search.system_skill" placeholder="选择系统Skill" clearable style="width: 100%">
                    <el-option
                      v-for="skill in webSearchSystemSkills"
                      :key="skill.id"
                      :label="skill.name"
                      :value="skill.id"
                    >
                      <span>{{ skill.name }}</span>
                      <el-tag size="small" type="info" style="margin-left: 8px;">{{ skill.version }}</el-tag>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自定义Skill">
                  <el-select v-model="form.web_search.custom_skill" placeholder="选择自定义Skill" clearable style="width: 100%">
                    <el-option
                      v-for="skill in webSearchCustomSkills"
                      :key="skill.id"
                      :label="skill.name"
                      :value="skill.id"
                    >
                      <span>{{ skill.name }}</span>
                      <el-tag size="small" type="warning" style="margin-left: 8px;">{{ skill.custom_version || skill.version }}</el-tag>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <!-- Web Search Skill列表 -->
            <el-table
              :data="webSearchSkills"
              v-if="webSearchSkills.length > 0"
              size="small"
              border
              style="width: 100%"
            >
              <el-table-column prop="name" label="Skill名称" width="120" />
              <el-table-column prop="version" label="版本" width="80" align="center">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.version }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="enabled" label="启用" width="80" align="center">
                <template #default="{ row }">
                  <el-switch v-model="row.enabled" size="small" @change="updateWebSearchSkill(row)" />
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-else description="暂无配置的联网搜索Skill" :image-size="60" style="margin: 10px 0; padding: 10px 0;" />

            <!-- Search Targets -->
            <el-divider style="margin-top: 10px;" />
            <el-form-item label="搜索目标">
              <el-checkbox-group v-model="form.web_search.target">
                <el-checkbox
                  v-for="target in availableSearchTargets"
                  :key="target.id"
                  :label="target.id"
                >
                  {{ target.name }}
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>
        </template>
      </el-form>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      title="模型详情"
      width="700px"
    >
      <el-descriptions v-if="currentModel" :column="2" border>
        <el-descriptions-item label="模型名称">{{ currentModel.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentModel.enabled ? 'success' : 'danger'">
            {{ currentModel.enabled ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前模型">
          <el-tag :type="currentModel.current === 'big' ? 'warning' : 'info'">
            {{ currentModel.current === 'big' ? '大模型' : '小模型' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="基础URL">{{ currentModel.base_url }}</el-descriptions-item>
        <el-descriptions-item label="小模型">{{ currentModel.small_model }}</el-descriptions-item>
        <el-descriptions-item label="大模型">{{ currentModel.big_model }}</el-descriptions-item>
        <el-descriptions-item label="知识库">
          <el-tag :type="currentModel.knowledge_enabled ? 'success' : 'info'">
            {{ currentModel.knowledge_enabled ? '已启用' : '未启用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="联网搜索">
          <el-tag :type="currentModel.web_search_enabled ? 'success' : 'info'">
            {{ currentModel.web_search_enabled ? '已启用' : '未启用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, CopyDocument, View, Hide, Connection } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  listVirtualModels,
  getVirtualModel,
  createVirtualModel,
  updateVirtualModel,
  deleteVirtualModel,
  toggleVirtualModel,
  switchCurrentModel,
  getSkills,
  getSearchTargets,
  getProxyUrl,
  testConnection,
  type VirtualModelSummary,
  type VirtualModel,
  type SkillInfo,
  type SearchTargetInfo
} from '@/api/virtualModels'

// State
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEditing = ref(false)
const models = ref<VirtualModelSummary[]>([])
const currentModel = ref<VirtualModelSummary | null>(null)
const formRef = ref<FormInstance>()
const showProxyKey = ref(false)

const testing = reactive({
  small: false,
  big: false
})

const stats = reactive({
  total: 0,
  enabled: 0
})

// Skills and search targets loaded from backend
const availableSkills = ref<SkillInfo[]>([])
const availableSearchTargets = ref<SearchTargetInfo[]>([])

const modelsUsingBigModel = computed(() => {
  return models.value.filter(m => m.current === 'big').length
})

// Form
const form = reactive({
  name: '',
  proxy_key: '',
  base_url: '',
  current: 'small' as 'small' | 'big',
  use: true,
  small: {
    model: '',
    api_key: '',
    base_url: '',
    embedding_model: ''
  },
  big: {
    model: '',
    api_key: '',
    base_url: '',
    embedding_model: ''
  },
  knowledge: {
    enabled: true,
    shared: true,
    system_skill: '',
    custom_skill: '',
    skills: [] as Array<{name: string, version: string, enabled: boolean}>
  },
  web_search: {
    enabled: true,
    system_skill: '',
    custom_skill: '',
    skills: [] as Array<{name: string, version: string, enabled: boolean}>,
    target: [] as string[]
  }
})

// Knowledge skills computed property
const knowledgeSkills = computed({
  get: () => form.knowledge.skills,
  set: (val) => { form.knowledge.skills = val }
})

// Knowledge system skills (skills that have system version)
const knowledgeSystemSkills = computed(() => {
  return availableSkills.value.filter(s => 
    s.category === 'knowledge' && s.enabled
  )
})

// Knowledge custom skills (skills that have custom version)
const knowledgeCustomSkills = computed(() => {
  return availableSkills.value.filter(s => 
    s.category === 'knowledge' && s.has_custom
  )
})

// Web search skills computed property
const webSearchSkills = computed({
  get: () => form.web_search.skills,
  set: (val) => { form.web_search.skills = val }
})

// Web search system skills
const webSearchSystemSkills = computed(() => {
  return availableSkills.value.filter(s => 
    (s.category === 'router' || !s.category) && s.enabled
  )
})

// Web search custom skills
const webSearchCustomSkills = computed(() => {
  return availableSkills.value.filter(s => 
    (s.category === 'router' || !s.category) && s.has_custom
  )
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  proxy_key: [
    { required: true, message: '请输入代理Key', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  'small.model': [
    { required: true, message: '请输入小模型名称', trigger: 'blur' }
  ],
  'small.base_url': [
    { required: true, message: '请输入小模型Base URL', trigger: 'blur' }
  ],
  'big.model': [
    { required: true, message: '请输入大模型名称', trigger: 'blur' }
  ],
  'big.base_url': [
    { required: true, message: '请输入大模型Base URL', trigger: 'blur' }
  ]
}

// Methods
const loadModels = async () => {
  loading.value = true
  try {
    const res = await listVirtualModels()
    console.log('API Response:', JSON.stringify(res))
    if (res && res.success) {
      models.value = res.data.models
      stats.total = res.data.total
      stats.enabled = res.data.enabled
    }
  } catch (error: any) {
    console.error('Load models error:', error)
    ElMessage.error(error.response?.data?.message || '加载模型列表失败')
  } finally {
    loading.value = false
  }
}

// Load skills and search targets from backend
const loadSkillsAndTargets = async () => {
  try {
    const [skillsRes, targetsRes] = await Promise.all([
      getSkills(),
      getSearchTargets()
    ])
    if (skillsRes.success) {
      availableSkills.value = skillsRes.data || []
    }
    if (targetsRes.success) {
      availableSearchTargets.value = targetsRes.data || []
    }
  } catch (error: any) {
    console.error('Load skills/targets error:', error)
    // Use fallback data on error
    availableSearchTargets.value = [
      { id: 'searxng', name: 'SearXNG', enabled: true, description: 'Privacy-respecting metasearch engine' },
      { id: 'LibreX', name: 'LibreX', enabled: true, description: 'Privacy-preserving search engine' },
      { id: '4get', name: '4get', enabled: true, description: 'Minimalist search engine' },
      { id: 'brave', name: 'Brave Search', enabled: false, description: 'Privacy-focused search' },
      { id: 'duckduckgo', name: 'DuckDuckGo', enabled: false, description: 'Privacy-respecting search' },
      { id: 'google', name: 'Google', enabled: false, description: 'Google web search' }
    ]
  }
}

// Auto-fill base_url with backend URL from config
const autoFillBaseUrl = async () => {
  if (!form.base_url) {
    try {
      const res = await getProxyUrl()
      if (res.success && res.data) {
        form.base_url = res.data.proxy_url
      } else {
        // Fallback to frontend origin
        form.base_url = window.location.origin + '/proxy/v1'
      }
    } catch (error) {
      // Fallback to frontend origin
      form.base_url = window.location.origin + '/proxy/v1'
    }
  }
}

// Generate random proxy key
const generateProxyKey = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const prefix = 'sk_'
  const length = 32
  let result = prefix
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  form.proxy_key = result
  ElMessage.success('已生成新的代理Key')
}

// Copy proxy key to clipboard
const copyProxyKey = async () => {
  if (!form.proxy_key) {
    ElMessage.warning('请先生成或输入代理Key')
    return
  }
  try {
    await navigator.clipboard.writeText(form.proxy_key)
    ElMessage.success('已复制到剪贴板')
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = form.proxy_key
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    ElMessage.success('已复制到剪贴板')
  }
}

// Clear base_url on focus
const clearBaseUrl = (field: string) => {
  const fields = field.split('.')
  let obj: any = form
  for (let i = 0; i < fields.length - 1; i++) {
    obj = obj[fields[i]]
  }
  const lastField = fields[fields.length - 1]
  if (obj[lastField] === '' || obj[lastField].startsWith('例如:')) {
    obj[lastField] = ''
  }
}

// Test model connection
const testModel = async (type: 'small' | 'big') => {
  testing[type] = true
  try {
    const modelConfig = form[type]
    if (!modelConfig.model) {
      ElMessage.warning(`请先输入${type === 'small' ? '小' : '大'}模型名称`)
      return
    }
    if (!modelConfig.base_url) {
      ElMessage.warning(`请先输入${type === 'small' ? '小' : '大'}模型Base URL`)
      return
    }

    const result = await testConnection({
      model: modelConfig.model,
      base_url: modelConfig.base_url,
      api_key: modelConfig.api_key || undefined
    })

    if (result.connected) {
      ElMessage.success(`${type === 'small' ? '小' : '大'}模型连接测试成功`)
    } else {
      ElMessage.warning(`${type === 'small' ? '小' : '大'}模型连接失败: ${result.message}`)
    }
  } catch (error: any) {
    console.error('Test connection error:', error)
    ElMessage.error(error.response?.data?.message || '连接测试失败')
  } finally {
    testing[type] = false
  }
}

const updateKnowledgeSkill = (skill: {name: string, version: string, enabled: boolean}) => {
  ElMessage.success(`已${skill.enabled ? '启用' : '禁用'} Skill: ${skill.name}`)
}

const showCreateDialog = () => {
  isEditing.value = false
  resetForm()
  autoFillBaseUrl()
  dialogVisible.value = true
}

const resetForm = () => {
  form.name = ''
  form.proxy_key = ''
  form.base_url = ''
  form.current = 'small'
  form.use = true
  form.small = {
    model: '',
    api_key: '',
    base_url: '',
    embedding_model: ''
  }
  form.big = {
    model: '',
    api_key: '',
    base_url: '',
    embedding_model: ''
  }
  form.knowledge = {
    enabled: true,
    shared: true,
    skills: [] as Array<{name: string, version: string, enabled: boolean}>
  }
  form.web_search = {
    enabled: true,
    skills: [] as Array<{name: string, version: string, enabled: boolean}>,
    target: [] as string[]
  }
}

const viewModelDetail = (row: VirtualModelSummary) => {
  currentModel.value = row
  detailVisible.value = true
}

const editModel = async (row: VirtualModelSummary) => {
  isEditing.value = true
  try {
    const res = await getVirtualModel(row.name)
    if (res.success) {
      const config = res.config
      Object.assign(form, {
        name: row.name,
        ...config
      })
      dialogVisible.value = true
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '获取模型详情失败')
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const { name, ...config } = form
      
      if (isEditing.value) {
        await updateVirtualModel(name, config)
        ElMessage.success('更新成功')
      } else {
        await createVirtualModel(name, config as VirtualModel)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      loadModels()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const confirmDelete = (row: VirtualModelSummary) => {
  ElMessageBox.confirm(
    `确定要删除虚拟模型 "${row.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'danger'
    }
  ).then(async () => {
    try {
      await deleteVirtualModel(row.name)
      ElMessage.success('删除成功')
      loadModels()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }).catch(() => {})
}

const toggleModel = async (row: VirtualModelSummary) => {
  try {
    await toggleVirtualModel(row.name, !row.enabled)
    ElMessage.success(row.enabled ? '已禁用' : '已启用')
    loadModels()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

const switchModel = async (row: VirtualModelSummary) => {
  const target = row.current === 'small' ? 'big' : 'small'
  try {
    await switchCurrentModel(row.name, target)
    ElMessage.success(`已切换至${target === 'big' ? '大模型' : '小模型'}`)
    loadModels()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '切换失败')
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadModels(),
    loadSkillsAndTargets()
  ])
})
</script>

<style scoped lang="scss">
.virtual-models-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 24px;
    color: #303133;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;

  .stats-value {
    font-size: 32px;
    font-weight: bold;
    color: #409eff;
    margin-bottom: 8px;

    &.success { color: #67c23a; }
    &.warning { color: #e6a23c; }
    &.info { color: #909399; }
  }

  .stats-label {
    font-size: 14px;
    color: #606266;
  }
}

.models-table-card {
  margin-top: 20px;
}

.feature-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.skill-card {
  margin: 10px 0;
  background-color: #fafafa;

  :deep(.el-card__header) {
    padding: 10px 15px;
    background-color: #f0f0f0;
    font-weight: bold;
  }
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-divider__text) {
  font-size: 14px;
  font-weight: bold;
  color: #606266;
}

// Dialog scroll styles
.virtual-model-dialog {
  :deep(.el-dialog) {
    margin-bottom: 2vh;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-dialog__header) {
    flex-shrink: 0;
    padding: 15px 20px;
    border-bottom: 1px solid #ebeef5;
    margin-right: 0;
  }

  :deep(.el-dialog__body) {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    max-height: calc(90vh - 120px);
  }

  :deep(.el-dialog__footer) {
    flex-shrink: 0;
    padding: 15px 20px;
    border-top: 1px solid #ebeef5;
  }
}

.dialog-form {
  max-height: none;
}
</style>
