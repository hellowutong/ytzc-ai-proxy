<template>
  <div
    v-show="modelValue"
    class="context-menu"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <div class="menu-item" @click="handleAction('rename')">
      <el-icon><Document /></el-icon>
      <span>重命名</span>
    </div>
    <div class="menu-divider"></div>
    <div class="menu-item" @click="handleAction('fetch')">
      <el-icon><Refresh /></el-icon>
      <span>立即抓取</span>
    </div>
    <div class="menu-divider"></div>
    <div class="menu-item delete" @click="handleAction('delete')">
      <el-icon><Delete /></el-icon>
      <span>删除</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { Document, Refresh, Delete } from '@element-plus/icons-vue'
import type { RSSFeed } from '@/types'

const props = defineProps<{
  modelValue: boolean
  position: { x: number; y: number }
  feed: RSSFeed | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'rename': [feed: RSSFeed]
  'delete': [feed: RSSFeed]
  'fetch': [feed: RSSFeed]
}>()

const handleAction = (action: 'rename' | 'delete' | 'fetch') => {
  if (!props.feed) return
  
  emit('update:modelValue', false)
  emit(action, props.feed)
}

// 点击外部关闭菜单
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.context-menu')) {
    emit('update:modelValue', false)
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: #252526;
  border: 1px solid #454545;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  min-width: 140px;
  padding: 4px 0;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #cccccc;
  transition: background 0.2s ease;
}

.menu-item:hover {
  background: #094771;
  color: #fff;
}

.menu-item.delete:hover {
  background: #dc3545;
}

.menu-divider {
  height: 1px;
  background: #454545;
  margin: 4px 0;
}
</style>
