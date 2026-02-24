<template>
  <el-menu
    :default-active="activeMenu"
    class="sidebar-menu vscode-menu"
    background-color="transparent"
    text-color="#858585"
    active-text-color="#cccccc"
    router
    :collapse="false"
  >
    <el-menu-item index="/admin/dashboard">
      <el-icon><Odometer /></el-icon>
      <span>看板</span>
    </el-menu-item>
    
    <el-sub-menu index="models">
      <template #title>
        <el-icon><Connection /></el-icon>
        <span>虚拟模型</span>
      </template>
      <el-menu-item index="/admin/models">模型管理</el-menu-item>
    </el-sub-menu>
    
    <el-menu-item index="/admin/skills">
      <el-icon><Lightning /></el-icon>
      <span>Skill管理</span>
    </el-menu-item>
    
    <el-menu-item index="/admin/conversations">
      <el-icon><ChatDotRound /></el-icon>
      <span>对话历史</span>
    </el-menu-item>
    
    <el-menu-item index="/admin/knowledge">
      <el-icon><Collection /></el-icon>
      <span>知识库</span>
    </el-menu-item>
    
    <el-menu-item index="/admin/media">
      <el-icon><VideoCamera /></el-icon>
      <span>媒体处理</span>
    </el-menu-item>
    
    <el-menu-item index="/admin/rss">
      <el-icon><Bell /></el-icon>
      <span>RSS订阅</span>
    </el-menu-item>
    
    <el-sub-menu index="logs">
      <template #title>
        <el-icon><Document /></el-icon>
        <span>日志查询</span>
      </template>
      <el-menu-item index="/admin/logs">日志中心</el-menu-item>
    </el-sub-menu>
    
    <el-menu-item index="/admin/config">
      <el-icon><Setting /></el-icon>
      <span>系统配置</span>
    </el-menu-item>
    
    <el-menu-item index="/admin/raw-data">
      <el-icon><DataLine /></el-icon>
      <span>原始数据</span>
    </el-menu-item>
    
    <el-divider class="menu-divider" />
    
    <el-menu-item index="/proxy/chat">
      <el-icon><ChatLineRound /></el-icon>
      <span>WebChat测试</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Odometer,
  Connection,
  ChatDotRound,
  Collection,
  VideoCamera,
  Document,
  Setting,
  DataLine,
  ChatLineRound,
  Lightning,
  Bell
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.sidebar-menu {
  border-right: none;
  flex: 1;
  padding: 12px 0;
  background-color: transparent;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
  margin: 4px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: #2a2d2e !important;
  color: #cccccc !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #264f78 !important;
  color: #cccccc !important;
  font-weight: 500;
  border-left: 3px solid #007acc;
}

.sidebar-menu :deep(.el-icon) {
  font-size: 18px;
  margin-right: 12px;
}

.menu-divider {
  margin: 12px 16px;
  border-color: #3c3c3c;
}

/* Override Element Plus menu background */
.sidebar-menu :deep(.el-menu),
.sidebar-menu :deep(.el-sub-menu .el-menu) {
  background-color: transparent;
}
</style>
