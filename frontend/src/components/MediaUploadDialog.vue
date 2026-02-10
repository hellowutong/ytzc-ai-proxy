<template>
  <el-dialog
    v-model="visible"
    title="上传文件"
    width="500px"
  >
    <el-form :model="form" label-width="120px"
    >
      <el-form-item label="选择文件">
        <el-upload
          ref="uploadRef"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          class="upload-dragger"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
        </el-upload>
      </el-form-item>
      
      <el-form-item label="转录处理器" v-if="processors.length > 1">
        <el-select v-model="form.processor">
          <el-option 
            v-for="p in processors" 
            :key="p" 
            :label="p" 
            :value="p"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="模型" v-if="models.length">
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
        <el-button type="primary" @click="handleUpload" :disabled="!form.file">开始上传</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: boolean
  type: string
  processors: string[]
  models: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'upload', data: { file: File; config: any }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  file: null as File | null,
  processor: props.processors[0] || 'default',
  model: props.models[0] || 'base',
  language: 'zh',
  auto_process: true
})

const handleFileChange = (file: any) => {
  form.value.file = file.raw
}

const handleUpload = () => {
  if (!form.value.file) return
  
  emit('upload', {
    file: form.value.file,
    config: {
      processor: form.value.processor,
      model: form.value.model,
      language: form.value.language,
      auto_process: form.value.auto_process
    }
  })
  
  // Reset form
  form.value.file = null
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

.upload-dragger :deep(.el-upload-dragger) {
  background: #1E1E1E;
  border: 2px dashed #3C3C3C;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #007ACC;
}

.upload-dragger :deep(.el-icon--upload) {
  color: #858585;
}

.upload-dragger :deep(.el-upload__text) {
  color: #CCCCCC;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
