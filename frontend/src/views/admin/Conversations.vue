<template>
  <div class="conversations">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索会话内容"
        clearable
        style="width: 300px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="margin-left: 12px;"
      />
    </div>

    <!-- Conversations Table -->
    <el-card class="table-card">
      <el-table :data="filteredConversations" style="width: 100%" v-loading="chatStore.loading">
        <el-table-column prop="id" label="ID" width="300">
          <template #default="{ row }">
            <span class="id-cell">{{ row.id.slice(0, 8) }}...</span>
          </template>
        </el-table-column>

        <el-table-column prop="model" label="使用模型" width="150" />

        <el-table-column label="消息数" width="150">
          <template #default="{ row }">
            <el-tag>{{ row.messages?.length || 0 }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="最后更新" width="180">
          <template #default="{ row }">
            {{ new Date(row.updated_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="350" fixed="right" class-name="operation-column">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewConversation(row)">查看</el-button>
            <el-button link type="danger" @click="deleteConversation(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Conversation Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      title="对话详情"
      width="800px"
      class="conversation-dialog"
    >
      <div v-if="selectedConversation" class="conversation-detail">
        <div class="detail-header">
          <span>模型: {{ selectedConversation.model }}</span>
          <span>消息数: {{ selectedConversation.messages?.length || 0 }}</span>
        </div>
        
        <div class="messages-container">
          <div 
            v-for="(msg, index) in selectedConversation.messages" 
            :key="index"
            class="message-item"
            :class="msg.role"
          >
            <div class="message-role">{{ msg.role === 'user' ? '用户' : 'AI' }}</div>
            <div class="message-content">{{ msg.content }}</div>
            <div v-if="msg.timestamp" class="message-time">
              {{ new Date(msg.timestamp).toLocaleString('zh-CN') }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores'
import type { Conversation } from '@/types'

const chatStore = useChatStore()

const searchQuery = ref('')
const dateRange = ref([])
const showDetailDialog = ref(false)
const selectedConversation = ref<Conversation | null>(null)

const filteredConversations = computed(() => {
  let result = chatStore.conversations
  
  if (searchQuery.value) {
    result = result.filter(c => {
      const searchLower = searchQuery.value.toLowerCase()
      return c.id.toLowerCase().includes(searchLower) ||
        c.messages?.some(m => m.content.toLowerCase().includes(searchLower))
    })
  }
  
  return result
})

const viewConversation = (conversation: Conversation) => {
  selectedConversation.value = conversation
  showDetailDialog.value = true
}

const deleteConversation = async (conversation: Conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除此对话吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    // TODO: Implement delete API
    ElMessage.success('删除成功')
  } catch {
    // Cancelled
  }
}

onMounted(() => {
  chatStore.fetchConversations()
})
</script>

<style scoped>
.conversations {
  padding: 0;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.table-card {
  background: #252526;
  border: 1px solid #3C3C3C;
}

.id-cell {
  font-family: monospace;
  color: #858585;
}

.conversation-dialog :deep(.el-dialog) {
  background: #252526;
}

.conversation-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #3C3C3C;
  margin-right: 0;
  padding: 20px;
}

.conversation-dialog :deep(.el-dialog__title) {
  color: #CCCCCC;
}

.conversation-dialog :deep(.el-dialog__body) {
  padding: 20px;
  background: #1E1E1E;
}

.detail-header {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #3C3C3C;
  color: #858585;
}

.messages-container {
  max-height: 500px;
  overflow-y: auto;
}

.message-item {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #2D2D30;
}

.message-item.user {
  background: #007ACC20;
  border-left: 3px solid #007ACC;
}

.message-item.assistant {
  background: #2D2D30;
  border-left: 3px solid #3fb950;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: #858585;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.message-content {
  color: #CCCCCC;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-time {
  font-size: 11px;
  color: #6e7681;
  margin-top: 8px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table th.el-table__cell) {
  color: var(--text-secondary) !important;
}

/* 统一所有表头单元格背景色，包括固定列 */
:deep(.el-table .el-table__header-wrapper th.el-table__cell),
:deep(.el-table .el-table__fixed-header-wrapper th.el-table__cell) {
  background-color: var(--bg-tertiary) !important;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-hover);
}
</style>
