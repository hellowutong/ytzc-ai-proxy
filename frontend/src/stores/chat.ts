import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Conversation, Message } from '@/types'
import { useModelStore } from './models'

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const isStreaming = ref(false)
  const settings = ref({
    temperature: 0.7,
    max_tokens: 2000,
    stream: true,
    knowledge_enabled: true,
    web_search_enabled: false,
    dark_theme: true,
    code_highlight: true,
    show_thinking: false
  })

  // Actions
  async function fetchConversations() {
    try {
      const response = await fetch('/admin/ai/v1/conversations')
      const result = await response.json()
      if (result.code === 200) {
        conversations.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    }
  }

  async function createConversation(model: string) {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      model,
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    conversations.value.unshift(newConversation)
    currentConversation.value = newConversation
    return newConversation
  }

  function setCurrentConversation(conversation: Conversation | null) {
    currentConversation.value = conversation
  }

  async function sendMessage(content: string, model: string) {
    if (!currentConversation.value) {
      await createConversation(model)
    }

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }

    currentConversation.value?.messages.push(userMessage)

    try {
      isStreaming.value = true

      // 获取当前模型的 proxy_key 用于认证
      const modelStore = useModelStore()
      const currentVm = modelStore.models.find(m => m.name === model)
      const proxyKey = currentVm?.proxy_key || ''

      const response = await fetch('/proxy/ai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${proxyKey}`
        },
        body: JSON.stringify({
          model,
          messages: currentConversation.value?.messages || [],
          temperature: settings.value.temperature,
          max_tokens: settings.value.max_tokens,
          stream: settings.value.stream
        })
      })

      if (settings.value.stream) {
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        let assistantContent = ''

        const assistantMessage: Message = {
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString()
        }
        currentConversation.value?.messages.push(assistantMessage)

        while (reader) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') continue

              try {
                const parsed = JSON.parse(data)
                const delta = parsed.choices?.[0]?.delta?.content
                if (delta) {
                  assistantContent += delta
                  if (assistantMessage) {
                    assistantMessage.content = assistantContent
                  }
                }
              } catch (e) {
                // Ignore parse errors
              }
            }
          }
        }
      } else {
        const result = await response.json()
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.choices?.[0]?.message?.content || '',
          timestamp: new Date().toISOString()
        }
        currentConversation.value?.messages.push(assistantMessage)
      }

      if (currentConversation.value) {
        currentConversation.value.updated_at = new Date().toISOString()
      }

      // 刷新模型数据以获取最新的 current 值（关键词切换后需要更新显示）
      await modelStore.fetchModels()

    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      isStreaming.value = false
    }
  }

  function stopStreaming() {
    isStreaming.value = false
  }

  function updateSettings(newSettings: Partial<typeof settings.value>) {
    settings.value = { ...settings.value, ...newSettings }
  }

  function clearCurrentConversation() {
    if (currentConversation.value) {
      currentConversation.value.messages = []
    }
  }

  return {
    conversations,
    currentConversation,
    isStreaming,
    settings,
    fetchConversations,
    createConversation,
    setCurrentConversation,
    sendMessage,
    stopStreaming,
    updateSettings,
    clearCurrentConversation
  }
})
