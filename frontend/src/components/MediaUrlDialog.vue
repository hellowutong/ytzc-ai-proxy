<template>
  <el-dialog
    v-model="visible"
    title="URL下载"
    width="500px"
  >
    <el-form :model="form" label-width="120px"
    >
      <el-form-item label="视频URL" required>
        <el-input 
          v-model="form.url" 
          placeholder="https://example.com/video.mp4"
          type="textarea"
          rows="3"
        />
      </el-form-item>
      
      <el-form-item label="转录处理器">
        <el-select v-model="form.processor">
          <el-option 
            v-for="p in processors" 
            :key="p" 
            :label="p" 
            :value="p"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="模型">
        <el-select v-model="form.model">
          <el-option 
            v-for="m in models" 
            :key="m" 
            :label="m" 
            :value="m"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="语言">
        <el-select v-model="form.language">
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
          <el-option label="自动检测" value="auto" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="自动转录">
        <el-switch v-model="form.auto_process" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleDownload" :disabled="!form.url">开始下载</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  modelValue: boolean
  type: string
  processors: string[]
  models: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'download', data: { url: string; config: any }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  url: '',
  processor: props.processors[0] || 'default',
  model: props.models[0] || 'base',
  language: 'zh',
  auto_process: true
})

const handleDownload = () => {
  if (!form.value.url) return
  
  emit('download', {
    url: form.value.url,
    config: {
      processor: form.value.processor,
      model: form.value.model,
      language: form.value.language,
      auto_process: form.value.auto_process
    }
  })
  
  // Reset form
  form.value.url = ''
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
