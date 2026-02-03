<template>
  <div class="backups-page">
    <div class="page-header">
      <h2>备份管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="createBackup" :loading="creating">
          <el-icon><Plus /></el-icon>
          创建备份
        </el-button>
      </div>
    </div>

    <el-table :data="backups" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="name" label="备份名称" />
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">
          {{ formatSize(row.size) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button-group>
            <el-button size="small" @click="downloadBackup(row)">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button size="small" type="warning" @click="restoreBackup(row)">
              <el-icon><RefreshRight /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="deleteBackup(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="backups.length === 0 && !loading" class="empty-state">
      <el-icon><Folder /></el-icon>
      <p>暂无备份</p>
      <el-button type="primary" @click="createBackup">创建第一个备份</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { backupsApi } from '@/api'

const backups = ref([])
const loading = ref(false)
const creating = ref(false)

async function loadBackups() {
  loading.value = true
  try {
    backups.value = await backupsApi.list()
  } catch (error) {
    ElMessage.error('加载备份失败')
  } finally {
    loading.value = false
  }
}

async function createBackup() {
  creating.value = true
  try {
    await backupsApi.create()
    ElMessage.success('备份创建成功')
    loadBackups()
  } catch (error) {
    ElMessage.error('备份创建失败')
  } finally {
    creating.value = false
  }
}

async function downloadBackup(row) {
  try {
    const blob = await backupsApi.download(row.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.name || `backup_${row.id}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

async function restoreBackup(row) {
  try {
    await ElMessageBox.confirm('确定恢复此备份? 当前数据将被覆盖!', '确认', { type: 'warning' })
    await backupsApi.restore(row.id)
    ElMessage.success('恢复成功，请刷新页面')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('恢复失败')
    }
  }
}

async function deleteBackup(row) {
  try {
    await ElMessageBox.confirm('确定删除此备份?', '确认', { type: 'warning' })
    await backupsApi.delete(row.id)
    ElMessage.success('删除成功')
    loadBackups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadBackups()
})
</script>

<style lang="scss" scoped>
.backups-page {
  padding: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
