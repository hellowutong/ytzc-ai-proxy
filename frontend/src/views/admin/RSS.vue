<template>
  <div class="rss">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>添加订阅
      </el-button>
      <el-button @click="showImportDialog = true">
        <el-icon><Upload /></el-icon>批量导入
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索名称/URL"
        clearable
        style="width: 240px; margin-left: 12px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- Feeds Table -->
    <el-card class="table-card" v-loading="rssStore.loading">
      <el-table :data="filteredFeeds" style="width: 100%">
        <el-table-column prop="name" label="名称" width="180" />
        
        <el-table-column prop="url" label="URL" width="500">
          <template #default="{ row }">
            <el-link :href="row.url" target="_blank" type="primary">{{ row.url }}</el-link>
          </template>
        </el-table-column>

        <el-table-column prop="update_interval" label="更新频率" width="120" />

        <el-table-column prop="article_count" label="文章数" width="150" />

        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="(val: boolean) => updateFeed(row.id, { enabled: val })" />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="fetchNow(row)">立即抓取</el-button>
            <el-button link type="primary" @click="editFeed(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteFeed(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Articles Section -->
    <el-card class="articles-card" v-if="selectedFeed">
      <template #header>
        <div class="card-header">
          <span>文章列表 - {{ selectedFeed.name }}</span>
          <el-button link @click="selectedFeed = null">关闭</el-button>
        </div>
      </template>
      
      <el-table :data="rssStore.articles" style="width: 100%" v-loading="articlesLoading">
        <el-table-column prop="title" label="标题">
          <template #default="{ row }">
            <el-link @click="viewArticle(row)" type="primary">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="published_at" label="发布时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.published_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        
        <el-table-column prop="fetch_status" label="抓取状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.fetch_status)">{{ getStatusText(row.fetch_status) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="content_length" label="内容长度" width="100">
          <template #default="{ row }">
            {{ row.content_length }} 字符
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewArticle(row)">查看</el-button>
            <el-button link type="primary" :href="row.link" target="_blank">原文</el-button>
            <el-button link type="danger" @click="deleteArticle(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Dialog -->
    <RSSFeedDialog
      v-model="showAddDialog"
      :feed="editingFeed"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search } from '@element-plus/icons-vue'
import { useRSSStore } from '@/stores'
import type { RSSFeed, RSSArticle } from '@/types'
import RSSFeedDialog from '@/components/RSSFeedDialog.vue'

const rssStore = useRSSStore()

const searchQuery = ref('')
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const editingFeed = ref<RSSFeed | null>(null)
const selectedFeed = ref<RSSFeed | null>(null)
const articlesLoading = ref(false)

const filteredFeeds = computed(() => {
  if (!searchQuery.value) return rssStore.feeds
  return rssStore.feeds.filter(f => 
    f.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    f.url.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    full: 'success',
    summary: 'warning',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    full: '完整内容',
    summary: '仅摘要',
    failed: '抓取失败'
  }
  return map[status] || status
}

const updateFeed = async (id: string, data: Partial<RSSFeed>) => {
  const success = await rssStore.updateFeed(id, data)
  if (success) {
    ElMessage.success('更新成功')
  } else {
    ElMessage.error('更新失败')
  }
}

const fetchNow = async (feed: RSSFeed) => {
  const success = await rssStore.fetchFeedNow(feed.id)
  if (success) {
    ElMessage.success('抓取任务已提交')
  } else {
    ElMessage.error('抓取失败')
  }
}

const editFeed = (feed: RSSFeed) => {
  editingFeed.value = { ...feed }
  showAddDialog.value = true
}

const deleteFeed = async (feed: RSSFeed) => {
  try {
    await ElMessageBox.confirm(`确定要删除订阅 "${feed.name}" 吗？`, '确认删除')
    const success = await rssStore.deleteFeed(feed.id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // Cancelled
  }
}

const viewArticle = async (article: RSSArticle) => {
  ElMessage.info(`查看文章: ${article.title}`)
}

const deleteArticle = async (article: RSSArticle) => {
  // TODO: Implement article deletion
  ElMessage.info('删除文章功能开发中')
}

const handleSubmit = async (feedData: Omit<RSSFeed, 'id' | 'article_count'>) => {
  let success
  if (editingFeed.value) {
    success = await rssStore.updateFeed(editingFeed.value.id, feedData)
  } else {
    success = await rssStore.createFeed(feedData)
  }
  
  if (success) {
    ElMessage.success(editingFeed.value ? '更新成功' : '创建成功')
    showAddDialog.value = false
    editingFeed.value = null
  } else {
    ElMessage.error(editingFeed.value ? '更新失败' : '创建失败')
  }
}

onMounted(() => {
  rssStore.fetchFeeds()
})
</script>

<style scoped>
.rss {
  padding: 0;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.table-card,
.articles-card {
  background: #252526;
  border: 1px solid #3C3C3C;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
  color: #CCCCCC;
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
