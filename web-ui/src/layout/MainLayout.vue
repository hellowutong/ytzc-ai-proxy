<template>
  <el-container class="app-container">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon v-if="collapsed"><Grid /></el-icon>
        <span v-else>TW AI Saver</span>
      </div>
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          :router="true"
          :background-color="sidebarBg"
          :text-color="sidebarTextColor"
          :active-text-color="primaryColor"
        >
          <template v-for="route in routes" :key="route.path">
            <el-menu-item
              v-for="child in route.children"
              :key="child.path"
              :index="`/${child.path}`"
            >
              <el-icon><component :is="child.meta.icon" /></el-icon>
              <template #title>{{ child.meta.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleSidebar">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRoute?.meta?.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-switch
            v-model="isDarkMode"
            active-text="暗色"
            inactive-text="亮色"
            @change="toggleTheme"
          />
          <el-dropdown trigger="click">
            <el-icon class="user-icon"><User /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const routes = router.options.routes.find(r => r.path === '/').children

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)
const collapsed = computed(() => appStore.sidebarCollapsed)
const isDarkMode = ref(appStore.theme === 'dark')

const sidebarBg = computed(() => 'var(--sidebar-bg)')
const sidebarTextColor = computed(() => 'var(--text-color)')
const primaryColor = '#409eff'

function toggleSidebar() {
  appStore.toggleSidebar()
}

function toggleTheme() {
  appStore.toggleTheme()
  isDarkMode.value = appStore.isDark
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.documentElement.className = `theme-${appStore.theme}`
})
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: bold;
    color: var(--primary-color);
    border-bottom: 1px solid var(--border-color);
  }
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  margin-right: 16px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 20px;

  .header-left {
    display: flex;
    align-items: center;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .user-icon {
      font-size: 20px;
      cursor: pointer;
    }
  }
}

.main-content {
  background-color: var(--bg-color);
}
</style>
