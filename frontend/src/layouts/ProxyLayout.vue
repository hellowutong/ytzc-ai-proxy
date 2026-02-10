<template>
  <div class="proxy-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Proxy layout is minimal - just renders the child route
</script>

<style scoped>
.proxy-layout {
  height: 100vh;
  background: var(--vscode-bg);
}
</style>
