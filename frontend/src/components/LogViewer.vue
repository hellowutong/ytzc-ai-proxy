<template>
  <div class="log-viewer">
    <!-- Filters -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="日志级别" v-if="type === 'system'">
          <el-checkbox-group v-model="filters.level">
            <el-checkbox label="DEBUG">DEBUG</el-checkbox>
            <el-checkbox label="INFO">INFO</el-checkbox>
            <el-checkbox label="WARNING">WARNING</el-checkbox>
            <el-checkbox label="ERROR">ERROR</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="模块" v-if="type === 'system'">
          <el-input v-model="filters.module" placeholder="模块名称" clearable />
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
          />
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索关键词" clearable />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="applyFilters"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button @click="exportLogs('json')">导出JSON</el-button>
          <el-button @click="exportLogs('csv')">导出CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Log Table -->
    <el-card class="log-card" v-loading="logStore.loading">
      <el-table :data="logStore.logs" style="width: 100%" height="calc(100vh - 350px)">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.timestamp).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        
        <el-table-column prop="level" label="级别" width="100" v-if="type === 'system'">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="module" label="模块" width="150" v-if="type === 'system'" />
        
        <el-table-column prop="message" label="消息" width="500" show-overflow-tooltip />

        <el-table-column label="操作" width="200" fixed="right" class-name="operation-column">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetails(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          background
          layout="prev, pager, next, sizes, total"
          :total="100"
          :page-sizes="[20, 50, 100]"
          default-page-size="50"
        />
      </div>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetailDialog" title="日志详情" width="600px">
      <pre class="detail-content">{{ JSON.stringify(selectedLog, null, 2) }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useLogStore } from '@/stores'
import type { LogEntry } from '@/types'

const props = defineProps<{
  type: 'system' | 'operation' | 'skill'
}>()

const logStore = useLogStore()

const filters = ref({
  level: [] as string[],
  module: '',
  keyword: ''
})

const dateRange = ref([])
const showDetailDialog = ref(false)
const selectedLog = ref<LogEntry | null>(null)

const getLevelType = (level: string) => {
  const map: Record<string, string> = {
    DEBUG: 'info',
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger'
  }
  return map[level] || 'info'
}

const applyFilters = () => {
  logStore.setFilters({
    ...filters.value,
    start_time: dateRange.value?.[0]?.toISOString(),
    end_time: dateRange.value?.[1]?.toISOString()
  })
  logStore.fetchLogs(props.type)
}

const resetFilters = () => {
  filters.value = {
    level: [],
    module: '',
    keyword: ''
  }
  dateRange.value = []
  applyFilters()
}

const exportLogs = async (format: 'json' | 'csv') => {
  await logStore.exportLogs(props.type, format)
}

const viewDetails = (log: LogEntry) => {
  selectedLog.value = log
  showDetailDialog.value = true
}

onMounted(() => {
  logStore.fetchLogs(props.type)
})
</script>

<style scoped>
.log-viewer {
  padding: 0;
}

.filter-card,
.log-card {
  background: #252526;
  border: 1px solid #3C3C3C;
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #3C3C3C;
  margin-top: 16px;
}

.detail-content {
  background: #1E1E1E;
  border: 1px solid #3C3C3C;
  border-radius: 4px;
  padding: 16px;
  margin: 0;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #CCCCCC;
  overflow-x: auto;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table th.el-table__cell) {
  color: var(--text-secondary) !important;
}

/* 统一所有表头单元格背景色，包括固定列 */
:deep(.el-table .el-table__header-wrapper th.el-table__cell),
:deep(.el-table .el-table__fixed-header-wrapper th.el-table__cell) {
  background-color: var(--bg-tertiary) !important;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-hover);
}
</style>
