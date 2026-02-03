<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>仪表盘</h2>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <el-icon class="stat-icon" :size="40" color="#409eff"><Connection /></el-icon>
          <div class="stat-content">
            <div class="stat-value">{{ stats.connections }}</div>
            <div class="stat-label">连接数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon class="stat-icon" :size="40" color="#67c23a"><ChatLineRound /></el-icon>
          <div class="stat-content">
            <div class="stat-value">{{ stats.sessions }}</div>
            <div class="stat-label">会话数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon class="stat-icon" :size="40" color="#e6a23c"><Star /></el-icon>
          <div class="stat-content">
            <div class="stat-value">{{ stats.skills }}</div>
            <div class="stat-label">技能数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <el-icon class="stat-icon" :size="40" color="#909399"><DataLine /></el-icon>
          <div class="stat-content">
            <div class="stat-value">{{ stats.vectors }}</div>
            <div class="stat-label">向量数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <span>会话趋势 (近7天)</span>
          </template>
          <div ref="chartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="provider-card">
          <template #header>
            <span>AI 提供商分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近会话</span>
          </template>
          <el-table :data="recentSessions" style="width: 100%">
            <el-table-column prop="id" label="ID" width="100" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>系统状态</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="后端服务">
              <el-tag :type="systemStatus.backend ? 'success' : 'danger'">
                {{ systemStatus.backend ? '运行中' : '停止' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="MongoDB">
              <el-tag :type="systemStatus.mongodb ? 'success' : 'warning'">
                {{ systemStatus.mongodb ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Qdrant">
              <el-tag :type="systemStatus.qdrant ? 'success' : 'warning'">
                {{ systemStatus.qdrant ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              {{ systemStatus.version || '未知' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { healthApi, connectionsApi, sessionsApi, skillsApi, vectorsApi } from '@/api'
import request from '@/api/request'

const stats = ref({
  connections: 0,
  sessions: 0,
  skills: 0,
  vectors: 0
})

const recentSessions = ref([])
const systemStatus = ref({
  backend: false,
  mongodb: false,
  qdrant: false,
  version: ''
})

const chartRef = ref(null)
const pieChartRef = ref(null)
let chartInstance = null
let pieChartInstance = null

async function loadStats() {
  try {
    const [health, connections, sessions, skills, statsResponse] = await Promise.all([
      healthApi.getHealth().catch(() => ({})),
      connectionsApi.list().catch(() => []),
      sessionsApi.list({ limit: 5 }).catch(() => ({ items: [] })),
      skillsApi.list({ limit: 5 }).catch(() => ({ items: [] })),
      request.get('/api/v1/stats').catch(() => ({}))
    ])

    // 连接数据可能是数组或对象
    stats.value.connections = Array.isArray(connections) ? connections.length : (connections.data?.length || 0)
    stats.value.sessions = sessions.items?.length || 0
    stats.value.skills = skills.items?.length || 0
    stats.value.vectors = 0 // vectors需要单独API调用
    
    recentSessions.value = sessions.items || []

    systemStatus.value = {
      backend: health.status === 'healthy',
      mongodb: false, // 暂时设为false，需要实际检查
      qdrant: false,  // 暂时设为false，需要实际检查
      version: health.version || statsResponse?.version || 'v1.0.0'
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 设置默认值避免前端崩溃
    stats.value = { connections: 0, sessions: 0, skills: 0, vectors: 0 }
    recentSessions.value = []
    systemStatus.value = { backend: false, mongodb: false, qdrant: false, version: 'v1.0.0' }
  }
}

function initCharts() {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
      yAxis: { type: 'value' },
      series: [{
        data: [12, 17, 8, 15, 22, 10, 18],
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 }
      }]
    })
  }

  if (pieChartRef.value) {
    pieChartInstance = echarts.init(pieChartRef.value)
    pieChartInstance.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: 40, name: 'OpenAI' },
          { value: 30, name: 'DeepSeek' },
          { value: 20, name: 'Claude' },
          { value: 10, name: 'Gemini' }
        ]
      }]
    })
  }
}

function refreshData() {
  loadStats()
}

function handleResize() {
  chartInstance?.resize()
  pieChartInstance?.resize()
}

onMounted(() => {
  loadStats()
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  pieChartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 0;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;

  .stat-icon {
    margin-right: 16px;
  }

  .stat-content {
    .stat-value {
      font-size: 28px;
      font-weight: bold;
      color: var(--text-color);
    }

    .stat-label {
      font-size: 14px;
      color: var(--text-color-secondary);
      margin-top: 4px;
    }
  }
}

.chart-card, .provider-card {
  height: 350px;

  :deep(.el-card__body) {
    height: calc(100% - 40px);
  }
}

.chart-container {
  height: 100%;
  width: 100%;
}
</style>
