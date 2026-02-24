<template>
  <div class="keyword-tag-input">
    <div class="tags-container">
      <el-tag
        v-for="(tag, index) in modelValue"
        :key="tag + index"
        closable
        @close="handleRemove(index)"
        class="keyword-tag"
        size="default"
      >
        {{ tag }}
      </el-tag>
      <el-input
        v-if="inputVisible"
        ref="inputRef"
        v-model="inputValue"
        size="small"
        class="tag-input"
        @keyup.enter="handleAdd"
        @keyup.escape="inputVisible = false"
        @blur="handleAdd"
      />
      <el-button
        v-else
        class="button-new-tag"
        size="small"
        @click="showInput"
        :disabled="modelValue.length >= maxTags"
      >
        + {{ placeholder || '添加关键词' }}
      </el-button>
    </div>
    <div class="counter">
      已添加 {{ modelValue.length }}/{{ maxTags }} 个关键词
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string[]
  placeholder?: string
  maxTags?: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref<HTMLInputElement>()

const maxTags = props.maxTags || 50

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleAdd = () => {
  const value = inputValue.value.trim()
  
  // 验证
  if (!value) {
    inputVisible.value = false
    inputValue.value = ''
    return
  }
  
  // 检查重复
  if (props.modelValue.includes(value)) {
    inputVisible.value = false
    inputValue.value = ''
    return
  }
  
  // 检查数量限制
  if (props.modelValue.length >= maxTags) {
    inputVisible.value = false
    inputValue.value = ''
    return
  }
  
  // 添加标签
  const newTags = [...props.modelValue, value]
  emit('update:modelValue', newTags)
  
  inputVisible.value = false
  inputValue.value = ''
}

const handleRemove = (index: number) => {
  const newTags = [...props.modelValue]
  newTags.splice(index, 1)
  emit('update:modelValue', newTags)
}
</script>

<style scoped>
.keyword-tag-input {
  width: 100%;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 32px;
  padding: 4px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.keyword-tag {
  margin: 0;
}

.tag-input {
  width: 120px;
}

.button-new-tag {
  border-style: dashed;
}

.counter {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
