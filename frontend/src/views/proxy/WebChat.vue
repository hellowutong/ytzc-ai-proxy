<template>
  <div class="webchat">
    <!-- Left Sidebar - Conversation History -->
    <aside class="sidebar-left">
      <div class="sidebar-header">
        <el-button type="primary" @click="createNewChat" class="new-chat-btn">
          <el-icon><Plus /></el-icon>新建对话
        </el-button>
      </div>
      
      <div class="conversation-list">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: chatStore.currentConversation?.id === conv.id }"
          @click="selectConversation(conv)"
        >
          <div class="conv-info">
            <div class="conv-title">对话 {{ conv.id.slice(0, 8) }}</div>
            <div class="conv-preview">{{ getPreview(conv) }}</div>
          </div>
          <el-button 
            link 
            class="delete-btn" 
            @click.stop="deleteConversation(conv)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <el-button link @click="showSettings = true">
          <el-icon><Setting /></el-icon>设置
        </el-button>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <div class="chat-main">
      <!-- Header -->
      <header class="chat-header">
        <div class="model-selector">
          <span>模型:</span>
          <el-select v-model="selectedModel" placeholder="选择模型" style="width: 160px;">
            <el-option 
              v-for="model in modelStore.enabledModels" 
              :key="model.name" 
              :label="model.name" 
              :value="model.name"
            />
          </el-select>
        </div>
        
        <div class="header-actions">
          <el-tag v-if="currentModelInfo">{{ currentModelInfo }}</el-tag>
          <el-button @click="clearChat">清空对话</el-button>
        </div>
      </header>

      <!-- Messages -->
      <div class="messages-area" ref="messagesContainer">
        <div v-if="!chatStore.currentConversation?.messages?.length" class="empty-state">
          <div class="welcome-text">
            <h2>👋 欢迎使用 AI Gateway</h2>
            <p>选择一个模型开始对话</p>
          </div>
        </div>
        
        <template v-else>
          <div
            v-for="(msg, index) in chatStore.currentConversation.messages"
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <div class="message-bubble">{{ msg.content }}</div>
              <div v-if="msg.timestamp" class="message-time">
                {{ new Date(msg.timestamp).toLocaleTimeString('zh-CN') }}
              </div>
            </div>
          </div>
          
          <div v-if="chatStore.isStreaming" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入消息... (Shift+Enter换行)"
            @keydown.shift.enter.prevent="inputMessage += '\\n'"
            @keydown.enter.exact.prevent="sendMessage"
            resize="none"
          />
          
          <div class="input-actions">
            <el-button 
              v-if="chatStore.isStreaming"
              type="danger" 
              @click="stopGeneration"
            >
              <el-icon><VideoPause /></el-icon>停止
            </el-button>
            <el-button 
              v-else
              type="primary" 
              :disabled="!inputMessage.trim() || !selectedModel"
              @click="sendMessage"
            >
              <el-icon><Promotion /></el-icon>发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Settings Drawer -->
    <el-drawer
      v-model="showSettings"
      title="⚙️ 设置"
      direction="rtl"
      size="360px"
    >
      <div class="settings-content">
        <h4>模型参数</h4>
        <el-form label-width="120px">
          <el-form-item label="Temperature">
            <el-slider v-model="chatStore.settings.temperature" :min="0" :max="2" :step="0.1" show-input />
          </el-form-item>
          
          <el-form-item label="Max Tokens">
            <el-input-number v-model="chatStore.settings.max_tokens" :min="100" :max="8000" :step="100" />
          </el-form-item>
          
          <el-form-item label="流式响应">
            <el-switch v-model="chatStore.settings.stream" />
          </el-form-item>
        </el-form>

        <el-divider />

        <h4>功能开关</h4>
        <el-form label-width="120px">
          <el-form-item label="知识库检索">
            <el-switch v-model="chatStore.settings.knowledge_enabled" />
          </el-form-item>
          
          <el-form-item label="联网搜索">
            <el-switch v-model="chatStore.settings.web_search_enabled" />
          </el-form-item>
        </el-form>

        <el-divider />

        <h4>显示设置</h4>
        <el-form label-width="120px">
          <el-form-item label="代码高亮">
            <el-switch v-model="chatStore.settings.code_highlight" />
          </el-form-item>
          
          <el-form-item label="显示思考过程">
            <el-switch v-model="chatStore.settings.show_thinking" />
          </el-form-item>
        </el-form>

        <div class="settings-actions">
          <el-button type="primary" @click="saveSettings">保存</el-button>
          <el-button @click="resetSettings">重置为默认</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Setting, VideoPause, Promotion } from '@element-plus/icons-vue'
import { useChatStore, useModelStore } from '@/stores'
import type { Conversation } from '@/types'

const chatStore = useChatStore()
const modelStore = useModelStore()

const selectedModel = ref('')
const inputMessage = ref('')
const showSettings = ref(false)
const messagesContainer = ref<HTMLDivElement>()

const currentModelInfo = computed(() => {
  if (!selectedModel.value) return null
  const model = modelStore.models.find(m => m.name === selectedModel.value)
  if (!model) return null
  return `${model.current === 'small' ? '小模型' : '大模型'}: ${model[model.current].model}`
})

const getPreview = (conv: Conversation) => {
  const lastMsg = conv.messages?.[conv.messages.length - 1]
  return lastMsg ? lastMsg.content.slice(0, 30) + '...' : '无消息'
}

const createNewChat = async () => {
  if (!selectedModel.value) {
    ElMessage.warning('请先选择模型')
    return
  }
  await chatStore.createConversation(selectedModel.value)
  scrollToBottom()
}

const selectConversation = (conv: Conversation) => {
  chatStore.setCurrentConversation(conv)
  selectedModel.value = conv.model
}

const deleteConversation = async (conv: Conversation) => {
  // TODO: Implement delete
  ElMessage.info('删除功能开发中')
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedModel.value) return
  
  const message = inputMessage.value
  inputMessage.value = ''
  
  if (!chatStore.currentConversation) {
    await chatStore.createConversation(selectedModel.value)
  }
  
  await chatStore.sendMessage(message, selectedModel.value)
  scrollToBottom()
}

const stopGeneration = () => {
  chatStore.stopStreaming()
}

const clearChat = () => {
  chatStore.clearCurrentConversation()
}

const saveSettings = () => {
  ElMessage.success('设置已保存')
  showSettings.value = false
}

const resetSettings = () => {
  chatStore.updateSettings({
    temperature: 0.7,
    max_tokens: 2000,
    stream: true,
    knowledge_enabled: true,
    web_search_enabled: false,
    code_highlight: true,
    show_thinking: false
  })
  ElMessage.success('设置已重置')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  modelStore.fetchModels()
  chatStore.fetchConversations()
})
</script>

<style scoped>
.webchat {
  display: flex;
  height: 100vh;
  background: var(--vscode-bg);
}

/* Sidebar */
.sidebar-left {
  width: 280px;
  background: var(--vscode-sidebar-bg);
  border-right: 1px solid var(--vscode-border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--vscode-border);
}

.new-chat-btn {
  width: 100%;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  background: #2a2d2e;
}

.conversation-item.active {
  background: #264f78;
  border-left: 3px solid #007acc;
}

.conv-info {
  flex: 1;
  overflow: hidden;
}

.conv-title {
  font-weight: 500;
  color: var(--vscode-text);
  margin-bottom: 4px;
}

.conv-preview {
  font-size: 12px;
  color: var(--vscode-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: var(--vscode-text-secondary);
}

.conversation-item:hover .delete-btn {
  opacity: 1;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--vscode-border);
}

/* Main Chat */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  height: 60px;
  background: var(--vscode-sidebar-bg);
  border-bottom: 1px solid var(--vscode-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--vscode-text);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Messages */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.welcome-text {
  text-align: center;
  color: var(--vscode-text-secondary);
}

.welcome-text h2 {
  color: var(--vscode-text);
  margin-bottom: 8px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #3c3c3c;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #3c3c3c;
  color: var(--vscode-text);
  line-height: 1.6;
}

.message.user .message-bubble {
  background: #007acc;
}

.message-time {
  font-size: 11px;
  color: #858585;
  margin-top: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #3c3c3c;
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--vscode-text-secondary);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

/* Input */
.input-area {
  padding: 16px 24px;
  background: var(--vscode-sidebar-bg);
  border-top: 1px solid var(--vscode-border);
}

.input-wrapper {
  position: relative;
}

.input-actions {
  position: absolute;
  right: 8px;
  bottom: 8px;
}

/* Settings */
.settings-content {
  padding: 0;
}

.settings-content h4 {
  color: var(--vscode-text);
  margin: 20px 0 16px;
}

.settings-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--vscode-border);
}

:deep(.el-drawer) {
  background: var(--vscode-sidebar-bg);
}

:deep(.el-drawer__header) {
  color: var(--vscode-text);
  border-bottom: 1px solid var(--vscode-border);
  margin-bottom: 0;
  padding: 20px;
}

:deep(.el-drawer__body) {
  padding: 0 20px 20px;
}

/* Override Element Plus components */
:deep(.el-textarea__inner) {
  background-color: var(--vscode-input-bg);
  border-color: var(--vscode-input-border);
  color: var(--vscode-text);
}

:deep(.el-textarea__inner:focus) {
  border-color: var(--vscode-blue);
}

:deep(.el-select .el-input__wrapper) {
  background-color: var(--vscode-input-bg);
  box-shadow: 0 0 0 1px var(--vscode-input-border);
}

:deep(.el-select .el-input__inner) {
  color: var(--vscode-text);
}
</style>
