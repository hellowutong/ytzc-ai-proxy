<template>
  <div class="config-page">
    <div class="page-header">
      <h2>系统配置</h2>
      <el-button type="primary" @click="saveConfig" :loading="saving">
        <el-icon><Check /></el-icon>
        保存配置
      </el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="基础配置" name="basic">
        <el-form :model="config" label-width="120px">
          <el-form-item label="应用名称">
            <el-input v-model="config.app_name" placeholder="TW AI Saver" />
          </el-form-item>
          <el-form-item label="API Base URL">
            <el-input v-model="config.api_base_url" placeholder="http://localhost:8080" />
          </el-form-item>
          <el-form-item label="默认代理 Key">
            <el-input v-model="config.default_proxy_key" type="password" show-password placeholder="Proxy Key" />
          </el-form-item>
          <el-form-item label="会话自动摘要">
            <el-switch v-model="config.auto_summarize" />
            <span class="form-tip">会话结束时自动生成摘要</span>
          </el-form-item>
          <el-form-item label="摘要长度">
            <el-slider v-model="config.summary_max_length" :min="100" :max="2000" show-input />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="AI 提供商" name="providers">
        <el-form :model="config.providers" label-width="120px">
          <el-form-item label="默认提供商">
            <el-select v-model="config.default_provider" placeholder="选择默认提供商" style="width: 300px">
              <el-option label="OpenAI" value="openai" />
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Anthropic" value="anthropic" />
              <el-option label="Google" value="google" />
            </el-select>
          </el-form-item>
          <el-form-item label="请求超时(秒)">
            <el-input-number v-model="config.request_timeout" :min="10" :max="300" />
          </el-form-item>
          <el-form-item label="自动重试">
            <el-switch v-model="config.auto_retry" />
          </el-form-item>
          <el-form-item label="重试次数">
            <el-input-number v-model="config.retry_count" :min="0" :max="5" :disabled="!config.auto_retry" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="安全配置" name="security">
        <el-form :model="config.security" label-width="120px">
          <el-form-item label="API Key 过期(天)">
            <el-input-number v-model="config.api_key_expire_days" :min="7" :max="365" />
          </el-form-item>
          <el-form-item label="Rate Limiting">
            <el-switch v-model="config.rate_limit_enabled" />
          </el-form-item>
          <el-form-item label="请求/分钟">
            <el-input-number v-model="config.rate_limit_requests" :min="10" :max="1000" :disabled="!config.rate_limit_enabled" />
          </el-form-item>
          <el-form-item label="审计日志">
            <el-switch v-model="config.audit_log_enabled" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="数据库" name="database">
        <el-form :model="config.database" label-width="120px">
          <el-form-item label="MongoDB URI">
            <el-input v-model="config.database.mongodb_uri" placeholder="mongodb://localhost:27017" />
          </el-form-item>
          <el-form-item label="Qdrant URL">
            <el-input v-model="config.database.qdrant_url" placeholder="http://localhost:6333" />
          </el-form-item>
          <el-form-item label="连接池大小">
            <el-input-number v-model="config.database.pool_size" :min="1" :max="100" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '@/api'

const activeTab = ref('basic')
const saving = ref(false)

const config = reactive({
  app_name: 'TW AI Saver',
  api_base_url: 'http://localhost:8080',
  default_proxy_key: '',
  auto_summarize: true,
  summary_max_length: 500,
  default_provider: 'deepseek',
  request_timeout: 60,
  auto_retry: true,
  retry_count: 3,
  api_key_expire_days: 30,
  rate_limit_enabled: true,
  rate_limit_requests: 60,
  audit_log_enabled: true,
  database: {
    mongodb_uri: 'mongodb://localhost:27017',
    qdrant_url: 'http://localhost:6333',
    pool_size: 10
  },
  providers: {},
  security: {}
})

async function loadConfig() {
  try {
    const data = await configApi.get()
    Object.assign(config, data)
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await configApi.update(config)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.config-page {
  padding: 0;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-color-secondary);
}
</style>
