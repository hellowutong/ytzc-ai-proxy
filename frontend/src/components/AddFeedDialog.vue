<template>
  <el-dialog
    v-model="visible"
    title="添加 RSS 订阅源"
    width="800px"
    class="add-feed-dialog"
    destroy-on-close
    @open="onDialogOpen"
  >
    <!-- URL 输入区 -->
    <div class="url-input-section">
      <el-input
        v-model="feedUrl"
        placeholder="输入 RSS URL 或网站地址..."
        size="large"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" size="large" @click="searchFeed" :loading="searching">
        搜索并添加
      </el-button>
    </div>

    <el-divider />

    <!-- 热门推荐 -->
    <div class="popular-section" v-loading="loadingDiscover">
      <h3 class="section-title">📊 热门订阅源（10个）</h3>
      <div class="feed-grid">
        <div
          v-for="feed in rssStore.discoverFeeds"
          :key="feed.url"
          class="feed-card"
        >
          <div class="feed-icon">{{ feed.icon[0].toUpperCase() }}</div>
          <div class="feed-name">{{ feed.name }}</div>
          <div class="feed-subscribers">{{ feed.subscribers }}订阅</div>
          <el-button 
            size="small" 
            :type="isSubscribed(feed.url) ? 'success' : 'primary'"
            :disabled="isSubscribed(feed.url)"
            @click="subscribePopular(feed)"
          >
            {{ isSubscribed(feed.url) ? '已订阅' : '+ 订阅' }}
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useRSSStore } from '@/stores'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'submit': [data: { name: string; url: string }]
}>()

const rssStore = useRSSStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const feedUrl = ref('')
const searching = ref(false)
const loadingDiscover = ref(false)

const isSubscribed = (url: string) => {
  return rssStore.feeds.some(f => f.url === url)
}

const onDialogOpen = async () => {
  // 弹窗打开时加载热门推荐
  if (rssStore.discoverFeeds.length === 0) {
    loadingDiscover.value = true
    await rssStore.fetchDiscover()
    loadingDiscover.value = false
  }
}


// 转换 RSSHub URL
const convertRsshubUrl = (url: string): string => {
  if (url.startsWith("rsshub://")) {
    return url.replace("rsshub://", "https://rsshub.app/")
  }
  return url
}
const searchFeed = async () => {
  if (!feedUrl.value.trim()) {
    ElMessage.warning('请输入RSS URL')
    return
  }
  
  searching.value = true
  try {
    emit('submit', {
      name: '新订阅',
      url: convertRsshubUrl(feedUrl.value.trim())
    })
    feedUrl.value = ''
  } finally {
    searching.value = false
  }
}

const subscribePopular = (feed: typeof rssStore.discoverFeeds[0]) => {
  emit('submit', {
    name: feed.name,
    url: feed.url
  })
}
</script>

<style scoped>
.url-input-section {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.url-input-section .el-input {
  flex: 1;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #cccccc;
  margin: 0 0 16px 0;
}

.feed-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.feed-card {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  transition: all 0.2s ease;
}

.feed-card:hover {
  border-color: #007acc;
}

.feed-icon {
  width: 40px;
  height: 40px;
  background: #007acc;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  margin: 0 auto 8px;
}

.feed-name {
  font-size: 13px;
  color: #cccccc;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feed-subscribers {
  font-size: 11px;
  color: #858585;
  margin-bottom: 8px;
}

:deep(.el-dialog) {
  background: #252526;
  border: 1px solid #454545;
}

:deep(.el-dialog__title) {
  color: #cccccc;
}

:deep(.el-divider) {
  border-color: #454545;
}
</style>
