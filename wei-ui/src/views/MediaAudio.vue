<template>
  <div class="media-sub-container">
    <!-- 搜索和筛选 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索音频..."
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
        v-for="audio in filteredAudios"
        :key="audio.id"
        class="media-item"
        shadow="hover"
      >
        <div class="audio-cover" @click="playAudio(audio)">
          <div class="audio-icon">
            <el-icon :size="50" color="#67C23A"><Headset /></el-icon>
          </div>
          <div class="audio-duration">{{ formatDuration(audio.duration) }}</div>
          <div class="play-overlay">
            <el-icon :size="40"><VideoPlay /></el-icon>
          </div>
        </div>
        <div class="media-info">
          <h4 class="media-title" :title="audio.title">{{ audio.title }}</h4>
          <div class="media-meta">
            <span>{{ formatSize(audio.size) }}</span>
            <el-tag size="small" :type="getStatusType(audio.status)">
              {{ getStatusText(audio.status) }}
            </el-tag>
          </div>
          <div class="media-actions">
            <el-button type="primary" link @click="viewDetails(audio)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button type="danger" link @click="deleteAudio(audio)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 列表视图 -->
    <el-table v-else :data="filteredAudios" stripe border>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="artist" label="艺术家" width="150" />
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
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="playAudio(row)">播放</el-button>
          <el-button type="danger" link @click="deleteAudio(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="音频详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ selectedAudio?.title }}</el-descriptions-item>
        <el-descriptions-item label="艺术家">{{ selectedAudio?.artist || '-' }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ selectedAudio?.filename }}</el-descriptions-item>
        <el-descriptions-item label="专辑">{{ selectedAudio?.album || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时长">{{ formatDuration(selectedAudio?.duration) }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatSize(selectedAudio?.size) }}</el-descriptions-item>
        <el-descriptions-item label="比特率">{{ selectedAudio?.bitrate || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedAudio?.status)">
            {{ getStatusText(selectedAudio?.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 播放器 -->
      <div class="audio-player">
        <audio controls style="width: 100%">
          <source :src="selectedAudio?.url" />
        </audio>
      </div>

      <!-- 转录文本 -->
      <div v-if="selectedAudio?.transcript" class="transcript-section">
        <h4>转录文本</h4>
        <el-input
          v-model="selectedAudio.transcript"
          type="textarea"
          :rows="8"
          readonly
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { Search, VideoPlay, View, Delete, Headset } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Audio {
  id: string
  title: string
  filename: string
  artist?: string
  album?: string
  duration: number
  size: number
  bitrate?: string
  url?: string
  status: 'pending' | 'processing' | 'processed' | 'error'
  transcript?: string
  created_at: string
}

const viewMode = inject('viewMode', ref('grid'))
const searchKeyword = ref('')
const filterStatus = ref('')
const detailVisible = ref(false)
const selectedAudio = ref<Audio | null>(null)

const audios = ref<Audio[]>([
  {
    id: '1',
    title: 'Podcast Episode 1',
    filename: 'podcast-01.mp3',
    artist: 'Tech Talk',
    duration: 3600,
    size: 45678901,
    bitrate: '128 kbps',
    status: 'processed',
    transcript: '这是音频的转录文本...',
    created_at: new Date().toISOString()
  },
  {
    id: '2',
    title: '会议录音',
    filename: 'meeting-2024-01.wav',
    duration: 5400,
    size: 123456789,
    bitrate: '256 kbps',
    status: 'processing',
    created_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    id: '3',
    title: '音乐专辑 - Track 1',
    filename: 'album-track-01.flac',
    artist: 'Unknown Artist',
    album: 'Best Collection',
    duration: 245,
    size: 23456789,
    bitrate: 'Lossless',
    status: 'pending',
    created_at: new Date(Date.now() - 172800000).toISOString()
  }
])

const filteredAudios = computed(() => {
  let result = audios.value
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(a => 
      a.title.toLowerCase().includes(keyword) ||
      (a.artist && a.artist.toLowerCase().includes(keyword))
    )
  }
  
  if (filterStatus.value) {
    result = result.filter(a => a.status === filterStatus.value)
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

const playAudio = (audio: Audio) => {
  ElMessage.info(`播放音频: ${audio.title}`)
}

const viewDetails = (audio: Audio) => {
  selectedAudio.value = audio
  detailVisible.value = true
}

const deleteAudio = async (audio: Audio) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${audio.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    audios.value = audios.value.filter(a => a.id !== audio.id)
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

.audio-cover {
  position: relative;
  aspect-ratio: 1;
  cursor: pointer;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  display: flex;
  align-items: center;
  justify-content: center;

  .audio-icon {
    opacity: 0.7;
  }

  .audio-duration {
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
    background: rgba(0, 0, 0, 0.4);
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

.audio-player {
  margin-top: 20px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.transcript-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: var(--el-text-color-primary);
  }
}
</style>