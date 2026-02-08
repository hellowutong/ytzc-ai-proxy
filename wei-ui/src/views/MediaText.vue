<template>
  <div class="media-sub-container">
    <!-- 搜索和筛选 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索文本/图片..."
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterType" placeholder="类型" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="文本" value="text" />
        <el-option label="图片" value="image" />
        <el-option label="Markdown" value="markdown" />
      </el-select>
    </div>

    <!-- 网格视图 -->
    <div v-if="viewMode === 'grid'" class="media-grid">
      <el-card
        v-for="item in filteredItems"
        :key="item.id"
        class="media-item"
        shadow="hover"
      >
        <div class="item-preview" @click="viewDetails(item)">
          <!-- 图片预览 -->
          <template v-if="item.type === 'image'">
            <el-image :src="item.url" fit="cover" class="image-preview">
              <template #error>
                <div class="image-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
          <!-- 文本预览 -->
          <template v-else>
            <div class="text-preview">
              <el-icon :size="40" color="#409EFF"><Document /></el-icon>
              <p class="preview-text">{{ item.content?.slice(0, 100) || '无内容' }}...</p>
            </div>
          </template>
        </div>
        <div class="media-info">
          <h4 class="media-title" :title="item.title">{{ item.title }}</h4>
          <div class="media-meta">
            <el-tag size="small" :type="getTypeColor(item.type)">
              {{ getTypeText(item.type) }}
            </el-tag>
            <span>{{ formatSize(item.size) }}</span>
          </div>
          <div class="media-actions">
            <el-button type="primary" link @click="viewDetails(item)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button type="danger" link @click="deleteItem(item)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 列表视图 -->
    <el-table v-else :data="filteredItems" stripe border>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.type)">{{ getTypeText(row.type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">
          {{ formatSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="viewDetails(row)">查看</el-button>
          <el-button type="danger" link @click="deleteItem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="详情" width="900px">
      <div v-if="selectedItem?.type === 'image'" class="image-detail">
        <el-image :src="selectedItem.url" fit="contain" style="max-height: 500px" />
        <el-descriptions :column="2" border class="detail-info">
          <el-descriptions-item label="标题">{{ selectedItem?.title }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ selectedItem?.filename }}</el-descriptions-item>
          <el-descriptions-item label="尺寸">{{ selectedItem?.dimensions || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatSize(selectedItem?.size) }}</el-descriptions-item>
          <el-descriptions-item label="格式">{{ selectedItem?.format?.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatTime(selectedItem?.created_at) }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else class="text-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{ selectedItem?.title }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ selectedItem?.filename }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ getTypeText(selectedItem?.type) }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatSize(selectedItem?.size) }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatTime(selectedItem?.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="content-section">
          <h4>内容</h4>
          <div v-if="selectedItem?.type === 'markdown'" class="markdown-content" v-html="renderMarkdown(selectedItem?.content)" />
          <pre v-else class="text-content">{{ selectedItem?.content }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { Search, View, Delete, Document, Picture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface TextMediaItem {
  id: string
  title: string
  filename: string
  type: 'text' | 'image' | 'markdown'
  content?: string
  url?: string
  size: number
  dimensions?: string
  format?: string
  created_at: string
}

const viewMode = inject('viewMode', ref('grid'))
const searchKeyword = ref('')
const filterType = ref('')
const detailVisible = ref(false)
const selectedItem = ref<TextMediaItem | null>(null)

const items = ref<TextMediaItem[]>([
  {
    id: '1',
    title: '项目文档',
    filename: 'project-doc.md',
    type: 'markdown',
    content: '# 项目文档\n\n## 概述\n\n这是一个AI网关项目...',
    size: 4523,
    created_at: new Date().toISOString()
  },
  {
    id: '2',
    title: '架构图',
    filename: 'architecture.png',
    type: 'image',
    url: 'https://placeholder.com/400x300',
    size: 123456,
    dimensions: '1920x1080',
    format: 'png',
    created_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '3',
    title: '配置说明',
    filename: 'config.txt',
    type: 'text',
    content: '配置说明文件内容...',
    size: 2048,
    created_at: new Date(Date.now() - 172800000).toISOString()
  },
  {
    id: '4',
    title: 'Screenshot',
    filename: 'screenshot.jpg',
    type: 'image',
    url: 'https://placeholder.com/400x300',
    size: 345678,
    dimensions: '2560x1440',
    format: 'jpg',
    created_at: new Date(Date.now() - 259200000).toISOString()
  }
])

const filteredItems = computed(() => {
  let result = items.value
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item => 
      item.title.toLowerCase().includes(keyword) ||
      (item.content && item.content.toLowerCase().includes(keyword))
    )
  }
  
  if (filterType.value) {
    result = result.filter(item => item.type === filterType.value)
  }
  
  return result
})

const getTypeColor = (type: string | undefined): string => {
  const colorMap: Record<string, string> = {
    'text': 'info',
    'image': 'success',
    'markdown': 'warning'
  }
  return colorMap[type || 'text'] || 'info'
}

const getTypeText = (type: string | undefined): string => {
  const textMap: Record<string, string> = {
    'text': '文本',
    'image': '图片',
    'markdown': 'Markdown'
  }
  return textMap[type || 'text'] || '未知'
}

const formatSize = (bytes: number | undefined): string => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(2)} ${units[i]}`
}

const formatTime = (timestamp: string | undefined): string => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const renderMarkdown = (content: string | undefined): string => {
  // 简化的Markdown渲染，实际项目中可以使用marked等库
  if (!content) return ''
  return content
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/\n/gim, '<br>')
}

const viewDetails = (item: TextMediaItem) => {
  selectedItem.value = item
  detailVisible.value = true
}

const deleteItem = async (item: TextMediaItem) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${item.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    items.value = items.value.filter(i => i.id !== item.id)
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}
</script>

<style scoped lang="scss">
.media-sub-container {
  padding: 20px 0;
}

.toolbar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.media-item {
  :deep(.el-card__body) {
    padding: 0;
  }
}

.item-preview {
  aspect-ratio: 4/3;
  cursor: pointer;
  overflow: hidden;
  background: var(--el-fill-color-light);

  .image-preview {
    width: 100%;
    height: 100%;
  }

  .image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .text-preview {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    text-align: center;

    .preview-text {
      margin-top: 10px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }
}

.media-info {
  padding: 15px;

  .media-title {
    margin: 0 0 10px 0;
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .media-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 10px;
  }

  .media-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

.image-detail {
  text-align: center;

  .el-image {
    margin-bottom: 20px;
  }

  .detail-info {
    text-align: left;
  }
}

.text-detail {
  .content-section {
    margin-top: 20px;

    h4 {
      margin-bottom: 10px;
      color: var(--el-text-color-primary);
    }

    .text-content {
      background: #f5f5f5;
      padding: 15px;
      border-radius: 4px;
      max-height: 400px;
      overflow-y: auto;
      white-space: pre-wrap;
    }

    .markdown-content {
      padding: 15px;
      background: var(--el-fill-color-light);
      border-radius: 4px;
      max-height: 400px;
      overflow-y: auto;

      :deep(h1) { font-size: 24px; margin: 16px 0; }
      :deep(h2) { font-size: 20px; margin: 14px 0; }
      :deep(h3) { font-size: 18px; margin: 12px 0; }
      :deep(strong) { font-weight: bold; }
      :deep(em) { font-style: italic; }
    }
  }
}
</style>