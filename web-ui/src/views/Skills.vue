<template>
  <div class="skills-page">
    <div class="page-header">
      <h2>技能管理</h2>
      <div class="header-actions">
        <el-upload
          :auto-upload="false"
          :on-change="handleUpload"
          accept=".zip"
          :show-file-list="false"
        >
          <el-button type="warning">
            <el-icon><Upload /></el-icon>
            导入 ZIP
          </el-button>
        </el-upload>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建技能
        </el-button>
      </div>
    </div>

    <el-table :data="skills" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : row.status === 'draft' ? 'warning' : 'info'">
            {{ row.status === 'published' ? '已发布' : row.status === 'draft' ? '草稿' : '归档' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" align="center" />
      <el-table-column prop="current_version_id" label="当前版本" width="100" />
      <el-table-column label="操作" width="280" align="center">
        <template #default="{ row }">
          <el-button-group>
            <el-button size="small" @click="viewSkill(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button size="small" @click="editSkill(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="success" @click="publishSkill(row)" :disabled="row.status === 'published'">
              <el-icon><Check /></el-icon>
            </el-button>
            <el-button size="small" type="primary" @click="exportSkill(row)">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="deleteSkill(row)">
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
      @size-change="loadSkills"
      @current-change="loadSkills"
      style="margin-top: 20px; justify-content: flex-end"
    />

    <el-drawer v-model="drawerVisible" title="技能详情" size="50%">
      <div class="skill-detail" v-if="currentSkill">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ currentSkill.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ currentSkill.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentSkill.status === 'published' ? 'success' : 'warning'">
              {{ currentSkill.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">{{ currentSkill.version }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentSkill.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentSkill.updated_at }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 20px 0 10px;">版本历史</h4>
        <el-timeline>
          <el-timeline-item
            v-for="v in versions"
            :key="v.id"
            :timestamp="v.created_at"
            :type="v.id === currentSkill.current_version_id ? 'primary' : ''"
          >
            <strong>{{ v.version_id }}</strong>
            <p>{{ v.description || '无描述' }}</p>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑技能' : '新建技能'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="技能名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="技能描述" />
        </el-form-item>
        <el-form-item label="提示词" prop="prompt_template">
          <el-input v-model="form.prompt_template" type="textarea" :rows="5" placeholder="系统提示词模板" />
        </el-form-item>
        <el-form-item label="规则" prop="rules">
          <el-input v-model="form.rules" type="textarea" :rows="3" placeholder="YAML 格式规则" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSkill" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { skillsApi } from '@/api'

const skills = ref([])
const versions = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const currentSkill = ref(null)
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const form = reactive({
  name: '',
  description: '',
  prompt_template: '',
  rules: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  prompt_template: [{ required: true, message: '请输入提示词', trigger: 'blur' }]
}

async function loadSkills() {
  loading.value = true
  try {
    const res = await skillsApi.list({ page: pagination.page, size: pagination.size })
    skills.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    ElMessage.error('加载技能失败')
  } finally {
    loading.value = false
  }
}

async function loadVersions(skillId) {
  try {
    versions.value = await skillsApi.listVersions(skillId)
  } catch (error) {
    console.error('加载版本失败:', error)
  }
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { name: '', description: '', prompt_template: '', rules: '' })
  dialogVisible.value = true
}

function viewSkill(row) {
  currentSkill.value = row
  loadVersions(row.id)
  drawerVisible.value = true
}

function editSkill(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

async function saveSkill() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value) {
        await skillsApi.update(editingId.value, form)
        ElMessage.success('更新成功')
      } else {
        await skillsApi.create(form)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadSkills()
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

async function publishSkill(row) {
  try {
    await skillsApi.publish(row.id)
    ElMessage.success('发布成功')
    loadSkills()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

async function exportSkill(row) {
  try {
    const blob = await skillsApi.export(row.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.name}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

async function deleteSkill(row) {
  try {
    await ElMessageBox.confirm('确定删除此技能?', '确认', { type: 'warning' })
    await skillsApi.delete(row.id)
    ElMessage.success('删除成功')
    loadSkills()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleUpload({ raw }) {
  const formData = new FormData()
  formData.append('file', raw)

  try {
    await skillsApi.upload(formData)
    ElMessage.success('导入成功')
    loadSkills()
  } catch (error) {
    ElMessage.error('导入失败')
  }
}

onMounted(() => {
  loadSkills()
})
</script>

<style lang="scss" scoped>
.skills-page {
  padding: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
