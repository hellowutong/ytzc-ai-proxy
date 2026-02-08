<template>
  <div class="skill-container">
    <div class="page-header">
      <h2>Skill管理</h2>
    </div>
    <el-card>
      <el-empty description="Skill管理页面开发中" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.skill-container {
  padding: 20px;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  padding-right: 5px;
}

.page-header {
  margin-bottom: 20px;
  overflow-x: hidden;
  width: 100%;

  h2 {
    margin: 0;
    font-size: 24px;
    color: #303133;
    overflow-x: hidden;
    word-break: break-all;
  }
}

:deep(.el-card) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

:deep(.el-card__body) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

:deep(.el-empty) {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}
</style>
