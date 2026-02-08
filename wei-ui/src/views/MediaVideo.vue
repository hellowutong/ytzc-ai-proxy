<template>
  <div class="media-sub-container">
    <!-- 搜索和筛选 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索视频..."
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="已处理" value="processed" />
        <el-option label="处理中" value="processing" />
        <el-option label="待处理" value="pending" />
      </el-select>
    </div>

    <!-- 网格视图 -->
    <div v-if="viewMode === 'grid'" class="media-grid">
      <el-card
        v-for="video in filteredVideos"
        :key="video.id"
        class="media-item"
        shadow="hover"
      >
        <div class="video-thumbnail" @click="playVideo(video)">
          <el-image :src="video.thumbnail || '/default-video-thumb.jpg'" fit="cover">
            <template #error>
              <div class="image-placeholder">
                <el-icon :size="40"><VideoPlay /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="video-duration">{{ formatDuration(video.duration) }}</div>
          <div class="play-overlay">
            <el-icon :size="50"><VideoPlay /></el-icon>
          </div>
        </div>
        <div class="media-info">
          <h4 class="media-title" :title="video.title">{{ video.title }}</h4>
          <div class="media-meta">
            <span>{{ formatSize(video.size) }}</span>
            <el-tag size="small" :type="getStatusType(video.status)">
              {{ getStatusText(video.status) }}
            </el-tag>
          </div>
          <div class="media-actions">
            <el-button type="primary" link @click="viewDetails(video)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button type="danger" link @click="deleteVideo(video)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 列表视图 -->
    <el-table v-else :data="filteredVideos" stripe border>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="duration" label="时长" width="120">
        <template #default="{ row }">
          {{ formatDuration(row.duration) }}
        </template>
      </el-table-column>
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">
          {{ formatSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="playVideo(row)">播放</el-button>
          <el-button type="danger" link @click="deleteVideo(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="视频详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ selectedVideo?.title }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ selectedVideo?.filename }}</el-descriptions-item>
        <el-descriptions-item label="时长">{{ formatDuration(selectedVideo?.duration) }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatSize(selectedVideo?.size) }}</el-descriptions-item>
        <el-descriptions-item label="分辨率">{{ selectedVideo?.resolution || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="编码格式">{{ selectedVideo?.codec || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedVideo?.status)">
            {{ getStatusText(selectedVideo?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="上传时间">{{ formatTime(selectedVideo?.created_at) }}</el-descriptions-item>
      </el-descriptions>
      
      <!-- 处理进度 -->
      <div v-if="selectedVideo?.status === 'processing'" class="processing-info">
        <h4>处理进度</h4>
        <el-progress :percentage="selectedVideo.progress || 0" />
      </div>

      <!-- 转录文本 -->
      <div v-if="selectedVideo?.transcript" class="transcript-section">
        <h4>转录文本</h4>
        <el-input
          v-model="selectedVideo.transcript"
          type="textarea"
          :rows="10"
          readonly
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { Search, VideoPlay, View, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Video {
  id: string
  title: string
  filename: string
  duration: number
  size: number
  resolution?: string
  codec?: string
  thumbnail?: string
  status: 'pending' | 'processing' | 'processed' | 'error'
  progress?: number
  transcript?: string
  created_at: string
}

const viewMode = inject('viewMode', ref('grid'))
const searchKeyword = ref('')
const filterStatus = ref('')
const detailVisible = ref(false)
const selectedVideo = ref<Video | null>(null)

const videos = ref<Video[]>([
  {
    id: '1',
    title: 'Vue3 教程第1集',
    filename: 'vue3-tutorial-01.mp4',
    duration: 1845,
    size: 156789012,
    resolution: '1920x1080',
    codec: 'H.264',
    status: 'processed',
    transcript: '这是视频的转录文本内容...',
    created_at: new Date().toISOString()
  },
  {
    id: '2',
    title: 'FastAPI 入门',
    filename: 'fastapi-intro.mp4',
    duration: 3600,
    size: 234567890,
    status: 'processing',
    progress: 65,
    created_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '3',
    title: 'Python 高级特性',
    filename: 'python-advanced.mp4',
    duration: 2700,
    size: 198765432,
    status: 'pending',
    created_at: new Date(Date.now() - 172800000).toISOString()
  }
])

const filteredVideos = computed(() => {
  let result = videos.value
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(v => v.title.toLowerCase().includes(keyword))
  }
  
  if (filterStatus.value) {
    result = result.filter(v => v.status === filterStatus.value)
  }
  
  return result
})

const formatDuration = (seconds: number | undefined): string => {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatSize = (bytes: number | undefined): string => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
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

const getStatusType = (status: string | undefined): string => {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'processed': 'success',
    'error': 'danger'
  }
  return typeMap[status || 'pending'] || 'info'
}

const getStatusText = (status: string | undefined): string => {
  const textMap: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'processed': '已处理',
    'error': '错误'
  }
  return textMap[status || 'pending'] || '未知'
}

const playVideo = (video: Video) => {
  ElMessage.info(`播放视频: ${video.title}`)
}

const viewDetails = (video: Video) => {
  selectedVideo.value = video
  detailVisible.value = true
}

const deleteVideo = async (video: Video) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${video.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    videos.value = videos.value.filter(v => v.id !== video.id)
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
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.media-item {
  :deep(.el-card__body) {
    padding: 0;
  }
}

.video-thumbnail {
  position: relative;
  aspect-ratio: 16/9;
  cursor: pointer;
  overflow: hidden;

  .el-image {
    width: 100%;
    height: 100%;
  }

  .image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--el-fill-color);
  }

  .video-duration {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
  }

  .play-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s;

    .el-icon {
      color: white;
    }
  }

  &:hover .play-overlay {
    opacity: 1;
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

.processing-info,
.transcript-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: var(--el-text-color-primary);
  }
}
</style>