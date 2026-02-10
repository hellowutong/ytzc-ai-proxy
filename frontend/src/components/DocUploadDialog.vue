<template>
  <el-dialog
    v-model="visible"
    title="上传文档"
    width="500px"
  >
    <el-form :model="form" label-width="120px">
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
          <template #tip>
            <div class="el-upload__tip">支持 PDF, TXT, DOC, JPG 格式</div>
          </template>
        </el-upload>
      </el-form-item>
      
      <el-form-item label="目标虚拟模型">
        <el-select v-model="form.model" placeholder="选择模型">
          <el-option 
            v-for="model in modelStore.enabledModels" 
            :key="model.name" 
            :label="model.name" 
            :value="model.name"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="共享知识库">
        <el-switch v-model="form.shared" />
      </el-form-item>
      
      <el-form-item label="分段大小">
        <el-input-number v-model="form.chunk_size" :min="100" :max="2000" :step="100" />
      </el-form-item>
      
      <el-form-item label="重叠大小">
        <el-input-number v-model="form.overlap" :min="0" :max="500" :step="10" />
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
import { useModelStore } from '@/stores'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'upload', data: { file: File; model: string; shared: boolean }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const modelStore = useModelStore()

const form = ref({
  file: null as File | null,
  model: '',
  shared: false,
  chunk_size: 500,
  overlap: 50
})

const handleFileChange = (file: any) => {
  form.value.file = file.raw
}

const handleUpload = () => {
  if (!form.value.file || !form.value.model) return
  
  emit('upload', {
    file: form.value.file,
    model: form.value.model,
    shared: form.value.shared
  })
  
  // Reset form
  form.value = {
    file: null,
    model: '',
    shared: false,
    chunk_size: 500,
    overlap: 50
  }
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

.upload-dragger :deep(.el-upload__tip) {
  color: #858585;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
