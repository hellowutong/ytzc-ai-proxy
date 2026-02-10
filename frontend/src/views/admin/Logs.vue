<template>
  <div class="logs">
    <el-tabs v-model="activeTab" type="border-card" class="logs-tabs">
      <!-- System Logs -->
      <el-tab-pane label="系统日志" name="system">
        <LogViewer type="system" />
      </el-tab-pane>

      <!-- Operation Logs -->
      <el-tab-pane label="操作日志" name="operation">
        <LogViewer type="operation" />
      </el-tab-pane>

      <!-- Skill Logs -->
      <el-tab-pane label="Skill执行日志" name="skill">
        <LogViewer type="skill" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LogViewer from '@/components/LogViewer.vue'

const activeTab = ref('system')
</script>

<style scoped>
.logs {
  padding: 0;
}

.logs-tabs {
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
