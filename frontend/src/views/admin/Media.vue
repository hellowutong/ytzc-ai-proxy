<template>
  <div class="media">
    <el-tabs v-model="activeTab" type="border-card" class="media-tabs">
      <!-- Video Tab -->
      <el-tab-pane label="视频处理" name="video">
        <MediaList 
          type="video"
          :processors="['whisper', 'faster_whisper', 'whisper_npu']"
          :models="['base', 'small', 'medium', 'large']"
        />
      </el-tab-pane>

      <!-- Audio Tab -->
      <el-tab-pane label="音频处理" name="audio">
        <MediaList 
          type="audio"
          :processors="['whisper', 'faster_whisper', 'whisper_npu']"
          :models="['base', 'small', 'medium', 'large']"
        />
      </el-tab-pane>

      <!-- Text Tab -->
      <el-tab-pane label="文档处理" name="text">
        <MediaList 
          type="text"
          :processors="['default']"
          :models="[]"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MediaList from '@/components/MediaList.vue'

const activeTab = ref('video')
</script>

<style scoped>
.media {
  padding: 0;
}

.media-tabs {
  background: #252526;
  border: 1px solid #3C3C3C;
}

:deep(.el-tabs__header) {
  background: #2D2D30;
  border-bottom: 1px solid #3C3C3C;
  margin: 0;
}

:deep(.el-tabs__item) {
  color: #858585;
}

:deep(.el-tabs__item.is-active) {
  color: #007ACC;
  background: #252526;
}

:deep(.el-tabs__content) {
  padding: 20px;
}
</style>
