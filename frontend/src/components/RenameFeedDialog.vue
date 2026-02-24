<template>
  <el-dialog
    v-model="visible"
    title="重命名订阅"
    width="300px"
    class="rename-dialog"
    destroy-on-close
    @opened="onDialogOpened"
  >
    <div class="rename-form">
      <div class="current-name">
        当前名称: {{ feed?.name }}
      </div>
      
      <el-input
        ref="nameInputRef"
        v-model="newName"
        placeholder="输入新名称"
        size="large"
        @keyup.enter="handleConfirm"
      />
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button size="small" @click="visible = false">取消</el-button>
        <el-button size="small" type="primary" @click="handleConfirm" :loading="loading">确认</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { RSSFeed } from '@/types'

const props = defineProps<{
  modelValue: boolean
  feed: RSSFeed | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [feedId: string, newName: string]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const nameInputRef = ref()
const newName = ref('')
const loading = ref(false)

// 监听feed变化，更新输入框值
watch(() => props.feed, (feed) => {
  if (feed) {
    newName.value = feed.name
  }
}, { immediate: true })

// 对话框打开后选中输入框文本
const onDialogOpened = () => {
  nextTick(() => {
    nameInputRef.value?.input?.select()
  })
}

const handleConfirm = () => {
  if (!props.feed) return
  
  const trimmedName = newName.value.trim()
  if (!trimmedName) {
    return
  }
  
  if (trimmedName === props.feed.name) {
    visible.value = false
    return
  }
  
  loading.value = true
  emit('confirm', props.feed.id, trimmedName)
  loading.value = false
  visible.value = false
}
</script>

<style scoped>
.rename-form {
  padding: 16px 0;
}

.current-name {
  font-size: 13px;
  color: #858585;
  margin-bottom: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.el-dialog) {
  background: #252526;
  border: 1px solid #454545;
}

:deep(.el-dialog__title) {
  color: #cccccc;
  font-size: 15px;
}

:deep(.el-dialog__body) {
  padding: 0 20px;
}

:deep(.el-input__wrapper) {
  background: #3c3c3c !important;
}

:deep(.el-input__inner) {
  color: #cccccc !important;
}
</style>
