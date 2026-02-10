<template>
  <div class="raw-data">
    <el-row :gutter="20">
      <!-- Navigation -->
      <el-col :span="4">
        <el-card class="nav-card">
          <template #header>
            <span>数据类型</span>
          </template>
          
          <el-menu
            :default-active="activeType"
            @select="handleSelect"
            class="data-menu"
          >
            <el-menu-item index="conversations">
              <el-icon><ChatDotRound /></el-icon>
              <span>对话数据</span>
            </el-menu-item>
            
            <el-menu-item index="media">
              <el-icon><VideoCamera /></el-icon>
              <span>媒体数据</span>
            </el-menu-item>
            
            <el-menu-item index="rss">
              <el-icon><Bell /></el-icon>
              <span>RSS数据</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- Data View -->
      <el-col :span="20">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span>{{ getTitle(activeType) }}</span>
              <el-button @click="refreshData">
                <el-icon><Refresh /></el-icon>刷新
              </el-button>
            </div>
          </template>
          
          <pre class="json-viewer">{{ formattedData }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChatDotRound, VideoCamera, Bell, Refresh } from '@element-plus/icons-vue'

const activeType = ref('conversations')
const rawData = ref<any>({})

const getTitle = (type: string) => {
  const titles: Record<string, string> = {
    conversations: '原始对话数据',
    media: '原始媒体数据',
    rss: '原始RSS数据'
  }
  return titles[type] || type
}

const formattedData = computed(() => {
  return JSON.stringify(rawData.value, null, 2)
})

const handleSelect = (index: string) => {
  activeType.value = index
  fetchData(index)
}

const fetchData = async (type: string) => {
  // Mock data - replace with actual API calls
  const mockData: Record<string, any> = {
    conversations: {
      total: 156,
      items: [
        { id: 'conv_001', model: 'demo1', message_count: 24 },
        { id: 'conv_002', model: 'demo2', message_count: 12 }
      ]
    },
    media: {
      total: 45,
      items: [
        { id: 'media_001', type: 'video', status: 'completed' },
        { id: 'media_002', type: 'audio', status: 'processing' }
      ]
    },
    rss: {
      total: 1234,
      items: [
        { id: 'article_001', feed: 'Tech News', title: 'AI News' },
        { id: 'article_002', feed: 'Science Daily', title: 'New Discovery' }
      ]
    }
  }
  
  rawData.value = mockData[type] || {}
}

const refreshData = () => {
  fetchData(activeType.value)
}

onMounted(() => {
  fetchData(activeType.value)
})
</script>

<style scoped>
.raw-data {
  padding: 0;
}

.nav-card,
.data-card {
  background: #252526;
  border: 1px solid #3C3C3C;
}

.data-menu {
  background: transparent;
  border-right: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.json-viewer {
  background: #1E1E1E;
  border: 1px solid #3C3C3C;
  border-radius: 4px;
  padding: 16px;
  margin: 0;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #CCCCCC;
  overflow-x: auto;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
  color: #CCCCCC;
}

:deep(.el-menu-item) {
  color: #858585;
}

:deep(.el-menu-item.is-active) {
  color: #007ACC;
  background: #007ACC20;
}

:deep(.el-menu-item:hover) {
  background: #2D2D30;
}
</style>
