<template>
  <div class="rawdata-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>原始数据管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索数据..."
              style="width: 250px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="openAddDialog">
              <el-icon><Plus /></el-icon>
              添加数据
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredData" stripe border v-loading="loading">
        <el-table-column type="index" width="50" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="content_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.content_type)">{{ row.content_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="150" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'processed' ? 'success' : 'warning'">
              {{ row.status === 'processed' ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetails(row)">查看</el-button>
            <el-button type="warning" link @click="editData(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteData(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑数据' : '添加数据'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-select v-model="form.content_type" placeholder="选择类型" style="width: 100%">
            <el-option label="文章" value="article" />
            <el-option label="文档" value="document" />
            <el-option label="网页" value="webpage" />
            <el-option label="代码" value="code" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="10"
            placeholder="请输入内容..."
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="添加标签"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="数据详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ selectedData?.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getTypeColor(selectedData?.content_type)">{{ selectedData?.content_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源">{{ selectedData?.source }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="selectedData?.status === 'processed' ? 'success' : 'warning'">
            {{ selectedData?.status === 'processed' ? '已处理' : '待处理' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedData?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(selectedData?.updated_at) }}</el-descriptions-item>
      </el-descriptions>
      <div class="content-preview">
        <h4>内容预览</h4>
        <pre>{{ selectedData?.content }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface RawData {
  id: string
  title: string
  content: string
  content_type: string
  source: string
  tags: string[]
  status: 'pending' | 'processed'
  created_at: string
  updated_at: string
}

const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(100)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const selectedData = ref<RawData | null>(null)

const form = ref<Partial<RawData>>({
  title: '',
  content: '',
  content_type: 'article',
  tags: []
})

const rawDataList = ref<RawData[]>([
  {
    id: '1',
    title: 'Vue3 组合式API最佳实践',
    content: 'Vue3的组合式API提供了更好的逻辑复用和代码组织方式...',
    content_type: 'article',
    source: '手动录入',
    tags: ['Vue', '前端', '教程'],
    status: 'processed',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: '2',
    title: 'Python FastAPI 入门指南',
    content: 'FastAPI是一个现代、快速的Python Web框架...',
    content_type: 'document',
    source: '导入',
    tags: ['Python', '后端', 'API'],
    status: 'pending',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString()
  }
])

const filteredData = computed(() => {
  if (!searchKeyword.value) return rawDataList.value
  const keyword = searchKeyword.value.toLowerCase()
  return rawDataList.value.filter(item =>
    item.title.toLowerCase().includes(keyword) ||
    item.content.toLowerCase().includes(keyword) ||
    item.tags.some(tag => tag.toLowerCase().includes(keyword))
  )
})

const getTypeColor = (type: string | undefined): string => {
  const colorMap: Record<string, string> = {
    'article': 'success',
    'document': 'primary',
    'webpage': 'warning',
    'code': 'danger',
    'other': 'info'
  }
  return colorMap[type || 'other'] || 'info'
}

const formatTime = (timestamp: string | undefined): string => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const openAddDialog = () => {
  isEdit.value = false
  form.value = {
    title: '',
    content: '',
    content_type: 'article',
    tags: []
  }
  dialogVisible.value = true
}

const editData = (row: RawData) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const viewDetails = (row: RawData) => {
  selectedData.value = row
  detailVisible.value = true
}

const deleteData = async (row: RawData) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${row.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    rawDataList.value = rawDataList.value.filter(item => item.id !== row.id)
    ElMessage.success('删除成功')
  } catch {
    // 取消删除
  }
}

const submitForm = () => {
  if (isEdit.value) {
    const index = rawDataList.value.findIndex(item => item.id === form.value.id)
    if (index > -1) {
      rawDataList.value[index] = { ...rawDataList.value[index], ...form.value } as RawData
    }
    ElMessage.success('更新成功')
  } else {
    const newData: RawData = {
      ...form.value as RawData,
      id: Date.now().toString(),
      source: '手动录入',
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    rawDataList.value.unshift(newData)
    ElMessage.success('添加成功')
  }
  dialogVisible.value = false
}
</script>

<style scoped lang="scss">
.rawdata-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.content-preview {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: var(--el-text-color-primary);
  }

  pre {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}
</style>