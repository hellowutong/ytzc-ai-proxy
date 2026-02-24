<template>
  <el-dialog
    v-model="visible"
    title="RSS 配置"
    width="500px"
    class="rss-config-dialog"
    destroy-on-close
  >
    <!-- 抓取配置 -->
    <div class="config-section">
      <h3 class="section-title">📋 抓取配置</h3>
      
      <div class="config-item">
        <div class="config-label">
          <label>最大并发数</label>
          <span class="config-desc">同时抓取的最大订阅数</span>
        </div>
        <el-input-number v-model="config.max_concurrent" :min="1" :max="10" />
      </div>

      <div class="config-item">
        <div class="config-label">
          <label>自动抓取</label>
        </div>
        <el-switch v-model="config.auto_fetch" />
      </div>

      <div class="config-item">
        <div class="config-label">
          <label>抓取间隔（分钟）</label>
        </div>
        <el-input-number v-model="config.fetch_interval" :min="5" :max="1440" :step="5" />
      </div>

      <div class="config-item">
        <div class="config-label">
          <label>文章保留天数</label>
          <span class="config-desc">超过天数自动删除</span>
        </div>
        <el-input-number v-model="config.retention_days" :min="1" :max="365" />
      </div>

      <div class="config-item">
        <div class="config-label">
          <label>默认永久保存</label>
          <span class="config-desc">抓取的文章默认永久保存</span>
        </div>
        <el-switch v-model="config.default_permanent" />
      </div>
    </div>

    <el-divider />

    <!-- Skill 配置 -->
    <div class="config-section">
      <h3 class="section-title">🤖 Skill 配置</h3>

      <div class="config-item">
        <div class="config-label">
          <label>系统 Skill</label>
        </div>
        <div class="config-control">
          <el-switch v-model="config.skill.enabled" />
          <el-select v-model="config.skill.version" size="small" style="width: 80px; margin-left: 12px;" >
            <el-option label="v1" value="v1" />
            <el-option label="v2" value="v2" />
          </el-select>
        </div>
      </div>

      <div class="config-item">
        <div class="config-label">
          <label>自定义 Skill</label>
        </div>
        <div class="config-control">
          <el-switch v-model="config.skill.custom.enabled" />
          <el-select v-model="config.skill.custom.version" size="small" style="width: 80px; margin-left: 12px;">
            <el-option label="v1" value="v1" />
            <el-option label="v2" value="v2" />
          </el-select>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '@/stores'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const configStore = useConfigStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const saving = ref(false)

// 默认配置
const config = ref({
  max_concurrent: 5,
  auto_fetch: true,
  fetch_interval: 30,
  retention_days: 30,
  default_permanent: false,
  skill: {
    enabled: true,
    version: 'v1',
    custom: {
      enabled: true,
      version: 'v1'
    }
  }
})

const loadConfig = async () => {
  // 从 store 或 API 加载配置
  try {
    await configStore.fetchConfig()
    const rssConfig = configStore.config?.rss
    if (rssConfig) {
      config.value = {
        ...config.value,
        ...rssConfig,
        skill: {
          ...config.value.skill,
          ...rssConfig.skill
        }
      }
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    // 调用 API 保存配置
    const success = await configStore.updateConfig({
      rss: config.value
    })
    
    if (success) {
      ElMessage.success('配置保存成功')
      visible.value = false
    } else {
      ElMessage.error('保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (visible.value) {
    loadConfig()
  }
})

// 监听弹窗打开
import { watch } from 'vue'
watch(() => visible.value, (val) => {
  if (val) loadConfig()
})
</script>

<style scoped>
.config-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #cccccc;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #454545;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-label label {
  font-size: 14px;
  color: #cccccc;
  font-weight: 500;
}

.config-desc {
  font-size: 12px;
  color: #858585;
}

.config-control {
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog) {
  background: #252526;
  border: 1px solid #454545;
}

:deep(.el-dialog__title) {
  color: #cccccc;
}

:deep(.el-divider) {
  border-color: #454545;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: #3c3c3c;
  border-color: #454545;
  color: #cccccc;
}

:deep(.el-input__wrapper) {
  background: #3c3c3c !important;
}
</style>
