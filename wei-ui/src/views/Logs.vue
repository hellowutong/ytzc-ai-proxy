<template>
  <div class="logs-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="header-actions">
            <el-select v-model="filterLevel" placeholder="日志级别" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
              <el-option label="CRITICAL" value="CRITICAL" />
            </el-select>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索关键词"
              style="width: 200px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="fetchLogs" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredLogs"
        v-loading="loading"
        stripe
        border
        height="600"
        style="width: 100%"
      >
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
        <el-table-column prop="details" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetails(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="800px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="时间">{{ formatTime(selectedLog?.timestamp) }}</el-descriptions-item>
        <el-descriptions-item label="级别">
          <el-tag :type="getLevelType(selectedLog?.level)">{{ selectedLog?.level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源">{{ selectedLog?.source }}</el-descriptions-item>
        <el-descriptions-item label="消息">{{ selectedLog?.message }}</el-descriptions-item>
        <el-descriptions-item label="详情" v-if="selectedLog?.details">
          <pre class="detail-json">{{ JSON.stringify(selectedLog?.details, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { request } from '@/api/request'

interface LogEntry {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  details?: any
}

const loading = ref(false)
const logs = ref<LogEntry[]>([])
const filterLevel = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const detailVisible = ref(false)
const selectedLog = ref<LogEntry | null>(null)

// 模拟日志数据
const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'INFO',
    source: 'system',
    message: '系统启动成功',
    details: { version: '1.0.0', pid: 12345 }
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    level: 'DEBUG',
    source: 'config',
    message: '配置文件加载完成',
    details: { path: '/app/config.yml', size: 2048 }
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    level: 'WARNING',
    source: 'database',
    message: '数据库连接池接近上限',
    details: { current: 45, max: 50 }
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 180000).toISOString(),
    level: 'ERROR',
    source: 'api',
    message: 'API调用失败',
    details: { endpoint: '/api/v1/chat', error: 'Timeout' }
  }
]

const filteredLogs = computed(() => {
  let result = logs.value

  if (filterLevel.value) {
    result = result.filter(log => log.level === filterLevel.value)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(keyword) ||
      log.source.toLowerCase().includes(keyword)
    )
  }

  return result
})

const getLevelType = (level: string): string => {
  const typeMap: Record<string, string> = {
    'DEBUG': 'info',
    'INFO': 'success',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'danger'
  }
  return typeMap[level] || 'info'
}

const formatTime = (timestamp: string | undefined): string => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const fetchLogs = async () => {
  loading.value = true
  try {
    // 这里应该调用实际的API
    // const res = await request.get('/logs', {
    //   params: { level: filterLevel.value, page: currentPage.value, size: pageSize.value }
    // })
    // logs.value = res.data.data.items
    // total.value = res.data.data.total
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    logs.value = mockLogs
    total.value = mockLogs.length
    ElMessage.success('日志已刷新')
  } catch (error) {
    ElMessage.error('获取日志失败')
    console.error('Fetch logs error:', error)
  } finally {
    loading.value = false
  }
}

const showDetails = (row: LogEntry) => {
  selectedLog.value = row
  detailVisible.value = true
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchLogs()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchLogs()
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.logs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-actions {
    display: flex;
    gap: 10px;
    align-items: center;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.detail-json {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
}
</style>