<template>
  <div class="media-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>媒体管理</span>
          <div class="header-actions">
            <el-radio-group v-model="viewMode">
              <el-radio-button label="grid">
                <el-icon><Grid /></el-icon>
              </el-radio-button>
              <el-radio-button label="list">
                <el-icon><List /></el-icon>
              </el-radio-button>
            </el-radio-group>
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
            <el-button @click="showUrlDialog = true">
              <el-icon><Link /></el-icon>
              URL下载
            </el-button>
          </div>
        </div>
      </template>

      <!-- Statistics -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#409EFF"><Files /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.total_files || 0 }}</div>
                <div class="stat-label">总文件</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#67C23A"><VideoPlay /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.by_type?.video || 0 }}</div>
                <div class="stat-label">视频</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#E6A23C"><Headset /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.by_type?.audio || 0 }}</div>
                <div class="stat-label">音频</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#909399"><Document /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.by_type?.text || 0 }}</div>
                <div class="stat-label">文本</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#67C23A"><CircleCheck /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.transcribed_count || 0 }}</div>
                <div class="stat-label">已转录</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-item">
              <el-icon class="stat-icon" :size="32" color="#F56C6C"><CircleClose /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ stats?.failed_count || 0 }}</div>
                <div class="stat-label">失败</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Submenu -->
      <el-menu
        :default-active="activeMenu"
        class="media-menu"
        mode="horizontal"
        @select="handleMenuSelect"
      >
        <el-menu-item index="video">
          <el-icon><VideoPlay /></el-icon>
          <span>视频</span>
        </el-menu-item>
        <el-menu-item index="audio">
          <el-icon><Headset /></el-icon>
          <span>音频</span>
        </el-menu-item>
        <el-menu-item index="text">
          <el-icon><Document /></el-icon>
          <span>文本&图片</span>
        </el-menu-item>
      </el-menu>

      <!-- Content Area - Router View -->
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </el-card>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="uploadVisible"
      title="上传媒体文件"
      width="600px"
      destroy-on-close
    >
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".mp4,.avi,.mov,.mkv,.mp3,.wav,.ogg,.txt,.pdf,.doc,.docx,.jpg,.jpeg,.png"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持视频(mp4, avi, mov)、音频(mp3, wav, ogg)、文本(txt, pdf, doc)、图片(jpg, png)格式
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="留空使用文件名" />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="uploadForm.tags"
            multiple
            filterable
            allow-create
            placeholder="添加标签"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="自动转录">
          <el-switch v-model="uploadForm.auto_transcribe" active-text="上传后自动转录(仅音视频)" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :loading="uploading">
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <!-- URL Download Dialog -->
    <el-dialog
      v-model="urlVisible"
      title="从URL下载"
      width="600px"
      destroy-on-close
    >
      <el-form :model="urlForm" label-width="100px">
        <el-form-item label="URL">
          <el-input
            v-model="urlForm.url"
            placeholder="https://example.com/video.mp4"
          />
        </el-form-item>

        <el-form-item label="类型">
          <el-radio-group v-model="urlForm.media_type">
            <el-radio-button label="video">视频</el-radio-button>
            <el-radio-button label="audio">音频</el-radio-button>
            <el-radio-button label="text">文本/图片</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="标题">
          <el-input v-model="urlForm.title" placeholder="留空使用URL文件名" />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="urlForm.tags"
            multiple
            filterable
            allow-create
            placeholder="添加标签"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="自动转录">
          <el-switch v-model="urlForm.auto_transcribe" active-text="下载后自动转录(仅音视频)" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="urlVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUrlDownload" :loading="downloading">
          开始下载
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Upload,
  Grid,
  List,
  VideoPlay,
  Headset,
  Document,
  Link,
  Files,
  CircleCheck,
  CircleClose,
  UploadFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import {
  uploadMediaFile,
  downloadFromUrl,
  getMediaStats,
  type MediaStats,
  type MediaType,
} from '@/api/media'

const router = useRouter()
const route = useRoute()

const viewMode = ref('list')
const activeMenu = ref('video')
const uploadVisible = ref(false)
const urlVisible = ref(false)
const uploading = ref(false)
const downloading = ref(false)
const stats = ref<MediaStats | null>(null)

const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const uploadForm = ref({
  title: '',
  tags: [] as string[],
  auto_transcribe: true,
})

const urlForm = ref({
  url: '',
  media_type: 'video' as MediaType,
  title: '',
  tags: [] as string[],
  auto_transcribe: true,
})

const fetchStats = async () => {
  try {
    stats.value = await getMediaStats()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
  router.push(`/media/${index}`)
}

const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file.raw || null
}

const confirmUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    const res = await uploadMediaFile(
      selectedFile.value,
      undefined, // Auto-detect type
      uploadForm.value.title || undefined,
      uploadForm.value.tags,
      uploadForm.value.auto_transcribe
    )
    ElMessage.success(`上传成功: ${res.file_name}`)
    uploadVisible.value = false
    fetchStats()
    
    // Reset form
    selectedFile.value = null
    uploadForm.value = { title: '', tags: [], auto_transcribe: true }
    uploadRef.value?.clearFiles()
    
    // Refresh current view
    window.dispatchEvent(new CustomEvent('media-updated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const confirmUrlDownload = async () => {
  if (!urlForm.value.url) {
    ElMessage.warning('请输入URL')
    return
  }

  downloading.value = true
  try {
    await downloadFromUrl({
      url: urlForm.value.url,
      media_type: urlForm.value.media_type,
      title: urlForm.value.title || undefined,
      tags: urlForm.value.tags,
      auto_transcribe: urlForm.value.auto_transcribe,
    })
    ElMessage.success('下载任务已启动')
    urlVisible.value = false
    fetchStats()
    
    // Reset form
    urlForm.value = {
      url: '',
      media_type: 'video',
      title: '',
      tags: [],
      auto_transcribe: true,
    }
    
    // Refresh current view
    window.dispatchEvent(new CustomEvent('media-updated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '下载失败')
  } finally {
    downloading.value = false
  }
}

const showUploadDialog = () => {
  uploadVisible.value = true
}

const showUrlDialog = () => {
  urlVisible.value = true
}

onMounted(() => {
  // Set active menu based on current route
  const path = route.path
  if (path.includes('/media/video')) {
    activeMenu.value = 'video'
  } else if (path.includes('/media/audio')) {
    activeMenu.value = 'audio'
  } else if (path.includes('/media/text')) {
    activeMenu.value = 'text'
  }
  
  fetchStats()
})
</script>

<style scoped lang="scss">
.media-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-actions {
    display: flex;
    gap: 10px;
    align-items: center;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  :deep(.el-card__body) {
    padding: 15px;
  }
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;

  .stat-info {
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: var(--el-text-color-primary);
    }

    .stat-label {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin-top: 2px;
    }
  }
}

.media-menu {
  margin-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}
</style>
