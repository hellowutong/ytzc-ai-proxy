<template>
  <div class="vectors-page">
    <div class="page-header">
      <h2>向量管理</h2>
      <div class="header-actions">
        <el-button type="danger" @click="handleBatchDelete" :disabled="selectedIds.length === 0">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button type="primary" @click="showUpsertDialog">
          <el-icon><Plus /></el-icon>
          添加向量
        </el-button>
      </div>
    </div>

    <el-card class="collection-card">
      <template #header>
        <span>向量集合</span>
      </template>
      <el-table :data="collections" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="集合名称" />
        <el-table-column prop="vectors_count" label="向量数量" width="120" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'green' ? 'success' : 'warning'">
              {{ row.status === 'green' ? '正常' : '构建中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewCollection(row)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button size="small" type="primary" @click="showSearchDialog(row)">
                <el-icon><Search /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click="deleteCollection(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="search-card" v-if="searchResults.length > 0">
      <template #header>
        <span>搜索结果</span>
      </template>
      <div class="search-results">
        <div v-for="(result, index) in searchResults" :key="index" class="result-item">
          <div class="result-score">相似度: {{ (result.score * 100).toFixed(2) }}%</div>
          <div class="result-content">{{ result.payload?.content || 'N/A' }}</div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="searchDialogVisible" title="向量搜索" width="600px">
      <el-form :model="searchForm" label-width="80px">
        <el-form-item label="集合">
          <el-select v-model="searchForm.collection" placeholder="选择集合" style="width: 100%">
            <el-option v-for="c in collections" :key="c.name" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="查询文本">
          <el-input v-model="searchForm.query" type="textarea" :rows="3" placeholder="输入查询文本" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="searchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="performSearch" :loading="searching">
          搜索
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="upsertDialogVisible" title="添加向量" width="600px">
      <el-form :model="upsertForm" label-width="80px">
        <el-form-item label="集合">
          <el-select v-model="upsertForm.collection" placeholder="选择集合" style="width: 100%">
            <el-option v-for="c in collections" :key="c.name" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="向量ID">
          <el-input v-model="upsertForm.id" placeholder="向量ID" />
        </el-form-item>
        <el-form-item label="向量值">
          <el-input v-model="upsertForm.vector" type="textarea" :rows="4" placeholder="[0.1, 0.2, 0.3, ...]" />
        </el-form-item>
        <el-form-item label="元数据">
          <el-input v-model="upsertForm.payload" type="textarea" :rows="3" placeholder='{"content": "文本内容"}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="upsertDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpsert" :loading="upserting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vectorsApi } from '@/api'

const collections = ref([])
const searchResults = ref([])
const loading = ref(false)
const searching = ref(false)
const upserting = ref(false)
const searchDialogVisible = ref(false)
const upsertDialogVisible = ref(false)
const selectedIds = ref([])

const searchForm = reactive({
  collection: '',
  query: ''
})

const upsertForm = reactive({
  collection: '',
  id: '',
  vector: '',
  payload: ''
})

async function loadCollections() {
  loading.value = true
  try {
    collections.value = await vectorsApi.listCollections()
  } catch (error) {
    ElMessage.error('加载集合失败')
  } finally {
    loading.value = false
  }
}

function showSearchDialog(row) {
  searchForm.collection = row.name
  searchForm.query = ''
  searchDialogVisible.value = true
}

async function performSearch() {
  if (!searchForm.collection || !searchForm.query) {
    ElMessage.warning('请填写查询条件')
    return
  }

  searching.value = true
  try {
    searchResults.value = await vectorsApi.search({
      collection: searchForm.collection,
      query: searchForm.query
    })
    ElMessage.success('搜索完成')
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

function showUpsertDialog() {
  upsertForm.collection = ''
  upsertForm.id = ''
  upsertForm.vector = ''
  upsertForm.payload = ''
  upsertDialogVisible.value = true
}

async function submitUpsert() {
  if (!upsertForm.collection || !upsertForm.vector) {
    ElMessage.warning('请填写必要信息')
    return
  }

  upserting.value = true
  try {
    await vectorsApi.upsert({
      collection: upsertForm.collection,
      id: upsertForm.id,
      vector: JSON.parse(upsertForm.vector),
      payload: upsertForm.payload ? JSON.parse(upsertForm.payload) : {}
    })
    ElMessage.success('添加成功')
    upsertDialogVisible.value = false
    loadCollections()
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    upserting.value = false
  }
}

function viewCollection(row) {
  ElMessage.info(`集合: ${row.name}, 向量数: ${row.vectors_count}`)
}

async function deleteCollection(row) {
  try {
    await ElMessageBox.confirm('确定删除此集合的所有数据?', '确认', { type: 'warning' })
    await vectorsApi.delete(row.name, [])
    ElMessage.success('删除成功')
    loadCollections()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的向量')
    return
  }

  try {
    const collection = collections.value[0]?.name
    if (collection) {
      await vectorsApi.delete(collection, selectedIds.value)
      ElMessage.success('批量删除成功')
    }
  } catch (error) {
    ElMessage.error('批量删除失败')
  }
}

onMounted(() => {
  loadCollections()
})
</script>

<style lang="scss" scoped>
.vectors-page {
  padding: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.collection-card, .search-card {
  margin-bottom: 20px;
}

.search-results {
  max-height: 400px;
  overflow-y: auto;

  .result-item {
    padding: 12px;
    border-bottom: 1px solid var(--border-color);

    &:last-child {
      border-bottom: none;
    }

    .result-score {
      font-size: 12px;
      color: var(--primary-color);
      margin-bottom: 8px;
    }

    .result-content {
      white-space: pre-wrap;
    }
  }
}
</style>
