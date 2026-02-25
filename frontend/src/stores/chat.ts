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
        // 去除重复ID的对话
        const seenIds = new Set<string>()
        const uniqueConversations = result.data.items.filter((conv: Conversation) => {
          if (seenIds.has(conv.id)) {
            console.warn('去除重复对话:', conv.id)
            return false
          }
          seenIds.add(conv.id)
          return true
        })
        
        // 保存当前对话ID
        const currentId = currentConversation.value?.id
        
        // 更新对话列表
        conversations.value = uniqueConversations
        
        // 如果之前有当前对话，在新列表中重新找到它
        if (currentId && currentConversation.value) {
          const found = conversations.value.find(c => c.id === currentId)
          if (found) {
            currentConversation.value = found
          } else {
            // 如果没找到，清空当前对话（说明已被删除）
            currentConversation.value = null
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    }
  }

  async function createConversation(model: string, metadata?: Record<string, any>) {
    try {
      // 先创建后端对话
      const response = await fetch('/admin/ai/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, metadata })
      })
      const result = await response.json()
      
      if (result.code === 200) {
        // 检查是否已存在相同ID的对话
        const existingIndex = conversations.value.findIndex(
          c => c.id === result.data.id
        )
        
        if (existingIndex !== -1) {
          // 已存在，直接使用已有对话，不创建新的
          currentConversation.value = conversations.value[existingIndex]
          return conversations.value[existingIndex]
        }
        
        // 创建新对话
        const newConversation: Conversation = {
          id: result.data.id,
          model,
          messages: [],
          metadata: result.data.metadata,  // 保存metadata
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
        conversations.value.unshift(newConversation)
        currentConversation.value = newConversation
        return newConversation
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
    return null
  }
    try {
      // 先创建后端对话
      const response = await fetch('/admin/ai/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model })
      })
      const result = await response.json()
      
      if (result.code === 200) {
        // 检查是否已存在相同ID的对话
        const existingIndex = conversations.value.findIndex(
          c => c.id === result.data.id
        )
        
        if (existingIndex !== -1) {
          // 已存在，直接使用已有对话，不创建新的
          currentConversation.value = conversations.value[existingIndex]
          return conversations.value[existingIndex]
        }
        
        // 创建新对话
        const newConversation: Conversation = {
          id: result.data.id,
          model,
          messages: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
        conversations.value.unshift(newConversation)
        currentConversation.value = newConversation
        return newConversation
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
    return null
  }

  function setCurrentConversation(conversation: Conversation | null) {
    currentConversation.value = conversation
  }

  async function sendMessage(content: string, model: string) {
    // 注意：createConversation 应该由调用方在发送消息前确保调用
    // 这里不再自动创建对话，避免重复创建

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
          conversation_id: currentConversation.value?.id || null,
          temperature: settings.value.temperature,
          max_tokens: settings.value.max_tokens,
          // 强制使用非流式（后端已统一为非流式响应）
          // stream: settings.value.stream
        })
      })

      // 检查Content-Type判断响应格式
      const contentType = response.headers.get('content-type') || ''
      const isJsonResponse = contentType.includes('application/json')

      if (isJsonResponse) {
        // 非流式响应 - 解析JSON
        const result = await response.json()

        // 检查是否是错误响应
        if (result.error) {
          const errorMessage: Message = {
            role: 'assistant',
            content: result.error.message || '抱歉，处理您的请求时出现了错误。',
            timestamp: new Date().toISOString()
          }
          currentConversation.value?.messages.push(errorMessage)
        } else {
          // 正常响应
          const assistantMessage: Message = {
            role: 'assistant',
            content: result.choices?.[0]?.message?.content || '',
            timestamp: new Date().toISOString()
          }
          currentConversation.value?.messages.push(assistantMessage)
        }
      } else {
        // 流式响应 (SSE) - 兼容旧版行为
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
                  assistantMessage.content = assistantContent
                }
              } catch (e) {
                // Ignore parse errors
              }
            }
          }
        }
      }

      if (currentConversation.value) {
        currentConversation.value.updated_at = new Date().toISOString()
      }

      // 刷新模型数据以获取最新的 current 值（关键词切换后需要更新显示）
      await modelStore.fetchModels()

    } catch (error) {
      console.error('Failed to send message:', error)
      // 添加错误消息到对话
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        timestamp: new Date().toISOString()
      }
      currentConversation.value?.messages.push(errorMessage)
    } finally {
      isStreaming.value = false
    }
  }

  async function saveConversation(conversation: Conversation | null) {
    if (!conversation) return
    
    try {
      // 确保对话有ID
      if (!conversation.id) {
        console.error('尝试保存没有ID的对话')
        return
      }
      
      const response = await fetch(`/admin/ai/v1/conversations/${conversation.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: conversation.messages,
          updated_at: conversation.updated_at
        })
      })
      
      // 如果405或404错误，静默处理（可能是旧版本后端）
      if (!response.ok) {
        console.warn(`保存对话失败: ${response.status}`)
        return
      }
      
      const result = await response.json()
      if (result.code === 200) {
        console.log('对话保存成功')
        // 不自动刷新对话列表，避免竞态条件和引用丢失
        // 只更新本地时间戳
        if (currentConversation.value) {
          currentConversation.value.updated_at = new Date().toISOString()
        }
      }
    } catch (error) {
      // 静默处理保存失败，不显示错误给用户
      console.warn('保存对话失败:', error)
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
  // RSS文章相关方法
  async function createRSSConversation(article: any, model: string) {
    const metadata = {
      source: 'rss',
      title: article.title,
      article_id: article.id,
      article_title: article.title,
      feed_id: article.subscription_id
    }
    
    const conversation = await createConversation(model, metadata)
    if (conversation) {
      // 自动发送system message加载文章内容
      const systemContent = buildArticleContext(article)
      const systemMessage: Message = {
        role: 'system',
        content: systemContent,
        timestamp: new Date().toISOString()
      }
      conversation.messages.push(systemMessage)
      await saveConversation(conversation)
    }
    return conversation
  }

  function buildArticleContext(article: any): string {
    const content = article.content?.slice(0, 3000) || ''
    return `你正在阅读一篇RSS文章。请基于以下内容回答用户问题。\n\n文章标题: ${article.title}\n文章来源: ${article.feed_name || '未知'}\n发布时间: ${article.published_at || '未知'}\n\n文章内容:\n${content}`
  }

  async function executeQuickAction(action: 'summarize' | 'translate' | 'keypoints', article: any) {
    const prompts = {
      summarize: '请用中文总结这篇文章的主要内容，不超过200字。',
      translate: '请将这篇文章翻译成英文，保留原文格式和段落结构。',
      keypoints: '请提取这篇文章的3-5个关键要点，用bullet points形式列出。'
    }
    
    // 确保有当前对话
    if (!currentConversation.value) {
      const model = article.virtual_model || 'demo1'
      await createRSSConversation(article, model)
    }
    
    if (currentConversation.value) {
      // 发送快捷操作消息
      const model = currentConversation.value.model
      await sendMessage(prompts[action], model)
    }
  }

  function getConversationByArticleId(articleId: string): Conversation | undefined {
    return conversations.value.find(
      c => c.metadata?.source === 'rss' && c.metadata?.article_id === articleId
    )
  }

  return {
    conversations,
    currentConversation,
    isStreaming,
    settings,
    fetchConversations,
    createConversation,
    createRSSConversation,     // 新增
    executeQuickAction,        // 新增
    getConversationByArticleId, // 新增
    setCurrentConversation,
    sendMessage,
    saveConversation,
    stopStreaming,
    updateSettings,
    clearCurrentConversation
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
    saveConversation,
    stopStreaming,
    updateSettings,
    clearCurrentConversation
  }
})
