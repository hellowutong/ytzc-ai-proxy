<template>
  <div class="media-list">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Plus /></el-icon>上传{{ typeLabel }}
      </el-button>
      <el-button v-if="type !== 'text'" @click="showUrlDialog = true">
        <el-icon><Link /></el-icon>URL下载
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名"
        clearable
        style="width: 240px; margin-left: 12px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px; margin-left: 12px;">
        <el-option label="全部" value="all" />
        <el-option label="待处理" value="pending" />
        <el-option label="处理中" value="processing" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
    </div>

    <!-- Media Table -->
    <el-card class="table-card" v-loading="mediaStore.loading">
      <el-table :data="filteredFiles" style="width: 100%">
        <el-table-column prop="filename" label="文件名" width="500" />
        
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.progress" 
              :status="row.status === 'failed' ? 'exception' : undefined"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewFile(row)">查看</el-button>
            <el-button link type="primary" @click="reprocess(row)">重新处理</el-button>
            <el-button link type="danger" @click="deleteFile(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Upload Dialog -->
    <MediaUploadDialog
      v-model="showUploadDialog"
      :type="type"
      :processors="processors"
      :models="models"
      @upload="handleUpload"
    />

    <!-- URL Download Dialog -->
    <MediaUrlDialog
      v-model="showUrlDialog"
      :type="type"
      :processors="processors"
      :models="models"
      @download="handleUrlDownload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Link, Search } from '@element-plus/icons-vue'
import { useMediaStore } from '@/stores'
import type { MediaFile } from '@/types'
import MediaUploadDialog from './MediaUploadDialog.vue'
import MediaUrlDialog from './MediaUrlDialog.vue'

const props = defineProps<{
  type: 'video' | 'audio' | 'text'
  processors: string[]
  models: string[]
}>()

const mediaStore = useMediaStore()

const searchQuery = ref('')
const statusFilter = ref('all')
const showUploadDialog = ref(false)
const showUrlDialog = ref(false)

const typeLabel = computed(() => {
  const map = { video: '视频', audio: '音频', text: '文档' }
  return map[props.type]
})

const filteredFiles = computed(() => {
  let result = mediaStore.files.filter(f => f.type === props.type)
  
  if (searchQuery.value) {
    result = result.filter(f => 
      f.filename.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (statusFilter.value !== 'all') {
    result = result.filter(f => f.status === statusFilter.value)
  }
  
  return result
})

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const viewFile = (file: MediaFile) => {
  ElMessage.info(`查看: ${file.filename}`)
}

const reprocess = async (file: MediaFile) => {
  const success = await mediaStore.reprocessFile(file.id)
  if (success) {
    ElMessage.success('重新处理任务已提交')
  } else {
    ElMessage.error('操作失败')
  }
}

const deleteFile = async (file: MediaFile) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${file.filename}" 吗？`, '确认删除')
    const success = await mediaStore.deleteFile(file.id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // Cancelled
  }
}

const handleUpload = async (data: { file: File; config: any }) => {
  const success = await mediaStore.uploadFile(data.file, props.type, data.config)
  if (success) {
    ElMessage.success('上传成功')
    showUploadDialog.value = false
  } else {
    ElMessage.error('上传失败')
  }
}

const handleUrlDownload = async (data: { url: string; config: any }) => {
  const success = await mediaStore.downloadFromUrl(data.url, props.type, data.config)
  if (success) {
    ElMessage.success('下载任务已提交')
    showUrlDialog.value = false
  } else {
    ElMessage.error('下载失败')
  }
}

onMounted(() => {
  mediaStore.fetchFiles(props.type)
})
</script>

<style scoped>
.media-list {
  padding: 0;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.table-card {
  background: #252526;
  border: 1px solid #3C3C3C;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
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
