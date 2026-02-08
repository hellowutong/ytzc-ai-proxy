<template>
  <el-container class="layout-container">
    <Sidebar />
    <el-container>
      <Header />
      <el-main class="main-content">
        <!-- 测试横幅 - 如果你看到这个,说明页面已更新 2024-02-08 21:50 -->
        <div style="background: #ff0000; color: white; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; font-size: 18px;">
          🔴 测试页面 - 如果你看到这个红色横幅,说明页面已更新!
        </div>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
