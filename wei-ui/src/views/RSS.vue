<template>
  <div class="rss-management">
    <!-- Statistics Cards -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="4" v-for="stat in displayStats" :key="stat.key">
        <el-card class="stat-card" :body-style="{ padding: '12px' }">
          <div class="stat-content">
            <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Toolbar -->
    <el-card class="toolbar-card" :body-style="{ padding: '16px' }">
      <el-row :gutter="16" align="middle">
        <el-col :span="4">
          <el-select v-model="filter.project_name" placeholder="全部订阅" clearable @change="handleFilterChange">
            <el-option
              v-for="project in projects"
              :key="project.name"
              :label="project.name"
              :value="project.name"
            />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select v-model="filter.status" placeholder="状态" clearable @change="handleFilterChange">
            <el-option label="未读" value="unread" />
            <el-option label="阅读中" value="reading" />
            <el-option label="已读" value="read" />
            <el-option label="已提取" value="extracted" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select v-model="filter.is_permanent" placeholder="存储类型" clearable @change="handleFilterChange">
            <el-option label="长期记忆" :value="true" />
            <el-option label="临时" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select v-model="filter.extracted" placeholder="提取状态" clearable @change="handleFilterChange">
            <el-option label="已提取" :value="true" />
            <el-option label="未提取" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="filter.search"
            placeholder="搜索标题/内容..."
            clearable
            @keyup.enter="handleFilterChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="5" style="text-align: right;">
          <el-button type="primary" @click="handleFetch" :loading="fetching">
            <el-icon><Refresh /></el-icon>刷新订阅
          </el-button>
          <el-button @click="showBatchDialog" :disabled="selectedItems.length === 0">
            <el-icon><FolderChecked /></el-icon>批量操作
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- RSS Items Table -->
    <el-card class="items-card">
      <el-table
        :data="items"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="_id"
      >
        <el-table-column type="selection" width="40" />
        
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="存储" width="70">
          <template #default="{ row }">
            <el-tooltip :content="row.is_permanent ? '长期记忆' : '临时'">
              <el-icon :size="16" :color="row.is_permanent ? '#67C23A' : '#909399'">
                <Star v-if="row.is_permanent" />
                <Timer v-else />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column label="标题" min-width="300">
          <template #default="{ row }">
            <div class="item-title" @click="handleViewDetail(row)">
              <el-link type="primary" :underline="false">
                {{ row.title }}
              </el-link>
              <el-tag v-if="row.extracted" type="success" size="small" effect="plain" class="extracted-tag">
                已提取
              </el-tag>
            </div>
            <div class="item-meta">
              <span class="project-name">{{ row.project_name }}</span>
              <span v-if="row.author">· {{ row.author }}</span>
              <span v-if="row.word_count">· {{ row.word_count }}字</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="获取时间" width="120">
          <template #default="{ row }">
            {{ formatRelativeTime(row.fetched_at) }}
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="120">
          <template #default="{ row }">
            {{ row.published_at ? formatRelativeTime(row.published_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                v-if="row.status === 'unread'"
                type="primary"
                size="small"
                @click="handleMarkRead(row)"
              >
                标为已读
              </el-button>
              <el-button
                v-if="!row.extracted"
                type="success"
                size="small"
                @click="handleExtract(row)"
                :loading="extractingId === row._id"
              >
                提取知识
              </el-button>
              <el-button size="small" @click="handleViewDetail(row)">
                详情
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialog.visible"
      :title="detailDialog.item?.title"
      width="800px"
      destroy-on-close
    >
      <div v-if="detailDialog.item" class="item-detail">
        <div class="detail-header">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="订阅源">{{ detailDialog.item.project_name }}</el-descriptions-item>
            <el-descriptions-item label="作者">{{ detailDialog.item.author || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(detailDialog.item.status)" size="small">
                {{ getStatusLabel(detailDialog.item.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="存储类型">
              {{ detailDialog.item.is_permanent ? '长期记忆' : '临时' }}
            </el-descriptions-item>
            <el-descriptions-item label="发布时间">
              {{ detailDialog.item.published_at ? new Date(detailDialog.item.published_at).toLocaleString() : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="获取时间">
              {{ new Date(detailDialog.item.fetched_at).toLocaleString() }}
            </el-descriptions-item>
            <el-descriptions-item label="阅读时长" v-if="detailDialog.item.read_duration">
              {{ formatDuration(detailDialog.item.read_duration) }}
            </el-descriptions-item>
            <el-descriptions-item label="字数" v-if="detailDialog.item.word_count">
              {{ detailDialog.item.word_count }}字
            </el-descriptions-item>
          </el-descriptions>
          
          <div class="detail-actions">
            <el-button
              v-if="detailDialog.item.status === 'unread'"
              type="primary"
              @click="handleMarkReadFromDetail"
            >
              标为已读
            </el-button>
            <el-button
              v-if="!detailDialog.item.extracted"
              type="success"
              @click="handleExtractFromDetail"
              :loading="extracting"
            >
              提取知识
            </el-button>
            <el-button @click="openOriginalLink">
              <el-icon><Link /></el-icon>原文链接
            </el-button>
          </div>
        </div>

        <el-divider />

        <div class="detail-content">
          <div v-if="detailDialog.item.content" class="content-text" v-html="detailDialog.item.content"></div>
          <div v-else-if="detailDialog.item.description" class="content-text">{{ detailDialog.item.description }}</div>
          <div v-else class="no-content">暂无内容</div>
        </div>

        <div v-if="detailDialog.item.tags?.length" class="detail-tags">
          <el-tag v-for="tag in detailDialog.item.tags" :key="tag" size="small" class="tag-item">
            {{ tag }}
          </el-tag>
        </div>
      </div>
    </el-dialog>

    <!-- Batch Operation Dialog -->
    <el-dialog v-model="batchDialog.visible" title="批量操作" width="400px">
      <div class="batch-content">
        <p>已选择 <strong>{{ selectedItems.length }}</strong> 篇文章</p>
        <el-radio-group v-model="batchDialog.operation">
          <el-radio label="read">标为已读</el-radio>
          <el-radio label="archive">归档</el-radio>
          <el-radio label="permanent">设为长期记忆</el-radio>
          <el-radio label="unpermanent">设为临时</el-radio>
          <el-radio label="delete" style="color: #F56C6C;">删除</el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <el-button @click="batchDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchExecute" :loading="batchDialog.loading">
          确认执行
        </el-button>
      </template>
    </el-dialog>

    <!-- Fetch Result Dialog -->
    <el-dialog v-model="fetchDialog.visible" title="订阅更新结果" width="500px">
      <div v-if="fetchDialog.result">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="总体状态">
            <el-tag :type="fetchDialog.result.success ? 'success' : 'warning'">
              {{ fetchDialog.result.success ? '成功' : '部分失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="新增文章">{{ fetchDialog.result.total_new }}</el-descriptions-item>
          <el-descriptions-item label="更新文章">{{ fetchDialog.result.total_updated }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ fetchDialog.result.duration_ms }}ms</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div class="fetch-results">
          <div v-for="result in fetchDialog.result.results" :key="result.project_name" class="fetch-result-item">
            <div class="result-header">
              <span class="project-name">{{ result.project_name }}</span>
              <el-tag :type="result.success ? 'success' : 'danger'" size="small">
                {{ result.success ? '成功' : '失败' }}
              </el-tag>
            </div>
            <div class="result-stats" v-if="result.success">
              <span>新增: {{ result.new_items }}</span>
              <span>更新: {{ result.updated_items }}</span>
            </div>
            <div class="result-error" v-if="result.error">
              <el-alert :title="result.error" type="error" :closable="false" />
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  FolderChecked,
  Star,
  Timer,
  Link
} from '@element-plus/icons-vue'
import {
  listRSSProjects,
  listRSSItems,
  getRSSItem,
  fetchRSSFeeds,
  markAsRead,
  extractToKnowledge,
  batchOperation,
  getRSSStats,
  getStatusType,
  getStatusLabel,
  formatDuration,
  formatRelativeTime,
  type RSSProject,
  type RSSItem,
  type RSSItemDetail,
  type RSSFetchResponse,
  type RSSStats
} from '../api/rss'

// State
const loading = ref(false)
const fetching = ref(false)
const extracting = ref(false)
const extractingId = ref<string | null>(null)
const projects = ref<RSSProject[]>([])
const items = ref<RSSItem[]>([])
const selectedItems = ref<RSSItem[]>([])
const stats = ref<RSSStats | null>(null)

// Filter
const filter = reactive({
  project_name: undefined as string | undefined,
  status: undefined as string | undefined,
  is_permanent: undefined as boolean | undefined,
  extracted: undefined as boolean | undefined,
  search: ''
})

// Pagination
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// Dialogs
const detailDialog = reactive({
  visible: false,
  item: null as RSSItemDetail | null
})

const batchDialog = reactive({
  visible: false,
  operation: 'read' as 'read' | 'archive' | 'delete' | 'permanent' | 'unpermanent',
  loading: false
})

const fetchDialog = reactive({
  visible: false,
  result: null as RSSFetchResponse | null
})

// Computed stats for display
const displayStats = computed(() => {
  if (!stats.value) return []
  
  return [
    { key: 'total', value: stats.value.total_items, label: '总文章', color: '#409EFF' },
    { key: 'unread', value: stats.value.unread_items, label: '未读', color: '#F56C6C' },
    { key: 'read', value: stats.value.read_items, label: '已读', color: '#67C23A' },
    { key: 'extracted', value: stats.value.extracted_items, label: '已提取', color: '#E6A23C' },
    { key: 'permanent', value: stats.value.permanent_items, label: '长期记忆', color: '#909399' },
    { key: 'today', value: stats.value.today_items, label: '今日新增', color: '#409EFF' }
  ]
})

// Methods
async function loadStats() {
  try {
    stats.value = await getRSSStats()
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadProjects() {
  try {
    projects.value = await listRSSProjects()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

async function loadItems() {
  loading.value = true
  try {
    const params = {
      project_name: filter.project_name,
      status: filter.status,
      is_permanent: filter.is_permanent,
      extracted: filter.extracted,
      search: filter.search || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    // Remove undefined values
    Object.keys(params).forEach(key => {
      if (params[key as keyof typeof params] === undefined) {
        delete (params as any)[key]
      }
    })
    
    items.value = await listRSSItems(params)
    // Note: The API doesn't return total count, so we'll estimate
    pagination.total = items.value.length === pagination.page_size 
      ? pagination.page * pagination.page_size + 1 
      : (pagination.page - 1) * pagination.page_size + items.value.length
  } catch (error) {
    ElMessage.error('加载文章列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  pagination.page = 1
  loadItems()
}

function handlePageChange(page: number) {
  pagination.page = page
  loadItems()
}

function handleSizeChange(size: number) {
  pagination.page_size = size
  pagination.page = 1
  loadItems()
}

function handleSelectionChange(selection: RSSItem[]) {
  selectedItems.value = selection
}

async function handleFetch() {
  fetching.value = true
  try {
    const result = await fetchRSSFeeds(filter.project_name)
    fetchDialog.result = result
    fetchDialog.visible = true
    
    ElMessage.success(`订阅更新完成：新增 ${result.total_new} 篇，更新 ${result.total_updated} 篇`)
    
    // Refresh data
    await loadStats()
    await loadItems()
  } catch (error) {
    ElMessage.error('订阅更新失败')
    console.error(error)
  } finally {
    fetching.value = false
  }
}

async function handleMarkRead(row: RSSItem) {
  try {
    await markAsRead(row._id)
    ElMessage.success('已标为已读')
    row.status = 'read'
    await loadStats()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

async function handleExtract(row: RSSItem) {
  extractingId.value = row._id
  try {
    const result = await extractToKnowledge(row._id)
    if (result.success) {
      ElMessage.success('知识提取成功')
      row.extracted = true
      row.extraction_doc_id = result.document_id || null
      await loadStats()
    } else {
      ElMessage.warning(result.message)
    }
  } catch (error) {
    ElMessage.error('知识提取失败')
    console.error(error)
  } finally {
    extractingId.value = null
  }
}

async function handleViewDetail(row: RSSItem) {
  try {
    const detail = await getRSSItem(row._id)
    detailDialog.item = detail
    detailDialog.visible = true
  } catch (error) {
    ElMessage.error('加载详情失败')
    console.error(error)
  }
}

async function handleMarkReadFromDetail() {
  if (!detailDialog.item) return
  
  try {
    await markAsRead(detailDialog.item._id)
    ElMessage.success('已标为已读')
    detailDialog.item.status = 'read'
    
    // Update item in list
    const item = items.value.find(i => i._id === detailDialog.item!._id)
    if (item) item.status = 'read'
    
    await loadStats()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

async function handleExtractFromDetail() {
  if (!detailDialog.item) return
  
  extracting.value = true
  try {
    const result = await extractToKnowledge(detailDialog.item._id)
    if (result.success) {
      ElMessage.success('知识提取成功')
      detailDialog.item.extracted = true
      detailDialog.item.extraction_doc_id = result.document_id || null
      
      // Update item in list
      const item = items.value.find(i => i._id === detailDialog.item!._id)
      if (item) {
        item.extracted = true
        item.extraction_doc_id = result.document_id || null
      }
      
      await loadStats()
    } else {
      ElMessage.warning(result.message)
    }
  } catch (error) {
    ElMessage.error('知识提取失败')
    console.error(error)
  } finally {
    extracting.value = false
  }
}

function openOriginalLink() {
  if (detailDialog.item?.link) {
    window.open(detailDialog.item.link, '_blank')
  }
}

function showBatchDialog() {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请先选择文章')
    return
  }
  batchDialog.operation = 'read'
  batchDialog.visible = true
}

async function handleBatchExecute() {
  if (batchDialog.operation === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedItems.value.length} 篇文章吗？`,
        '确认删除',
        { type: 'warning' }
      )
    } catch {
      return
    }
  }
  
  batchDialog.loading = true
  try {
    const result = await batchOperation(
      selectedItems.value.map(i => i._id),
      batchDialog.operation
    )
    
    if (result.success) {
      ElMessage.success(result.message)
      batchDialog.visible = false
      await loadItems()
      await loadStats()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('批量操作失败')
    console.error(error)
  } finally {
    batchDialog.loading = false
  }
}

// Lifecycle
onMounted(() => {
  loadStats()
  loadProjects()
  loadItems()
})
</script>

<style scoped>
.rss-management {
  padding: 16px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  padding: 8px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.toolbar-card {
  margin-bottom: 16px;
}

.items-card {
  min-height: 400px;
}

.item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.extracted-tag {
  flex-shrink: 0;
}

.item-meta {
  font-size: 12px;
  color: #909399;
}

.project-name {
  font-weight: 500;
  color: #409EFF;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* Detail Dialog */
.item-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-header {
  margin-bottom: 16px;
}

.detail-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.detail-content {
  line-height: 1.8;
  color: #303133;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.no-content {
  color: #909399;
  text-align: center;
  padding: 40px;
}

.detail-tags {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #EBEEF5;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 4px;
}

/* Batch Dialog */
.batch-content {
  padding: 16px 0;
}

.batch-content p {
  margin-bottom: 16px;
}

/* Fetch Dialog */
.fetch-results {
  max-height: 300px;
  overflow-y: auto;
}

.fetch-result-item {
  padding: 12px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  margin-bottom: 8px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.project-name {
  font-weight: 500;
}

.result-stats {
  font-size: 12px;
  color: #606266;
}

.result-stats span {
  margin-right: 16px;
}

.result-error {
  margin-top: 8px;
}
</style>
