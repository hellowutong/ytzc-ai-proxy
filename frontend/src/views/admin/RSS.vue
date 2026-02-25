<template>
  <div class="rss-reader">
    <!-- 三栏布局 -->
    <div class="rss-layout">
      <!-- 左侧：订阅源列表 -->
      <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="sidebar-header">
          <span class="title">📡 全部订阅源</span>
        </div>
        
        <div class="feed-list">
          <div
            v-for="feed in feeds"
            :key="feed.id"
            class="feed-item"
            :class="{ 
              active: selectedFeed?.id === feed.id,
              unread: feed.unreadCount > 0 
            }"
            @click="selectFeed(feed)"
            @contextmenu.prevent="showFeedContextMenu($event, feed)"
          >
            <div class="feed-info">
              <span class="feed-name">{{ feed.name }}</span>
              <span class="feed-count" v-if="feed.unreadCount > 0">
                {{ feed.unreadCount }}篇未读
              </span>
              <span class="feed-count" v-else>已同步</span>
            </div>
          </div>
        </div>
        
        <div class="sidebar-footer">
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>添加订阅
          </el-button>
          <el-button size="small" @click="showConfigDialog = true">
            <el-icon><Setting /></el-icon>RSS配置
          </el-button>
        </div>
      </aside>

      <!-- 中间：文章列表 -->
      <div class="article-list">
        <div class="list-header">
          <el-input
            v-model="searchQuery"
            placeholder="搜索文章..."
            clearable
            size="small"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="filterStatus" size="small" class="filter-select">
            <el-option label="全部" value="all" />
            <el-option :label="`未读(${unreadCount})`" value="unread" />
            <el-option label="已读" value="read" />
          </el-select>
        </div>
        
        <!-- 批量操作工具栏 -->
        <div class="batch-toolbar">
          <el-checkbox 
            v-model="selectAllChecked" 
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
            size="small"
          >
            全选
          </el-checkbox>
          <el-button
            type="danger"
            size="small"
            :disabled="selectedArticles.size === 0"
            @click="batchDelete"
          >
            <el-icon><Delete /></el-icon>
            批量删除 ({{ selectedArticles.size }})
          </el-button>
        </div>
        
        <div class="list-tabs">
          <span 
            class="tab-item" 
            :class="{ active: filterStatus === 'all' }"
            @click="filterStatus = 'all'"
          >全部</span>
          <span 
            class="tab-item" 
            :class="{ active: filterStatus === 'unread' }"
            @click="filterStatus = 'unread'"
          >未读({{ unreadCount }})</span>
          <span 
            class="tab-item" 
            :class="{ active: filterStatus === 'read' }"
            @click="filterStatus = 'read'"
          >已读</span>
        </div>
        
        <div class="articles-container" v-loading="articlesLoading">
          <div
            v-for="article in filteredArticles"
            :key="article.id"
            class="article-card"
            :class="{ 
              unread: !article.is_read, 
              active: selectedArticle?.id === article.id,
              selected: selectedArticles.has(article.id)
            }"
            @click="selectArticle(article)"
            @contextmenu.prevent="showArticleContextMenu($event, article)"
          >
            <div class="article-checkbox" @click.stop>
              <el-checkbox
                :model-value="selectedArticles.has(article.id)"
                @change="(val: boolean) => toggleArticleSelection(article.id, val)"
                size="small"
              />
            </div>
            <div class="article-content">
              <div class="article-header">
                <span v-if="!article.is_read" class="unread-dot"></span>
                <h4 class="article-title">{{ article.title }}</h4>
              </div>
              <div class="article-meta">
                <span class="source">📰 {{ getFeedName(article.subscription_id) }}</span>
                <span class="time">· {{ formatTime(article.published_at) }}</span>
              </div>
              <p class="article-summary">{{ getSummary(article) }}</p>
            </div>
          </div>
          
          <el-empty v-if="filteredArticles.length === 0" description="暂无文章" />
        </div>
      </div>

      <!-- 右侧：文章阅读区/AI对话区 -->
      <div class="article-reader" v-if="selectedArticle">
        <!-- 标签栏 -->
        <div class="tab-bar">
          <div 
            class="tab-item" 
            :class="{ active: activeTab === 'article' }"
            @click="activeTab = 'article'"
          >
            📖 文章
          </div>
          <div 
            class="tab-item" 
            :class="{ active: activeTab === 'chat' }"
            @click="activeTab = 'chat'"
          >
            🤖 AI对话
          </div>
          <div class="tab-actions">
            <el-button v-if="activeTab === 'article'" size="small" @click="startAIChat">
              <el-icon><ChatDotRound /></el-icon>与AI对话
            </el-button>
          </div>
        </div>

        <!-- 文章内容 -->
        <div v-show="activeTab === 'article'" class="reader-content-wrapper">
          <div class="reader-header">
            <div class="feed-tag">📰 {{ getFeedName(selectedArticle.subscription_id) }}</div>
            <h2 class="reader-title">{{ selectedArticle.title }}</h2>
            <div class="reader-meta">
              <span>👤 {{ selectedArticle.author || '未知作者' }}</span>
              <span>·</span>
              <span>⏰ {{ formatFullTime(selectedArticle.published_at) }}</span>
            </div>
          </div>
          
          <div class="reader-content" v-html="selectedArticle.content"></div>
          
          <div class="reader-footer">
            <el-button @click="closeReader">❌ 关闭</el-button>
          </div>
        </div>

        <!-- AI对话区 -->
        <div v-show="activeTab === 'chat'" class="chat-area">
          <!-- 模型选择 -->
          <div class="chat-header">
            <div class="model-selector">
              <span>模型:</span>
              <el-select v-model="selectedModel" size="small" style="width: 150px;">
                <el-option
                  v-for="model in modelStore.enabledModels"
                  :key="model.name"
                  :label="model.name"
                  :value="model.name"
                />
              </el-select>
            </div>
            <div class="chat-actions">
              <el-button size="small" @click="chatStore.clearCurrentConversation()">清空对话</el-button>
            </div>
          </div>

          <!-- 上下文横幅 -->
          <div class="context-banner">
            <div class="context-title">📄 当前上下文: 《{{ selectedArticle.title }}》</div>
            <div class="context-meta">来源: {{ getFeedName(selectedArticle.subscription_id) }} | {{ formatFullTime(selectedArticle.published_at) }}</div>
          </div>

          <!-- 快捷操作 -->
          <div class="quick-actions">
            <el-button size="small" @click="handleQuickAction('summarize')" :loading="isLoadingChat">📋 总结</el-button>
            <el-button size="small" @click="handleQuickAction('translate')" :loading="isLoadingChat">🌐 翻译</el-button>
            <el-button size="small" @click="handleQuickAction('keypoints')" :loading="isLoadingChat">🎯 关键点</el-button>
          </div>

          <!-- 消息区域 -->
          <div class="messages-area" ref="messagesContainer">
            <div v-if="!currentArticleConversation?.messages?.length" class="empty-chat">
              <p>💬 点击下方快捷按钮或输入问题开始对话</p>
            </div>
            <template v-else>
              <div
                v-for="(msg, index) in currentArticleConversation.messages"
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

          <!-- 输入区域 -->
          <div class="input-area">
            <div class="input-wrapper">
              <el-input
                v-model="chatInput"
                type="textarea"
                :rows="2"
                placeholder="输入问题... (Enter发送, Shift+Enter换行)"
                @keydown.enter.exact.prevent="handleSendMessage"
                resize="none"
              />
              <div class="input-actions">
                <el-button
                  v-if="chatStore.isStreaming"
                  type="danger"
                  size="small"
                  @click="chatStore.stopStreaming"
                >
                  停止
                </el-button>
                <el-button
                  v-else
                  type="primary"
                  size="small"
                  :disabled="!chatInput.trim()"
                  @click="handleSendMessage"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="article-reader empty" v-else>
        <el-empty description="选择一篇文章开始阅读" />
      </div>

    <!-- 添加订阅弹窗 -->
    <AddFeedDialog
      v-model="showAddDialog"
      @submit="handleAddFeed"
    />
    
    <!-- RSS配置弹窗 -->
    <RSSConfigDialog
      v-model="showConfigDialog"
    />
    
    <!-- 订阅源右键菜单 -->
    <FeedContextMenu
      v-model="contextMenuVisible"
      :position="contextMenuPosition"
      :feed="contextMenuFeed"
      @rename="renameFeed"
      @delete="deleteFeed"
      @fetch="fetchNow"
    />
    
    <!-- 文章右键菜单 -->
    <ArticleContextMenu
      v-model="articleContextMenuVisible"
      :position="articleContextMenuPosition"
      :article="contextMenuArticle"
      @markRead="handleMarkRead"
      @markUnread="handleMarkUnread"
      @copyLink="copyArticleLink"
      @delete="deleteArticle"
    />
    
    <!-- 重命名弹窗 -->
    <RenameFeedDialog
      v-model="showRenameDialog"
      :feed="renameFeedData"
      @confirm="handleRenameConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Setting, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { useRSSStore, useChatStore, useModelStore } from '@/stores'
import type { RSSFeed, RSSArticle } from '@/types'
import AddFeedDialog from '@/components/AddFeedDialog.vue'
import RSSConfigDialog from '@/components/RSSConfigDialog.vue'
import FeedContextMenu from '@/components/FeedContextMenu.vue'
import RenameFeedDialog from '@/components/RenameFeedDialog.vue'
import ArticleContextMenu from '@/components/ArticleContextMenu.vue'

const rssStore = useRSSStore()
const chatStore = useChatStore()
const modelStore = useModelStore()
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Setting, Delete } from '@element-plus/icons-vue'
import { useRSSStore } from '@/stores'
import type { RSSFeed, RSSArticle } from '@/types'
import AddFeedDialog from '@/components/AddFeedDialog.vue'
import RSSConfigDialog from '@/components/RSSConfigDialog.vue'
import FeedContextMenu from '@/components/FeedContextMenu.vue'
import RenameFeedDialog from '@/components/RenameFeedDialog.vue'
import ArticleContextMenu from '@/components/ArticleContextMenu.vue'

const rssStore = useRSSStore()

// 布局
const sidebarWidth = ref(240)

// 状态
const searchQuery = ref('')
const filterStatus = ref<'all' | 'unread' | 'read'>('all')
const showAddDialog = ref(false)
const showConfigDialog = ref(false)
const selectedFeed = ref<RSSFeed | null>(null)
const selectedArticle = ref<RSSArticle | null>(null)
const articlesLoading = ref(false)

// 批量选择
const selectedArticles = ref<Set<string>>(new Set())

// 计算属性 - 是否全选
const selectAllChecked = computed({
  get: () => filteredArticles.value.length > 0 && filteredArticles.value.every(a => selectedArticles.value.has(a.id)),
  set: (val: boolean) => handleSelectAll(val)
})

// 计算属性 - 是否半选
const isIndeterminate = computed(() => {
  const selectedCount = filteredArticles.value.filter(a => selectedArticles.value.has(a.id)).length
  return selectedCount > 0 && selectedCount < filteredArticles.value.length
})

// 右键菜单 - 订阅源
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuFeed = ref<RSSFeed | null>(null)

// 右键菜单 - 文章
const articleContextMenuVisible = ref(false)
const articleContextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuArticle = ref<RSSArticle | null>(null)

// 重命名弹窗
const showRenameDialog = ref(false)
const renameFeedData = ref<RSSFeed | null>(null)

const chatInput = ref('')

// AI对话相关
const activeTab = ref<'article' | 'chat'>('article')
const selectedModel = ref('demo1')
const isLoadingChat = ref(false)

// 计算属性 - 当前文章的对话
const currentArticleConversation = computed(() => {
  if (!selectedArticle.value) return null
  return chatStore.getConversationByArticleId(selectedArticle.value.id)
})
// 计算属性
const feeds = computed(() => rssStore.feeds.map(f => ({
  ...f,
  unreadCount: rssStore.articles.filter(a => a.subscription_id === f.id && !a.is_read).length
})))

const unreadCount = computed(() => 
  rssStore.articles.filter(a => !a.is_read).length
)

const filteredArticles = computed(() => {
  let articles = rssStore.articles
  
  // 按订阅源筛选
  if (selectedFeed.value) {
    articles = articles.filter(a => a.subscription_id === selectedFeed.value?.id)
  }
  
  // 按已读状态筛选
  if (filterStatus.value === 'unread') {
    articles = articles.filter(a => !a.is_read)
  } else if (filterStatus.value === 'read') {
    articles = articles.filter(a => a.is_read)
  }
  
  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    articles = articles.filter(a => 
      a.title.toLowerCase().includes(query) ||
      (a.content && a.content.toLowerCase().includes(query))
    )
  }
  
  return articles.sort((a, b) => {
    const dateA = a.published_at ? new Date(a.published_at).getTime() : 0
    const dateB = b.published_at ? new Date(b.published_at).getTime() : 0
    return dateB - dateA
  })
})

// 方法
const selectFeed = (feed: RSSFeed) => {
  selectedFeed.value = feed
  selectedArticle.value = null
  selectedArticles.value.clear() // 清除选择
  loadArticles(feed.id)
}

const selectArticle = async (article: RSSArticle) => {
  // 获取完整文章内容
  const fullArticle = await rssStore.getArticle(article.id)
  if (fullArticle) {
    selectedArticle.value = fullArticle
  } else {
    selectedArticle.value = article
  }
  
  // 标记为已读
  if (!article.is_read) {
    await rssStore.markArticleRead(article.id, true)
    article.is_read = true
  }
}

const loadArticles = async (feedId?: string) => {
  articlesLoading.value = true
  await rssStore.fetchArticles(feedId)
  articlesLoading.value = false
}

const getFeedName = (feedId: string) => {
  const feed = rssStore.feeds.find(f => f.id === feedId)
  return feed?.name || '未知订阅'
}

const getSummary = (article: RSSArticle) => {
  if (!article.content) return ''
  // 去除HTML标签，取前100字符
  const text = article.content.replace(/<[^\u003e]+>/g, '')
  return text.slice(0, 100) + (text.length > 100 ? '...' : '')
}

const formatTime = (time?: string) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}

const formatFullTime = (time?: string) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const closeReader = () => {
  selectedArticle.value = null
}

// 批量选择相关
const toggleArticleSelection = (articleId: string, selected: boolean) => {
  if (selected) {
    selectedArticles.value.add(articleId)
  } else {
    selectedArticles.value.delete(articleId)
  }
}

const handleSelectAll = (val: boolean) => {
  if (val) {
    filteredArticles.value.forEach(article => {
      selectedArticles.value.add(article.id)
    })
  } else {
    selectedArticles.value.clear()
  }
}

// 右键菜单 - 订阅源
const showFeedContextMenu = (e: MouseEvent, feed: RSSFeed) => {
  contextMenuFeed.value = feed
  contextMenuPosition.value = { x: e.clientX, y: e.clientY }
  contextMenuVisible.value = true
}

// 右键菜单 - 文章
const showArticleContextMenu = (e: MouseEvent, article: RSSArticle) => {
  contextMenuArticle.value = article
  articleContextMenuPosition.value = { x: e.clientX, y: e.clientY }
  articleContextMenuVisible.value = true
}

// 文章右键菜单操作
const handleMarkRead = async (article: RSSArticle) => {
  if (!article.is_read) {
    const success = await rssStore.markArticleRead(article.id, true)
    if (success) {
      article.is_read = true
      ElMessage.success('已标记为已读')
    }
  }
}

const handleMarkUnread = async (article: RSSArticle) => {
  if (article.is_read) {
    const success = await rssStore.markArticleRead(article.id, false)
    if (success) {
      article.is_read = false
      ElMessage.success('已标记为未读')
    }
  }
}

const copyArticleLink = (article: RSSArticle) => {
  if (article.link) {
    navigator.clipboard.writeText(article.link).then(() => {
      ElMessage.success('链接已复制')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}

const deleteArticle = async (article: RSSArticle) => {
  try {
    await ElMessageBox.confirm(`确定要删除文章 "${article.title}" 吗？`, '确认删除')
    const success = await rssStore.deleteArticle(article.id)
    if (success) {
      ElMessage.success('删除成功')
      // 如果删除的是当前正在阅读的文章，清空阅读区
      if (selectedArticle.value?.id === article.id) {
        selectedArticle.value = null
      }
      // 从选中列表中移除
      selectedArticles.value.delete(article.id)
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 用户取消
  }
}

const batchDelete = async () => {
  const ids = Array.from(selectedArticles.value)
  if (ids.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${ids.length} 篇文章吗？`, '确认批量删除')
    const result = await rssStore.batchDeleteArticles(ids)
    if (result.success) {
      ElMessage.success(`成功删除 ${result.count} 篇文章`)
      selectedArticles.value.clear()
      // 如果删除的文章包含当前正在阅读的，清空阅读区
      if (selectedArticle.value && ids.includes(selectedArticle.value.id)) {
        selectedArticle.value = null
      }
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch {
    // 用户取消
  }
}

// 订阅源操作
const renameFeed = (feed: RSSFeed) => {
  renameFeedData.value = feed
  showRenameDialog.value = true
}

const deleteFeed = async (feed: RSSFeed) => {
  try {
    await ElMessageBox.confirm(`确定要删除订阅 "${feed.name}" 吗？`, '确认删除')
    const success = await rssStore.deleteFeed(feed.id)
    if (success) {
      ElMessage.success('删除成功')
      if (selectedFeed.value?.id === feed.id) {
        selectedFeed.value = null
        selectedArticle.value = null
      }
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // Cancelled
  }
}

const fetchNow = async (feed: RSSFeed) => {
  const success = await rssStore.fetchFeedNow(feed.id)
  if (success) {
    ElMessage.success('抓取任务已提交')
    // 刷新文章列表
    setTimeout(() => loadArticles(feed.id), 3000)
  } else {
    ElMessage.error('抓取失败')
  }
}

const handleAddFeed = async (feedData: { name: string; url: string }) => {
  const success = await rssStore.createFeed({
    ...feedData,
    enabled: true,
    update_interval: '30m',
    retention_days: 30,
    permanent: false,
    model: 'demo1'
  })
  
  if (success) {
    ElMessage.success('订阅创建成功')
    showAddDialog.value = false
  } else {
    ElMessage.error('创建失败')
  }
}

const handleRenameConfirm = async (feedId: string, newName: string) => {
  const success = await rssStore.updateFeed(feedId, { name: newName })
  if (success) {
    ElMessage.success('重命名成功')
    // 如果当前选中的订阅被重命名，更新显示
    if (selectedFeed.value?.id === feedId) {
      selectedFeed.value = { ...selectedFeed.value, name: newName }
    }
  } else {
    ElMessage.error('重命名失败')
  }
}

// AI对话相关方法
const startAIChat = async () => {
  if (!selectedArticle.value) return
  
  activeTab.value = 'chat'
  
  // 检查是否已有对话
  const existingConv = chatStore.getConversationByArticleId(selectedArticle.value.id)
  if (!existingConv) {
    isLoadingChat.value = true
    try {
      const model = selectedModel.value || selectedArticle.value.virtual_model || 'demo1'
      await chatStore.createRSSConversation(selectedArticle.value, model)
      ElMessage.success('AI对话已启动')
    } catch (error) {
      ElMessage.error('启动AI对话失败')
    } finally {
      isLoadingChat.value = false
    }
  }
}

const handleQuickAction = async (action: 'summarize' | 'translate' | 'keypoints') => {
  if (!selectedArticle.value) return
  
  activeTab.value = 'chat'
  isLoadingChat.value = true
  try {
    await chatStore.executeQuickAction(action, selectedArticle.value)
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    isLoadingChat.value = false
  }
}

const sendChatMessage = async (content: string) => {
  if (!content.trim() || !selectedArticle.value) return
  
  // 确保有对话
  if (!chatStore.currentConversation) {
    await startAIChat()
  }
  
  const model = chatStore.currentConversation?.model || selectedModel.value
  await chatStore.sendMessage(content, model)
  await chatStore.sendMessage(content, model)
}

const handleSendMessage = async () => {
  const content = chatInput.value
  if (!content.trim()) return
  
  chatInput.value = ''
  await sendChatMessage(content)
}

// 键盘快捷键
const handleKeyDown = (e: KeyboardEvent) => {
  // Delete键删除选中的文章
  if (e.key === 'Delete' && selectedArticles.value.size > 0) {
    batchDelete()
  }
  // Ctrl+A 全选
  if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault()
    handleSelectAll(true)
  }
  // Space 切换当前选中文章的选中状态
  if (e.key === ' ' && selectedArticle.value) {
    e.preventDefault()
    toggleArticleSelection(selectedArticle.value.id, !selectedArticles.value.has(selectedArticle.value.id))
  }
}

onMounted(() => {
  rssStore.fetchFeeds()
  loadArticles()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.rss-reader {
  height: 100%;
  background: #1e1e1e;
}

.rss-layout {
  display: flex;
  height: 100%;
}

/* 左侧边栏 */
.sidebar {
  background: #252526;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #333;
}

.sidebar-header .title {
  font-size: 18px;
  font-weight: bold;
  color: #cccccc;
}

.feed-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.feed-item {
  padding: 12px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.feed-item:hover {
  background: #2a2d2e;
}

.feed-item.active {
  background: #264f78;
  border-left-color: #007acc;
}

.feed-item.unread {
  border-left-color: #007acc;
}

.feed-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feed-name {
  font-size: 14px;
  color: #ffffff;
  font-weight: 500;
}

.feed-item:not(.unread) .feed-name {
  color: #858585;
}

.feed-count {
  font-size: 12px;
  color: #858585;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #333;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 中间文章列表 */
.article-list {
  width: 360px;
  background: #1e1e1e;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
}

.list-header {
  padding: 12px;
  border-bottom: 1px solid #333;
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.filter-select {
  width: 100px;
}

/* 批量操作工具栏 */
.batch-toolbar {
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #252526;
}

.list-tabs {
  display: flex;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  gap: 16px;
}

.tab-item {
  font-size: 13px;
  color: #858585;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
}

.tab-item:hover {
  color: #cccccc;
}

.tab-item.active {
  color: #007acc;
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  right: 0;
  height: 2px;
  background: #007acc;
}

.articles-container {
  flex: 1;
  overflow-y: auto;
}

.article-card {
  padding: 12px 16px;
  border-bottom: 1px solid #333;
  cursor: pointer;
  transition: background 0.2s ease;
  border-left: 3px solid transparent;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.article-card:hover {
  background: #252526;
}

.article-card.active {
  background: #252526;
  border-left-color: #007acc;
}

.article-card.selected {
  background: #1e3a5f;
}

.article-card.unread {
  border-left-color: #007acc;
}

.article-card.unread .article-title {
  color: #ffffff;
}

.article-checkbox {
  flex-shrink: 0;
  padding-top: 2px;
}

.article-content {
  flex: 1;
  min-width: 0;
}

.article-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: #007acc;
  border-radius: 50%;
  flex-shrink: 0;
}

.article-title {
  font-size: 14px;
  font-weight: 500;
  color: #858585;
  margin: 0;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.article-meta {
  font-size: 12px;
  color: #858585;
  margin-bottom: 8px;
  display: flex;
  gap: 4px;
}

.article-summary {
  font-size: 13px;
  color: #858585;
  line-height: 1.6;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 右侧阅读区 */
.article-reader {
  flex: 1;
  background: #1e1e1e;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.article-reader.empty {
  justify-content: center;
  align-items: center;
}

.reader-header {
  padding: 24px 40px;
  border-bottom: 1px solid #333;
}

.feed-tag {
  font-size: 14px;
  color: #858585;
  margin-bottom: 12px;
}

.reader-title {
  font-size: 24px;
  font-weight: bold;
  color: #cccccc;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.reader-meta {
  font-size: 13px;
  color: #858585;
  display: flex;
  gap: 8px;
}

.reader-content {
  flex: 1;
  padding: 24px 40px;
  overflow-y: auto;
  font-size: 15px;
  line-height: 1.8;
  color: #cccccc;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.reader-content :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}

.reader-content :deep(blockquote) {
  border-left: 4px solid #007acc;
  margin: 16px 0;
  padding: 12px 16px;
  background: #252526;
  border-radius: 0 4px 4px 0;
}

.reader-content :deep(code) {
  background: #252526;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.reader-content :deep(pre) {
  background: #252526;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
}

.reader-footer {
  padding: 12px 40px;
  border-top: 1px solid #333;
}

/* 深色主题输入框 */
:deep(.el-input__wrapper) {
  background: #3c3c3c !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: #cccccc !important;
}

:deep(.el-select .el-input__wrapper) {
  background: #3c3c3c !important;
}

/* 深色主题复选框 */
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #007acc;
  border-color: #007acc;
}

:deep(.el-checkbox__inner) {
  background-color: #3c3c3c;
  border-color: #555;
}

:deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  background-color: #007acc;
  border-color: #007acc;
}
/* AI对话区样式 */

.tab-bar {
  display: flex;
  border-bottom: 1px solid #333;
  background: #1e1e1e;
  padding: 0 16px;
}

.tab-item {
  padding: 12px 20px;
  cursor: pointer;
  color: #858585;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.tab-item:hover {
  color: #cccccc;
}

.tab-item.active {
  color: #007acc;
  border-bottom-color: #007acc;
}

.tab-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.reader-content-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(100% - 45px);
  overflow: hidden;
}

.chat-area {
  display: flex;
  flex-direction: column;
  height: calc(100% - 45px);
  background: #1e1e1e;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #333;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cccccc;
}

.context-banner {
  background: #252526;
  border-left: 3px solid #007acc;
  padding: 12px 16px;
  margin: 8px 16px;
  border-radius: 0 4px 4px 0;
}

.context-title {
  color: #cccccc;
  font-weight: 500;
  margin-bottom: 4px;
}

.context-meta {
  color: #858585;
  font-size: 12px;
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid #333;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-chat {
  text-align: center;
  color: #858585;
  padding: 40px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
}

.message.user .message-bubble {
  background: #264f78;
  color: #ffffff;
  border-radius: 8px 8px 0 8px;
}

.message.assistant .message-bubble {
  background: #252526;
  color: #cccccc;
  border-left: 3px solid #007acc;
  border-radius: 8px 8px 8px 0;
}

.message-time {
  font-size: 12px;
  color: #858585;
  margin-top: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #858585;
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
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.input-area {
  padding: 12px 16px;
  border-top: 1px solid #333;
  background: #252526;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-textarea__inner) {
  background: #3c3c3c !important;
  color: #cccccc !important;
  border: 1px solid #454545 !important;
}
</style>
