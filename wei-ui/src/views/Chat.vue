<template>
  <div class="chat-container">
    <el-row :gutter="20" class="chat-layout">
      <!-- Left Sidebar: Settings -->
      <el-col :span="6" class="sidebar-col">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>对话设置</span>
            </div>
          </template>
          
          <div class="settings-content">
            <!-- Model Selection -->
            <div class="setting-item">
              <label>选择模型</label>
              <el-select 
                v-model="selectedModel" 
                placeholder="选择模型"
                style="width: 100%"
                :loading="modelsLoading"
              >
                <el-option 
                  v-for="model in models" 
                  :key="model.id" 
                  :label="model.id" 
                  :value="model.id" 
                />
              </el-select>
            </div>

            <!-- API Key -->
            <div class="setting-item">
              <label>API Key (proxy_key)</label>
              <el-input 
                v-model="apiKey" 
                type="password" 
                placeholder="输入API Key"
                show-password
                clearable
              />
            </div>

            <!-- Streaming Toggle -->
            <div class="setting-item">
              <el-switch v-model="streamEnabled" active-text="流式响应" />
            </div>

            <!-- Advanced Settings -->
            <el-collapse v-model="activeCollapse">
              <el-collapse-item title="高级设置" name="advanced">
                <div class="setting-item">
                  <label>Temperature: {{ temperature }}</label>
                  <el-slider v-model="temperature" :min="0" :max="2" :step="0.1" />
                </div>
                <div class="setting-item">
                  <label>Max Tokens: {{ maxTokens }}</label>
                  <el-slider v-model="maxTokens" :min="1" :max="4096" :step="1" />
                </div>
                <div class="setting-item">
                  <label>Top P: {{ topP }}</label>
                  <el-slider v-model="topP" :min="0" :max="1" :step="0.1" />
                </div>
              </el-collapse-item>
            </el-collapse>

            <!-- Action Buttons -->
            <div class="action-buttons">
              <el-button 
                type="danger" 
                plain 
                @click="clearChat"
                :icon="Delete"
              >
                清空对话
              </el-button>
              <el-button 
                type="info" 
                plain 
                @click="exportChat"
                :icon="Download"
              >
                导出
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Right: Chat Area -->
      <el-col :span="18" class="chat-col">
        <el-card class="chat-card">
          <template #header>
            <div class="chat-header">
              <span class="chat-title">AI 对话</span>
              <el-tag v-if="selectedModel" type="primary" size="small">
                {{ selectedModel }}
              </el-tag>
            </div>
          </template>

          <div class="messages-container" ref="messagesRef">
            <div v-if="messages.length === 0" class="empty-state">
              <el-icon :size="48" color="#909399"><ChatDotRound /></el-icon>
              <p>在下方输入消息开始对话</p>
            </div>

            <template v-else>
              <div
                v-for="(msg, index) in messages"
                :key="index"
                :class="['message', msg.role]"
              >
                <div class="message-avatar">
                  <el-avatar
                    :size="40"
                    :icon="msg.role === 'user' ? User : ChatDotRound"
                    :style="{ backgroundColor: msg.role === 'user' ? '#409EFF' : '#67C23A' }"
                  />
                </div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="role-name">{{ msg.role === 'user' ? '用户' : 'AI助手' }}</span>
                    <span class="message-time">{{ msg.timestamp ? formatTime(msg.timestamp) : '' }}</span>
                  </div>
                  <div class="message-text" v-html="formatMessage(msg.content)" />
                  <div v-if="msg.usage" class="message-usage">
                    <el-tag size="small" type="info">
                      Tokens: {{ msg.usage.total_tokens }} (Prompt: {{ msg.usage.prompt_tokens }}, Completion: {{ msg.usage.completion_tokens }})
                    </el-tag>
                  </div>
                </div>
              </div>

              <div v-if="isLoading" class="message assistant">
                <div class="message-avatar">
                  <el-avatar :size="40" :icon="ChatDotRound" style="background-color: #67C23A" />
                </div>
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

          <div class="input-area">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入消息... (Enter发送, Shift+Enter换行)"
              :disabled="isLoading"
              @keydown.enter.prevent="handleEnterKey"
            />
            <el-button
              type="primary"
              :loading="isLoading"
              :disabled="!inputMessage.trim() || !selectedModel || !apiKey"
              @click="sendMessage"
              class="send-btn"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Delete, User, ChatDotRound, Promotion, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAvailableModels,
  sendChatMessage,
  sendChatMessageStream,
  type ChatMessage,
  type ModelInfo,
} from '../api/chat'

// Message type with additional metadata
interface Message extends ChatMessage {
  timestamp?: number
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// State
const messages = ref<Message[]>([])
const inputMessage = ref('')
const selectedModel = ref('')
const models = ref<ModelInfo[]>([])
const modelsLoading = ref(false)
const apiKey = ref('')
const streamEnabled = ref(true)
const temperature = ref(0.7)
const maxTokens = ref(2048)
const topP = ref(1.0)
const isLoading = ref(false)
const activeCollapse = ref<string[]>([])
const messagesRef = ref<HTMLElement>()

// Load saved values from localStorage
onMounted(() => {
  const savedApiKey = localStorage.getItem('chat_api_key')
  const savedModel = localStorage.getItem('chat_selected_model')
  const savedStream = localStorage.getItem('chat_stream_enabled')
  const savedTemp = localStorage.getItem('chat_temperature')
  const savedMaxTokens = localStorage.getItem('chat_max_tokens')
  const savedTopP = localStorage.getItem('chat_top_p')

  if (savedApiKey) apiKey.value = savedApiKey
  if (savedModel) selectedModel.value = savedModel
  if (savedStream) streamEnabled.value = savedStream === 'true'
  if (savedTemp) temperature.value = parseFloat(savedTemp)
  if (savedMaxTokens) maxTokens.value = parseInt(savedMaxTokens)
  if (savedTopP) topP.value = parseFloat(savedTopP)

  fetchModels()
})

// Save to localStorage when values change
watch(apiKey, (val) => localStorage.setItem('chat_api_key', val))
watch(selectedModel, (val) => localStorage.setItem('chat_selected_model', val))
watch(streamEnabled, (val) => localStorage.setItem('chat_stream_enabled', String(val)))
watch(temperature, (val) => localStorage.setItem('chat_temperature', String(val)))
watch(maxTokens, (val) => localStorage.setItem('chat_max_tokens', String(val)))
watch(topP, (val) => localStorage.setItem('chat_top_p', String(val)))

// Fetch available models from API
const fetchModels = async () => {
  modelsLoading.value = true
  try {
    const response = await getAvailableModels()
    models.value = response.data
    
    // Auto-select first model if none selected
    if (!selectedModel.value && models.value.length > 0) {
      selectedModel.value = models.value[0].id
    }
  } catch (error: any) {
    ElMessage.error('加载模型失败: ' + (error.message || '未知错误'))
  } finally {
    modelsLoading.value = false
  }
}

// Format message with line breaks
const formatMessage = (content: string): string => {
  return content.replace(/\n/g, '<br>')
}

// Format timestamp
const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// Handle enter key - send on Enter, new line on Shift+Enter
const handleEnterKey = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    sendMessage()
  }
}

// Scroll to bottom
const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// Send message
const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || !selectedModel.value || !apiKey.value || isLoading.value) return

  // Add user message
  const userMsg: Message = {
    role: 'user',
    content,
    timestamp: Date.now(),
  }
  messages.value.push(userMsg)
  inputMessage.value = ''
  isLoading.value = true

  // Scroll to bottom
  await nextTick()
  scrollToBottom()

  // Prepare messages for API
  const apiMessages: ChatMessage[] = messages.value
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => ({ role: m.role, content: m.content }))

  try {
    if (streamEnabled.value) {
      // Streaming mode
      const assistantMsg: Message = {
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      }
      messages.value.push(assistantMsg)

      await sendChatMessageStream(
        {
          model: selectedModel.value,
          messages: apiMessages,
          stream: true,
          temperature: temperature.value,
          max_tokens: maxTokens.value,
          top_p: topP.value,
        },
        apiKey.value,
        (chunk, done) => {
          if (done) {
            isLoading.value = false
          } else {
            assistantMsg.content += chunk
            scrollToBottom()
          }
        }
      )
    } else {
      // Non-streaming mode
      const response = await sendChatMessage(
        {
          model: selectedModel.value,
          messages: apiMessages,
          stream: false,
          temperature: temperature.value,
          max_tokens: maxTokens.value,
          top_p: topP.value,
        },
        apiKey.value
      )

      const assistantContent = response.choices[0]?.message?.content || ''
      messages.value.push({
        role: 'assistant',
        content: assistantContent,
        timestamp: Date.now(),
        usage: response.usage,
      })
      isLoading.value = false
    }
  } catch (error: any) {
    ElMessage.error('发送失败: ' + (error.message || '请求失败'))
    // Remove the user message on error so user can retry
    messages.value.pop()
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// Clear chat
const clearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有对话消息吗？',
      '清空对话',
      {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    messages.value = []
    ElMessage.success('对话已清空')
  } catch {
    // User cancelled
  }
}

// Export chat
const exportChat = () => {
  if (messages.value.length === 0) {
    ElMessage.warning('没有消息可导出')
    return
  }

  const exportData = {
    model: selectedModel.value,
    timestamp: new Date().toISOString(),
    messages: messages.value,
  }

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success('对话已导出')
}
</script>

<style scoped lang="scss">
.chat-container {
  padding: 20px;
  height: calc(100vh - 100px);
}

.chat-layout {
  height: 100%;
}

.sidebar-col {
  height: 100%;
}

.settings-card {
  height: 100%;
  
  :deep(.el-card__body) {
    padding: 16px;
    height: calc(100% - 60px);
    overflow-y: auto;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-item label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.action-buttons .el-button {
  flex: 1;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  gap: 16px;

  p {
    font-size: 14px;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  
  span {
    width: 8px;
    height: 8px;
    background: #909399;
    border-radius: 50%;
    animation: typing 1s infinite;
  }

  span:nth-child(2) {
    animation-delay: 0.2s;
  }

  span:nth-child(3) {
    animation-delay: 0.4s;
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.chat-col {
  height: 100%;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0;
  }
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--el-fill-color-light);
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      background-color: var(--el-color-primary-light-9);
    }
  }

  &.assistant {
    .message-content {
      background-color: white;
    }
  }

  .message-content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .message-text {
      line-height: 1.6;
      word-break: break-word;
    }

    .message-usage {
      margin-top: 8px;
    }
  }
}

.input-area {
  padding: 20px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  gap: 12px;
  align-items: flex-end;

  .el-textarea {
    flex: 1;
  }

  .send-btn {
    margin-bottom: 4px;
  }
}
</style>