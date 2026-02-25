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
      const response = await fetch('/admin/ai/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, metadata })
      })
      
      const result = await response.json()
      if (result.code === 200) {
        const newConversation: Conversation = {
          id: result.data.id,
          model,
          messages: [],
          metadata: result.data.metadata,
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
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }

    currentConversation.value?.messages.push(userMessage)

    try {
      isStreaming.value = true

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
          max_tokens: settings.value.max_tokens
        })
      })

      const contentType = response.headers.get('content-type') || ''
      const isJsonResponse = contentType.includes('application/json')

      if (isJsonResponse) {
        const result = await response.json()
        
        if (result.error) {
          throw new Error(result.error.message || '请求失败')
        }

        const assistantMessage: Message = {
          role: 'assistant',
          content: result.choices?.[0]?.message?.content || '无响应内容',
          timestamp: new Date().toISOString()
        }

        currentConversation.value?.messages.push(assistantMessage)
        await saveConversation(currentConversation.value)
      } else {
        const errorText = await response.text()
        throw new Error(`服务器返回非JSON格式: ${errorText.substring(0, 100)}`)
      }
    } catch (error: any) {
      console.error('发送消息失败:', error)
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `抱歉，发生了错误: ${error.message || '未知错误'}`,
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
      
      if (!response.ok) {
        console.warn(`保存对话失败: ${response.status}`)
        return
      }
      
      const result = await response.json()
      if (result.code === 200) {
        console.log('对话保存成功')
        if (currentConversation.value) {
          currentConversation.value.updated_at = new Date().toISOString()
        }
      }
    } catch (error) {
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
    
    if (!currentConversation.value) {
      const model = article.virtual_model || 'demo1'
      await createRSSConversation(article, model)
    }
    
    if (currentConversation.value) {
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
    createRSSConversation,
    executeQuickAction,
    getConversationByArticleId,
    setCurrentConversation,
    sendMessage,
    saveConversation,
    stopStreaming,
    updateSettings,
    clearCurrentConversation
  }
})
