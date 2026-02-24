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
            :class="{ unread: !article.is_read, active: selectedArticle?.id === article.id }"
            @click="selectArticle(article)"
          >
            <h4 class="article-title">{{ article.title }}</h4>
            <div class="article-meta">
              <span class="source">📰 {{ getFeedName(article.subscription_id) }}</span>
              <span class="time">· {{ formatTime(article.published_at) }}</span>
            </div>
            <p class="article-summary">{{ getSummary(article) }}</p>
          </div>
          
          <el-empty v-if="filteredArticles.length === 0" description="暂无文章" />
        </div>
      </div>

      <!-- 右侧：文章阅读区 -->
      <div class="article-reader" v-if="selectedArticle">
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
      
      <div class="article-reader empty" v-else>
        <el-empty description="选择一篇文章开始阅读" />
      </div>
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
    
    <!-- 重命名弹窗 -->
    <RenameFeedDialog
      v-model="showRenameDialog"
      :feed="renameFeedData"
      @confirm="handleRenameConfirm"
    />
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Setting } from '@element-plus/icons-vue'
import { useRSSStore } from '@/stores'
import type { RSSFeed, RSSArticle } from '@/types'
import AddFeedDialog from '@/components/AddFeedDialog.vue'
import RSSConfigDialog from '@/components/RSSConfigDialog.vue'
import FeedContextMenu from '@/components/FeedContextMenu.vue'
import RenameFeedDialog from '@/components/RenameFeedDialog.vue'

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

// 右键菜单
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuFeed = ref<RSSFeed | null>(null)
// 重命名弹窗
const showRenameDialog = ref(false)
const renameFeedData = ref<RSSFeed | null>(null)

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
  const text = article.content.replace(/<[^>]+>/g, '')
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

// 右键菜单
const showFeedContextMenu = (e: MouseEvent, feed: RSSFeed) => {
  contextMenuFeed.value = feed
  contextMenuPosition.value = { x: e.clientX, y: e.clientY }
  contextMenuVisible.value = true
}

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

onMounted(() => {
  rssStore.fetchFeeds()
  loadArticles()
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
  padding: 16px;
  border-bottom: 1px solid #333;
  cursor: pointer;
  transition: background 0.2s ease;
  border-left: 3px solid transparent;
}

.article-card:hover {
  background: #252526;
}

.article-card.active {
  background: #252526;
  border-left-color: #007acc;
}

.article-card.unread {
  border-left-color: #007acc;
}

.article-card.unread .article-title {
  color: #ffffff;
}

.article-title {
  font-size: 14px;
  font-weight: 500;
  color: #858585;
  margin: 0 0 8px 0;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
</style>
