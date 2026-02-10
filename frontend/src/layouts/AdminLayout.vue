<template>
  <el-container class="admin-layout app-theme">
    <!-- Sidebar -->
    <el-aside width="240px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">🚀</span>
        <span class="logo-text">AI Gateway</span>
      </div>
      <SidebarMenu />
    </el-aside>
    
    <!-- Main Content -->
    <el-container class="main-container">
      <!-- Header -->
      <el-header class="header" height="60px">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta?.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="系统状态">
            <el-badge is-dot type="success" class="status-badge">
              <el-icon :size="20"><Monitor /></el-icon>
            </el-badge>
          </el-tooltip>
          <el-tooltip content="刷新页面">
            <el-button circle @click="refreshPage">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>
      
      <!-- Content -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { Monitor, Refresh } from '@element-plus/icons-vue'
import SidebarMenu from '@/components/SidebarMenu.vue'

const route = useRoute()
const router = useRouter()

const refreshPage = () => {
  router.go(0)
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background: var(--bg-secondary);
}

.sidebar {
  background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-primary);
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
}

.logo-icon {
  font-size: 26px;
  margin-right: 12px;
  filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.4));
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(90deg, var(--primary-400), var(--primary-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.main-container {
  background: var(--bg-secondary);
}

.header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-left :deep(.el-breadcrumb__inner) {
  color: var(--text-tertiary);
  font-weight: 500;
}

.header-left :deep(.el-breadcrumb__inner.is-link:hover) {
  color: var(--primary-400);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right :deep(.el-button) {
  background-color: var(--bg-tertiary);
  border-color: var(--border-secondary);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.header-right :deep(.el-button:hover) {
  background-color: var(--bg-hover);
  border-color: var(--border-tertiary);
  color: var(--text-primary);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
}

.status-badge {
  cursor: pointer;
  color: var(--text-secondary);
}

.main-content {
  padding: 28px;
  overflow-y: auto;
  background: var(--bg-secondary);
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
