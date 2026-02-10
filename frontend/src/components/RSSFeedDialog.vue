<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑订阅' : '添加订阅'"
    width="500px"
  >
    <el-form :model="form" label-width="120px"
    >
      <el-form-item label="订阅名称" required>
        <el-input v-model="form.name" placeholder="如: 技术新闻" />
      </el-form-item>
      
      <el-form-item label="RSS URL" required>
        <el-input v-model="form.url" placeholder="https://example.com/feed.xml" />
      </el-form-item>
      
      <el-form-item label="启用状态">
        <el-switch v-model="form.enabled" />
      </el-form-item>
      
      <el-form-item label="更新频率">
        <el-select v-model="form.update_interval">
          <el-option label="30分钟" value="30m" />
          <el-option label="1小时" value="1h" />
          <el-option label="6小时" value="6h" />
          <el-option label="每天" value="1d" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="保留天数">
        <el-input-number v-model="form.retention_days" :min="1" :max="365" />
      </el-form-item>
      
      <el-form-item label="永久保存">
        <el-switch v-model="form.permanent" />
      </el-form-item>
      
      <el-form-item label="关联模型">
        <el-select v-model="form.model" placeholder="选择知识提取模型">
          <el-option 
            v-for="model in modelStore.enabledModels" 
            :key="model.name" 
            :label="model.name" 
            :value="model.name"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useModelStore } from '@/stores'
import type { RSSFeed } from '@/types'

const props = defineProps<{
  modelValue: boolean
  feed: RSSFeed | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', value: Omit<RSSFeed, 'id' | 'article_count'>): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const modelStore = useModelStore()

const isEdit = computed(() => !!props.feed)

const defaultForm = {
  name: '',
  url: '',
  enabled: true,
  update_interval: '1h',
  retention_days: 30,
  permanent: false,
  model: ''
}

const form = ref({ ...defaultForm })

watch(() => props.feed, (newFeed) => {
  if (newFeed) {
    form.value = {
      name: newFeed.name,
      url: newFeed.url,
      enabled: newFeed.enabled,
      update_interval: newFeed.update_interval,
      retention_days: newFeed.retention_days,
      permanent: newFeed.permanent,
      model: newFeed.model
    }
  } else {
    form.value = { ...defaultForm }
  }
}, { immediate: true })

const handleSubmit = () => {
  if (!form.value.name || !form.value.url) {
    ElMessage.warning('请填写必填项')
    return
  }
  emit('submit', { ...form.value })
}
</script>

<style scoped>
:deep(.el-dialog) {
  background: #252526;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #3C3C3C;
  margin-right: 0;
}

:deep(.el-dialog__title) {
  color: #CCCCCC;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
