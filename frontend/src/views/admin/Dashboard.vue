<template>
  <div class="dashboard vscode-theme">
    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4" v-for="stat in statsList" :key="stat.key">
        <el-card class="stat-card" shadow="hover" @click="stat.onClick">
          <div class="stat-icon" :style="{ background: stat.gradient }">
            <el-icon :size="24" color="#fff">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboardStore.stats[stat.key] }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Dependencies Status Monitor -->
    <el-row :gutter="20" class="deps-row">
      <el-col :span="24">
        <el-card class="deps-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Monitor /></el-icon>
                第三方依赖状态监控
              </span>
              <el-button link @click="refreshDepsStatus">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="deps-grid">
            <div 
              v-for="dep in dependencies" 
              :key="dep.name" 
              class="dep-item"
              :class="{ 'dep-healthy': dep.status === 'healthy', 'dep-unhealthy': dep.status === 'unhealthy', 'dep-warning': dep.status === 'warning' }"
            >
              <div class="dep-header">
                <div class="dep-icon" :style="{ background: dep.color }">
                  <el-icon :size="20">
                    <component :is="dep.icon" />
                  </el-icon>
                </div>
                <div class="dep-status">
                  <el-tag 
                    :type="dep.status === 'healthy' ? 'success' : dep.status === 'warning' ? 'warning' : 'danger'"
                    size="small"
                  >
                    {{ dep.statusText }}
                  </el-tag>
                </div>
              </div>
              <div class="dep-info">
                <div class="dep-name">{{ dep.name }}</div>
                <div class="dep-detail">{{ dep.detail }}</div>
                <div class="dep-latency" v-if="dep.latency">
                  响应时间: {{ dep.latency }}ms
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-row :gutter="20" class="actions-row">
      <el-col :span="24">
        <el-card class="actions-card">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button 
              type="primary" 
              :loading="reloadingConfig"
              @click="handleReloadConfig"
            >
              <el-icon><Refresh /></el-icon>
              重载配置
            </el-button>
            <el-button 
              type="success" 
              :loading="reloadingSkills"
              @click="handleReloadSkills"
            >
              <el-icon><Lightning /></el-icon>
              重载Skill
            </el-button>
            <el-button @click="$router.push('/admin/logs')">
              <el-icon><Document /></el-icon>
              查看日志
            </el-button>
            <el-button @click="$router.push('/admin/config')">
              <el-icon><Setting /></el-icon>
              系统配置
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activities -->
    <el-row :gutter="20" class="activities-row">
      <el-col :span="24">
        <el-card class="activities-card" v-loading="dashboardStore.loading">
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <el-button link @click="refreshActivities">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <el-table :data="dashboardStore.activities" style="width: 100%">
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getTypeTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="操作" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="查看" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="viewLog(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Connection,
  ChatDotRound,
  Collection,
  VideoCamera,
  Bell,
  Monitor,
  Refresh,
  Lightning,
  Document,
  Setting,
  Tools,
  Timer,
  Coin,
  DataLine,
  Search,
  Grid
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores'

const router = useRouter()
const dashboardStore = useDashboardStore()

const reloadingConfig = ref(false)
const reloadingSkills = ref(false)

// Dependencies status - 从 store 获取
const dependencies = computed(() => dashboardStore.dependencies)

const refreshDepsStatus = async () => {
  ElMessage.info('正在刷新依赖状态...')
  await dashboardStore.fetchDependenciesStatus()
  ElMessage.success('依赖状态已刷新')
}

const statsList = [
  {
    key: 'virtual_models',
    label: '虚拟模型',
    icon: Connection,
    gradient: 'linear-gradient(135deg, #007ACC 0%, #1E90FF 100%)',
    onClick: () => router.push('/admin/models')
  },
  {
    key: 'today_conversations',
    label: '今日对话',
    icon: ChatDotRound,
    gradient: 'linear-gradient(135deg, #E06C75 0%, #FF6B6B 100%)',
    onClick: () => router.push('/admin/conversations')
  },
  {
    key: 'knowledge_docs',
    label: '知识库文档',
    icon: Collection,
    gradient: 'linear-gradient(135deg, #98C379 0%, #7CB342 100%)',
    onClick: () => router.push('/admin/knowledge')
  },
  {
    key: 'media_queue',
    label: '媒体队列',
    icon: VideoCamera,
    gradient: 'linear-gradient(135deg, #61AFEF 0%, #42A5F5 100%)',
    onClick: () => router.push('/admin/media')
  },
  {
    key: 'rss_feeds',
    label: 'RSS订阅',
    icon: Bell,
    gradient: 'linear-gradient(135deg, #D19A66 0%, #FF9800 100%)',
    onClick: () => router.push('/admin/rss')
  },
  {
    key: 'system_status',
    label: '系统状态',
    icon: Monitor,
    gradient: 'linear-gradient(135deg, #C678DD 0%, #AB47BC 100%)',
    onClick: () => refreshStats()
  }
]

const getTypeTag = (type: string) => {
  const map: Record<string, string> = {
    config: 'primary',
    skill: 'success',
    model: 'warning',
    media: 'info',
    rss: 'danger'
  }
  return map[type] || 'info'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const refreshStats = async () => {
  await dashboardStore.fetchStats()
  ElMessage.success('统计数据已刷新')
}

const refreshActivities = async () => {
  await dashboardStore.fetchActivities()
  ElMessage.success('活动列表已刷新')
}

const handleReloadConfig = async () => {
  reloadingConfig.value = true
  const success = await dashboardStore.reloadConfig()
  reloadingConfig.value = false
  if (success) {
    ElMessage.success('配置重载成功')
  } else {
    ElMessage.error('配置重载失败')
  }
}

const handleReloadSkills = async () => {
  reloadingSkills.value = true
  const success = await dashboardStore.reloadSkills()
  reloadingSkills.value = false
  if (success) {
    ElMessage.success('Skill重载成功')
  } else {
    ElMessage.error('Skill重载失败')
  }
}

const viewLog = (row: any) => {
  router.push('/admin/logs')
}

onMounted(() => {
  dashboardStore.fetchStats()
  dashboardStore.fetchActivities()
  dashboardStore.fetchDependenciesStatus()
})
</script>

<style scoped>
/* VS Code Theme Variables */
.vscode-theme {
  --vscode-bg: #1e1e1e;
  --vscode-sidebar: #252526;
  --vscode-card: #252526;
  --vscode-border: #3c3c3c;
  --vscode-text: #d4d4d4;
  --vscode-text-secondary: #858585;
  --vscode-blue: #007acc;
  --vscode-blue-light: #1e90ff;
  --vscode-green: #4caf50;
  --vscode-red: #f44336;
  --vscode-yellow: #ff9800;
  --vscode-purple: #9c27b0;
}

.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--vscode-card);
  border: 1px solid var(--vscode-border);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 122, 204, 0.2);
  border-color: var(--vscode-blue);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.stat-content {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--vscode-text);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--vscode-text-secondary);
}

/* Dependencies Status Section */
.deps-row {
  margin-bottom: 20px;
}

.deps-card {
  background: var(--vscode-card);
  border: 1px solid var(--vscode-border);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--vscode-text);
}

.deps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.dep-item {
  background: #2d2d2d;
  border: 1px solid var(--vscode-border);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.dep-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dep-healthy {
  border-left: 4px solid var(--vscode-green);
}

.dep-unhealthy {
  border-left: 4px solid var(--vscode-red);
}

.dep-warning {
  border-left: 4px solid var(--vscode-yellow);
}

.dep-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dep-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.dep-info {
  color: var(--vscode-text);
}

.dep-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.dep-detail {
  font-size: 13px;
  color: var(--vscode-text-secondary);
  margin-bottom: 8px;
}

.dep-latency {
  font-size: 12px;
  color: var(--vscode-blue-light);
  font-family: 'Consolas', 'Monaco', monospace;
}

.actions-row {
  margin-bottom: 20px;
}

.actions-card {
  background: var(--vscode-card);
  border: 1px solid var(--vscode-border);
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.activities-card {
  background: var(--vscode-card);
  border: 1px solid var(--vscode-border);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--vscode-border);
  color: var(--vscode-text);
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table tr) {
  background: transparent;
  color: var(--vscode-text);
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-hover);
}

:deep(.el-table td) {
  color: var(--vscode-text);
}

/* VS Code style buttons */
:deep(.el-button--primary) {
  background: var(--vscode-blue);
  border-color: var(--vscode-blue);
}

:deep(.el-button--primary:hover) {
  background: var(--vscode-blue-light);
  border-color: var(--vscode-blue-light);
}

:deep(.el-tag--success) {
  background: rgba(76, 175, 80, 0.2);
  border-color: var(--vscode-green);
  color: var(--vscode-green);
}

:deep(.el-tag--danger) {
  background: rgba(244, 67, 54, 0.2);
  border-color: var(--vscode-red);
  color: var(--vscode-red);
}

:deep(.el-tag--warning) {
  background: rgba(255, 152, 0, 0.2);
  border-color: var(--vscode-yellow);
  color: var(--vscode-yellow);
}
</style>
