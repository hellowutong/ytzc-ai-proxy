<template>
  <div class="media-type-view">
    <!-- Filters -->
    <div class="filter-row">
      <el-select 
        v-model="filterStatus" 
        placeholder="状态筛选" 
        clearable
        style="width: 150px;"
        @change="handleFilterChange"
      >
        <el-option
          v-for="status in statusOptions"
          :key="status.value"
          :label="status.label"
          :value="status.value"
        />
      </el-select>

      <el-input
        v-model="searchQuery"
        placeholder="搜索标题或文件名..."
        clearable
        style="width: 280px; margin-left: 15px;"
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-button @click="fetchData" style="margin-left: auto;">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <!-- Media Table -->
    <el-table
      :data="mediaFiles"
      v-loading="loading"
      stripe
      style="width: 100%"
      @row-click="handleRowClick"
    >
      <el-table-column type="index" width="50" />
      
      <el-table-column label="预览" width="100" align="center">
        <template #default="{ row }">
          <el-icon :size="28" color="#409EFF">
            <VideoPlay v-if="props.mediaType === 'video'" />
            <Microphone v-else-if="props.mediaType === 'audio'" />
            <Document v-else />
          </el-icon>
        </template>
      </el-table-column>

      <el-table-column label="标题" min-width="180">
        <template #default="{ row }">
          <div class="title-cell">
            <span class="title-text">{{ row.title }}</span>
            <div v-if="row.tags?.length" class="tags-row">
              <el-tag 
                v-for="tag in row.tags.slice(0, 3)" 
                :key="tag" 
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="文件名" prop="file_name" min-width="160" show-overflow-tooltip />

      <el-table-column label="大小" width="90">
        <template #default="{ row }">
          {{ formatFileSize(row.file_size) }}
        </template>
      </el-table-column>

      <el-table-column label="时长" width="90">
        <template #default="{ row }">
          {{ formatDuration(row.duration) }}
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="转录" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.transcription" type="success" size="small">
            {{ row.transcription.word_count }}字
          </el-tag>
          <el-tag v-else-if="canTranscribe(row)" type="info" size="small">未转录</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column label="来源" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.source_type === 'url' || row.source_type === 'download'" size="small" type="warning">URL</el-tag>
          <el-tag v-else size="small">上传</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="canTranscribe(row) && !row.transcription"
            type="primary"
            link
            size="small"
            @click.stop="startTranscription(row)"
          >
            转录
          </el-button>
          <el-button
            type="primary"
            link
            size="small"
            @click.stop="showDetail(row)"
          >
            详情
          </el-button>
          <el-button
            type="primary"
            link
            size="small"
            @click.stop="downloadFile(row)"
          >
            下载
          </el-button>
          <el-popconfirm
            title="确定删除该文件吗？"
            confirm-button-text="确定"
            cancel-button-text="取消"
            @confirm.stop="deleteFile(row)"
          >
            <template #reference>
              <el-button type="danger" link size="small" @click.stop>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      :title="detailMedia?.title || '媒体详情'"
      width="800px"
      destroy-on-close
    >
      <div v-if="detailMedia" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ detailMedia.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag>{{ detailMedia.media_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件名" :span="2">{{ detailMedia.file_name }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatFileSize(detailMedia.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ formatDuration(detailMedia.duration) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailMedia.status)">
              {{ getStatusLabel(detailMedia.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ detailMedia.source_type }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(detailMedia.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(detailMedia.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- Source URL -->
        <div v-if="detailMedia.source_url" class="detail-section">
          <h4>来源URL</h4>
          <el-input :model-value="detailMedia.source_url" readonly>
            <template #append>
              <el-button @click="copyUrl(detailMedia.source_url!)">复制</el-button>
            </template>
          </el-input>
        </div>

        <!-- Transcription Section -->
        <div v-if="detailMedia.transcription" class="detail-section">
          <h4>转录内容</h4>
          <el-descriptions :column="2" border size="small" class="mb-3">
            <el-descriptions-item label="语言">{{ detailMedia.transcription.language }}</el-descriptions-item>
            <el-descriptions-item label="字数">{{ detailMedia.transcription.word_count }}</el-descriptions-item>
            <el-descriptions-item label="置信度">
              {{ (detailMedia.transcription.confidence * 100).toFixed(1) }}%
            </el-descriptions-item>
            <el-descriptions-item label="耗时">
              {{ detailMedia.transcription.processing_time_ms }}ms
            </el-descriptions-item>
          </el-descriptions>

          <el-input
            type="textarea"
            :model-value="detailMedia.transcription.text"
            :rows="10"
            readonly
          />

          <!-- Segments -->
          <div v-if="detailMedia.transcription.segments?.length" class="segments-section">
            <h5>分段详情</h5>
            <el-timeline>
              <el-timeline-item
                v-for="(segment, idx) in detailMedia.transcription.segments"
                :key="idx"
                :timestamp="`${formatDuration(segment.start)} - ${formatDuration(segment.end)}`"
              >
                {{ segment.text }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="detailMedia.tags?.length" class="detail-section">
          <h4>标签</h4>
          <el-tag v-for="tag in detailMedia.tags" :key="tag" class="tag-item">{{ tag }}</el-tag>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button
          v-if="canTranscribe(detailMedia) && !detailMedia?.transcription"
          type="primary"
          @click="startTranscription(detailMedia!)"
        >
          开始转录
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { VideoPlay, Microphone, Document, Search, Refresh } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import {
  listMediaFiles,
  transcribeMedia,
  deleteMediaFile,
  getMediaFile,
  downloadMediaFile,
  formatFileSize,
  formatDuration,
  getStatusType,
  getStatusLabel,
  type MediaFile,
  type MediaType,
  type MediaStatus,
} from '@/api/media';

const props = defineProps<{
  mediaType: MediaType;
}>();

// State
const loading = ref(false);
const mediaFiles = ref<MediaFile[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const filterStatus = ref<MediaStatus | ''>('');
const searchQuery = ref('');

// Dialog
const showDetailDialog = ref(false);
const detailMedia = ref<MediaFile | null>(null);

// Options
const statusOptions = [
  { value: 'pending', label: '待处理' },
  { value: 'downloading', label: '下载中' },
  { value: 'uploaded', label: '已上传' },
  { value: 'transcribing', label: '转录中' },
  { value: 'transcribed', label: '已转录' },
  { value: 'processed', label: '已处理' },
  { value: 'failed', label: '失败' },
];

// Methods
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await listMediaFiles(
      props.mediaType,
      filterStatus.value || undefined,
      searchQuery.value || undefined,
      (currentPage.value - 1) * pageSize.value,
      pageSize.value
    );
    mediaFiles.value = res.media_files;
    total.value = res.total;
  } catch (error) {
    ElMessage.error('获取媒体列表失败');
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  currentPage.value = 1;
  fetchData();
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchData();
};

const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchData();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchData();
};

const handleRowClick = (row: MediaFile) => {
  showDetail(row);
};

const startTranscription = async (media: MediaFile) => {
  try {
    await transcribeMedia(media.id, { language: 'zh' });
    ElMessage.success('转录任务已启动');
    fetchData();
    if (showDetailDialog.value) {
      // Refresh detail
      const res = await getMediaFile(media.id);
      detailMedia.value = res;
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '转录启动失败');
  }
};

const showDetail = async (media: MediaFile) => {
  try {
    const res = await getMediaFile(media.id);
    detailMedia.value = res;
    showDetailDialog.value = true;
  } catch (error) {
    ElMessage.error('获取详情失败');
  }
};

const downloadFile = (media: MediaFile) => {
  const url = downloadMediaFile(media.id);
  window.open(url, '_blank');
};

const deleteFile = async (media: MediaFile) => {
  try {
    await deleteMediaFile(media.id);
    ElMessage.success('删除成功');
    fetchData();
  } catch (error) {
    ElMessage.error('删除失败');
  }
};

const canTranscribe = (media: MediaFile | null) => {
  if (!media) return false;
  return media.media_type === 'video' || media.media_type === 'audio';
};

const formatDate = (date: string) => {
  if (!date) return '-';
  return new Date(date).toLocaleString('zh-CN');
};

const copyUrl = (url: string) => {
  navigator.clipboard.writeText(url);
  ElMessage.success('已复制到剪贴板');
};

// Lifecycle
onMounted(() => {
  fetchData();
});
</script>

<style scoped lang="scss">
.media-type-view {
  .filter-row {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }

  .title-cell {
    .title-text {
      font-weight: 500;
      display: block;
      margin-bottom: 4px;
    }

    .tags-row {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }

    .tag-item {
      transform: scale(0.85);
      transform-origin: left;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .detail-content {
    .detail-section {
      margin-top: 20px;

      h4, h5 {
        margin-bottom: 10px;
        color: #303133;
        font-weight: 600;
      }

      h5 {
        font-size: 14px;
      }
    }

    .segments-section {
      margin-top: 20px;
      max-height: 300px;
      overflow-y: auto;
    }

    .tag-item {
      margin-right: 8px;
      margin-bottom: 8px;
    }
  }
}
</style>
