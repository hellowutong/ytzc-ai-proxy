<template>
  <div class="sessions-page">
    <div class="page-header">
      <h2>会话管理</h2>
      <div class="header-actions">
        <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建会话
        </el-button>
      </div>
    </div>

    <el-table
      :data="sessions"
      v-loading="loading"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '活跃' : '已结束' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message_count" label="消息数" width="100" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button-group>
            <el-button size="small" @click="viewSession(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button size="small" @click="editSession(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="deleteSession(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadSessions"
      @current-change="loadSessions"
      style="margin-top: 20px; justify-content: flex-end"
    />

    <el-drawer v-model="drawerVisible" title="会话详情" size="50%">
      <div class="session-detail" v-if="currentSession">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentSession.id }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ currentSession.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentSession.status === 'active' ? 'success' : 'info'">
              {{ currentSession.status === 'active' ? '活跃' : '已结束' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="消息数">{{ currentSession.message_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentSession.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentSession.updated_at }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px;">消息列表</h4>
        <div class="messages-list">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-item"
            :class="msg.role"
          >
            <div class="message-role">{{ msg.role === 'user' ? '用户' : 'AI' }}</div>
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑会话' : '新建会话'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="会话标题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSession" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sessionsApi } from '@/api'

const sessions = ref([])
const messages = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const currentSession = ref(null)
const selectedIds = ref([])
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const form = reactive({
  title: ''
})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

async function loadSessions() {
  loading.value = true
  try {
    const res = await sessionsApi.list({
      page: pagination.page,
      size: pagination.size
    })
    sessions.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    ElMessage.error('加载会话失败')
  } finally {
    loading.value = false
  }
}

async function loadMessages(sessionId) {
  try {
    messages.value = await sessionsApi.getMessages(sessionId)
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(s => s.id)
}

function showCreateDialog() {
  isEdit.value = false
  form.title = ''
  dialogVisible.value = true
}

function viewSession(row) {
  currentSession.value = row
  loadMessages(row.id)
  drawerVisible.value = true
}

function editSession(row) {
  isEdit.value = true
  editingId.value = row.id
  form.title = row.title
  dialogVisible.value = true
}

async function saveSession() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value) {
        await sessionsApi.update(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await sessionsApi.create(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadSessions()
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

async function deleteSession(row) {
  try {
    await ElMessageBox.confirm('确定删除此会话?', '确认', { type: 'warning' })
    await sessionsApi.delete(row.id)
    ElMessage.success('删除成功')
    loadSessions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 个会话?`, '确认', { type: 'warning' })
    await sessionsApi.deleteBatch(selectedIds.value)
    ElMessage.success('批量删除成功')
    loadSessions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<style lang="scss" scoped>
.sessions-page {
  padding: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.messages-list {
  max-height: 500px;
  overflow-y: auto;

  .message-item {
    padding: 12px;
    margin-bottom: 12px;
    border-radius: 8px;

    &.user {
      background: #e3f2fd;
      margin-left: 40px;
    }

    &.assistant {
      background: #f5f5f5;
      margin-right: 40px;
    }

    .message-role {
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
    }

    .message-content {
      white-space: pre-wrap;
    }
  }
}
</style>
