<template>
  <div class="dashboard">
    <h2>系统概览</h2>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">12,458</div>
          <div class="stat-label">今日请求</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">89</div>
          <div class="stat-label">活跃会话</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">3,421</div>
          <div class="stat-label">知识条目</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">Small</div>
          <div class="stat-label">当前模型</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>请求趋势 (近7天)</template>
          <div ref="trendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>模型使用占比</template>
          <div ref="pieChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="status-row">
      <el-col :span="12">
        <el-card>
          <template #header>系统状态</template>
          <div class="status-list">
            <div class="status-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>MongoDB 正常</span>
            </div>
            <div class="status-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>Redis 正常</span>
            </div>
            <div class="status-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>Qdrant 正常</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>RSS订阅状态</template>
          <div class="rss-list">
            <div class="rss-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>AI科技日报 - 5分钟前更新</span>
            </div>
            <div class="rss-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>技术博客 - 1小时前更新</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const trendChart = ref<HTMLDivElement>()
const pieChart = ref<HTMLDivElement>()

onMounted(() => {
  // Trend Chart
  if (trendChart.value) {
    const chart = echarts.init(trendChart.value)
    chart.setOption({
      xAxis: {
        type: 'category',
        data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        type: 'line',
        smooth: true
      }]
    })
  }

  // Pie Chart
  if (pieChart.value) {
    const chart = echarts.init(pieChart.value)
    chart.setOption({
      series: [{
        type: 'pie',
        data: [
          { value: 65, name: 'Small' },
          { value: 35, name: 'Big' }
        ]
      }]
    })
  }
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.charts-row {
  margin-bottom: 20px;
}

.status-list, .rss-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item, .rss-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
