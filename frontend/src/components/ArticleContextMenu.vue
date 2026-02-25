<template>
  <div
    v-show="modelValue"
    class="context-menu"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <!-- 标记已读/未读 - 根据文章状态显示不同选项 -->
    <div v-if="article && !article.is_read" class="menu-item" @click="handleAction('markRead')">
      <el-icon><Reading /></el-icon>
      <span>标记为已读</span>
    </div>
    <div v-if="article && article.is_read" class="menu-item" @click="handleAction('markUnread')">
      <el-icon><Reading /></el-icon>
      <span>标记为未读</span>
    </div>
    <div class="menu-divider"></div>
    
    <!-- 复制链接 -->
    <div class="menu-item" @click="handleAction('copyLink')">
      <el-icon><Link /></el-icon>
      <span>复制链接</span>
    </div>
    <div class="menu-divider"></div>
    
    <!-- 删除文章 - 危险操作 -->
    <div class="menu-item delete" @click="handleAction('delete')">
      <el-icon><Delete /></el-icon>
      <span>删除文章</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { Reading, Link, Delete } from '@element-plus/icons-vue'
import type { RSSArticle } from '@/types'

const props = defineProps<{
  modelValue: boolean
  position: { x: number; y: number }
  article: RSSArticle | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'markRead': [article: RSSArticle]
  'markUnread': [article: RSSArticle]
  'copyLink': [article: RSSArticle]
  'delete': [article: RSSArticle]
}>()

const handleAction = (action: 'markRead' | 'markUnread' | 'copyLink' | 'delete') => {
  if (!props.article) return
  
  emit('update:modelValue', false)
  emit(action, props.article)
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
