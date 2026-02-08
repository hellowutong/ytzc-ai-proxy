<template>
  <el-aside width="220px" class="sidebar">
    <div class="logo">
      <el-icon size="32"><Cpu /></el-icon>
      <span class="title">AI Gateway</span>
    </div>
    
    <el-menu
      :default-active="$route.path"
      router
      class="sidebar-menu"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      
      <el-menu-item index="/config">
        <el-icon><Setting /></el-icon>
        <span>系统配置</span>
      </el-menu-item>
      
      <el-menu-item index="/logs">
        <el-icon><Document /></el-icon>
        <span>系统日志</span>
      </el-menu-item>
      
      <el-menu-item index="/models">
        <el-icon><Cpu /></el-icon>
        <span>模型管理</span>
      </el-menu-item>
      
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>对话管理</span>
      </el-menu-item>
      
      <el-menu-item index="/raw-data">
        <el-icon><Files /></el-icon>
        <span>原始数据</span>
      </el-menu-item>
      
      <el-menu-item index="/knowledge">
        <el-icon><Collection /></el-icon>
        <span>知识库</span>
      </el-menu-item>

      <el-menu-item index="/skill">
        <el-icon><Grid /></el-icon>
        <span>Skill</span>
      </el-menu-item>

      <el-sub-menu index="/media">
        <template #title>
          <el-icon><VideoCamera /></el-icon>
          <span>媒体管理</span>
        </template>
        <el-menu-item index="/media/video">视频</el-menu-item>
        <el-menu-item index="/media/audio">音频</el-menu-item>
        <el-menu-item index="/media/text">文本&图片</el-menu-item>
      </el-sub-menu>
      
      <el-menu-item index="/rss">
        <el-icon><Connection /></el-icon>
        <span>RSS订阅</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { 
  Odometer, Setting, Document, Cpu, ChatDotRound, 
  Files, Collection, Grid, VideoCamera, Connection 
} from '@element-plus/icons-vue'

const $route = useRoute()
</script>

<style scoped>
.sidebar {
  background-color: #304156;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}

.logo .el-icon {
  margin-right: 10px;
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - 60px);
}
</style>
