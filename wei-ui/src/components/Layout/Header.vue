<template>
  <el-header class="header">
    <div class="header-left">
      <span class="page-title">{{ $route.meta.title || 'AI Gateway' }}</span>
    </div>
    <div class="header-right">
      <el-button type="primary" :icon="Refresh" @click="refreshPage">刷新</el-button>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'

const $route = useRoute()

const refreshPage = () => {
  window.location.reload()
}
</script>

<style scoped>
.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
}
</style>
