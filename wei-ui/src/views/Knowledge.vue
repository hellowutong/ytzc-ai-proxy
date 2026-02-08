<template>
  <div class="knowledge-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>知识库管理</h1>
        <p class="subtitle">管理文档、提取知识、构建智能问答系统</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>上传文档
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="4" v-for="stat in statsCards" :key="stat.key">
        <el-card class="stat-card" :body-style="{ padding: '15px' }">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Filter Bar -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="待处理" value="pending" />
            <el-option label="提取中" value="extracting" />
            <el-option label="已提取" value="extracted" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="processed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterForm.content_type" placeholder="全部类型" clearable style="width: 150px">
            <el-option label="文本" value="text" />
            <el-option label="PDF" value="pdf" />
            <el-option label="文档" value="doc" />
            <el-option label="图片" value="image" />
            <el-option label="视频" value="video" />
            <el-option label="音频" value="audio" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联模型">
          <el-select v-model="filterForm.model_id" placeholder="全部模型" clearable style="width: 180px">
            <el-option 
              v-for="model in virtualModels" 
              :key="model.name" 
              :label="model.name" 
              :value="model.name" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input 
            v-model="filterForm.search" 
            placeholder="搜索标题或内容" 
            clearable
            style="width: 250px"
            @keyup.enter="handleSearch"
          >
            <template #suffix>
              <el-icon @click="handleSearch" style="cursor: pointer"><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Documents Table -->
    <el-card class="table-card">
      <el-table 
        :data="documents" 
        v-loading="loading"
        stripe
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="doc-title">
              <el-icon class="doc-icon">
                <Document v-if="row.content_type === 'text'" />
                <Folder v-else-if="row.content_type === 'pdf'" />
                <Picture v-else-if="row.content_type === 'image'" />
                <VideoCamera v-else-if="row.content_type === 'video'" />
                <Microphone v-else-if="row.content_type === 'audio'" />
                <Document v-else />
              </el-icon>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="content_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ formatContentType(row.content_type) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ formatStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_id" label="关联模型" width="150">
          <template #default="{ row }">
            <span v-if="row.model_id">{{ row.model_id }}</span>
            <el-tag v-else-if="row.shared" type="success" size="small">共享</el-tag>
            <span v-else class="text-muted">未关联</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="chunk_count" label="知识块" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.chunk_count > 0" type="info" size="small">
              {{ row.chunk_count }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="word_count" label="字数" width="100" align="right">
          <template #default="{ row }">
            {{ row.word_count ? formatNumber(row.word_count) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="topics" label="主题" min-width="150">
          <template #default="{ row }">
            <el-tag 
              v-for="topic in row.topics || []" 
              :key="topic"
              size="small"
              class="topic-tag"
            >
              {{ topic }}
            </el-tag>
            <span v-if="!row.topics?.length" class="text-muted">未分类</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.status === 'pending' || row.status === 'extracted'" 
                type="primary" 
                size="small"
                @click.stop="handleExtract(row)"
                :loading="extractingId === row.id"
              >
                提取
              </el-button>
              <el-button 
                v-if="row.status === 'processed'" 
                type="success" 
                size="small"
                @click.stop="viewChunks(row)"
              >
                查看
              </el-button>
              <el-button 
                size="small"
                @click.stop="showDetail(row)"
              >
                详情
              </el-button>
              <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
                <el-button size="small">
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="download" v-if="row.file_path">
                      <el-icon><Download /></el-icon>下载文件
                    </el-dropdown-item>
                    <el-dropdown-item command="reprocess" v-if="row.status === 'processed'">
                      <el-icon><Refresh /></el-icon>重新处理
                    </el-dropdown-item>
                    <el-dropdown-item command="edit">
                      <el-icon><Edit /></el-icon>编辑
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="600px"
      destroy-on-close
    >
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            drag
            style="width: 100%"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持: TXT, PDF, DOC, MD, JPG, PNG, MP4, MP3 等格式，最大 100MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="文档标题">
          <el-input v-model="uploadForm.title" placeholder="默认使用文件名" />
        </el-form-item>
        
        <el-form-item label="关联模型">
          <el-select v-model="uploadForm.model_id" placeholder="选择关联模型" clearable style="width: 100%">
            <el-option 
              v-for="model in virtualModels" 
              :key="model.name" 
              :label="model.name" 
              :value="model.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="共享知识">
          <el-switch v-model="uploadForm.shared" />
          <span class="form-hint">开启后所有模型都可以使用此知识</span>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input v-model="uploadForm.tags" placeholder="用逗号分隔多个标签" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- Document Detail Dialog -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedDoc?.title || '文档详情'"
      width="800px"
      destroy-on-close
    >
      <el-descriptions :column="2" border v-if="selectedDoc">
        <el-descriptions-item label="ID">{{ selectedDoc.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedDoc.status)">
            {{ formatStatus(selectedDoc.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="类型">{{ formatContentType(selectedDoc.content_type) }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">
          {{ selectedDoc.file_size ? formatFileSize(selectedDoc.file_size) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="关联模型">
          {{ selectedDoc.model_id || (selectedDoc.shared ? '共享' : '未关联') }}
        </el-descriptions-item>
        <el-descriptions-item label="知识块">{{ selectedDoc.chunk_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="字数">{{ selectedDoc.word_count || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提取置信度">
          {{ selectedDoc.extraction_confidence ? (selectedDoc.extraction_confidence * 100).toFixed(1) + '%' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="主题" :span="2">
          <el-tag v-for="topic in selectedDoc.topics || []" :key="topic" size="small" class="topic-tag">
            {{ topic }}
          </el-tag>
          <span v-if="!selectedDoc.topics?.length">未分类</span>
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <el-tag v-for="tag in selectedDoc.tags || []" :key="tag" type="info" size="small" class="topic-tag">
            {{ tag }}
          </el-tag>
          <span v-if="!selectedDoc.tags?.length">无标签</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(selectedDoc.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ selectedDoc.updated_at ? formatDate(selectedDoc.updated_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容预览" :span="2">
          <div class="content-preview">
            <pre>{{ selectedDoc.content || '暂无内容（需要先提取知识）' }}</pre>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- Knowledge Query Dialog -->
    <el-dialog
      v-model="showQueryDialog"
      title="知识检索"
      width="900px"
      destroy-on-close
    >
      <el-form :model="queryForm" inline>
        <el-form-item label="查询内容" style="flex: 1;">
          <el-input 
            v-model="queryForm.query" 
            placeholder="输入问题或关键词，搜索相关知识..."
            style="width: 400px"
            @keyup.enter="submitQuery"
          >
            <template #append>
              <el-button @click="submitQuery" :loading="querying">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="相似度阈值">
          <el-slider v-model="queryForm.threshold" :min="0" :max="1" :step="0.05" style="width: 150px" />
        </el-form-item>
      </el-form>
      
      <div v-if="queryResults.length > 0" class="query-results">
        <h4>检索结果 ({{ queryResults.length }}条)</h4>
        <el-card v-for="(result, index) in queryResults" :key="index" class="result-card" shadow="hover">
          <div class="result-content">{{ result.content }}</div>
          <div class="result-meta">
            <el-tag size="small" type="info">相似度: {{ (result.score! * 100).toFixed(1) }}%</el-tag>
            <el-tag size="small" v-if="result.topic">主题: {{ result.topic }}</el-tag>
            <el-tag size="small" type="success">来源: {{ result.document_id }}</el-tag>
          </div>
        </el-card>
      </div>
      
      <el-empty v-else-if="queried" description="未找到相关知识" />
    </el-dialog>

    <!-- Floating Query Button -->
    <el-button 
      class="query-fab" 
      type="primary" 
      circle 
      size="large"
      @click="showQueryDialog = true"
    >
      <el-icon><Search /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Upload, Refresh, Search, Document, Folder, Picture,
  VideoCamera, Microphone, More, Download, Edit, Delete,
  UploadFilled
} from '@element-plus/icons-vue';
import type { UploadFile } from 'element-plus';
import {
  getDocuments, getDocument, deleteDocument,
  uploadFile, extractDocument, reprocessDocument, downloadDocument, queryKnowledge, getKnowledgeStats,
  type Document as DocType, type KnowledgeChunk, type DocumentStats
} from '../api/knowledge';
import { listVirtualModels, type VirtualModel } from '../api/virtualModels';

// Loading states
const loading = ref(false);
const uploading = ref(false);
const extractingId = ref<string | null>(null);
const querying = ref(false);

// Data
const documents = ref<DocType[]>([]);
const stats = ref<DocumentStats | null>(null);
const virtualModels = ref<VirtualModel[]>([]);
const selectedDoc = ref<DocType | null>(null);
const queryResults = ref<KnowledgeChunk[]>([]);
const queried = ref(false);

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
});

// Filter form
const filterForm = reactive({
  status: '',
  content_type: '',
  model_id: '',
  search: ''
});

// Upload form
const uploadForm = reactive({
  title: '',
  model_id: '',
  shared: false,
  tags: ''
});

const selectedFile = ref<File | null>(null);

// Query form
const queryForm = reactive({
  query: '',
  threshold: 0.76,
  limit: 5
});

// Dialog visibility
const showUploadDialog = ref(false);
const showDetailDialog = ref(false);
const showQueryDialog = ref(false);

// Statistics cards
const statsCards = computed(() => [
  { key: 'total', label: '总文档数', value: stats.value?.total_documents || 0 },
  { key: 'processed', label: '已处理', value: stats.value?.by_status?.processed || 0 },
  { key: 'pending', label: '待处理', value: stats.value?.by_status?.pending || 0 },
  { key: 'chunks', label: '知识块', value: stats.value?.total_chunks || 0 },
  { key: 'words', label: '总字数', value: formatNumber(stats.value?.total_words || 0) },
  { key: 'confidence', label: '平均置信度', value: stats.value?.avg_extraction_confidence ? (stats.value.avg_extraction_confidence * 100).toFixed(1) + '%' : '-' }
]);

// Methods
const loadDocuments = async () => {
  loading.value = true;
  try {
    const response = await getDocuments({
      status: filterForm.status || undefined,
      content_type: filterForm.content_type || undefined,
      model_id: filterForm.model_id || undefined,
      search: filterForm.search || undefined,
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    });
    documents.value = response.documents;
    pagination.total = response.total;
  } catch (error) {
    ElMessage.error('加载文档失败');
  } finally {
    loading.value = false;
  }
};

const loadStats = async () => {
  try {
    stats.value = await getKnowledgeStats();
  } catch (error) {
    console.error('加载统计失败:', error);
  }
};

const loadVirtualModels = async () => {
  try {
    const response = await listVirtualModels();
    virtualModels.value = response.data?.data?.models || response.data?.models || [];
  } catch (error) {
    console.error('加载模型失败:', error);
  }
};

const refreshData = () => {
  loadDocuments();
  loadStats();
};

const handleSearch = () => {
  pagination.page = 1;
  loadDocuments();
};

const resetFilter = () => {
  filterForm.status = '';
  filterForm.content_type = '';
  filterForm.model_id = '';
  filterForm.search = '';
  pagination.page = 1;
  loadDocuments();
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadDocuments();
};

const handleSizeChange = (size: number) => {
  pagination.pageSize = size;
  pagination.page = 1;
  loadDocuments();
};

const handleRowClick = (row: DocType) => {
  showDetail(row);
};

const showDetail = async (row: DocType) => {
  try {
    const doc = await getDocument(row.id!);
    selectedDoc.value = doc;
    showDetailDialog.value = true;
  } catch (error) {
    ElMessage.error('加载文档详情失败');
  }
};

const handleExtract = async (row: DocType) => {
  extractingId.value = row.id!;
  try {
    const result = await extractDocument(row.id!, {
      auto_classify: true
    });
    ElMessage.success(`知识提取完成，创建 ${result.chunks_created} 个知识块`);
    loadDocuments();
    loadStats();
  } catch (error) {
    ElMessage.error('知识提取失败');
  } finally {
    extractingId.value = null;
  }
};

const viewChunks = (row: DocType) => {
  showDetail(row);
};

const handleCommand = async (command: string, row: DocType) => {
  switch (command) {
    case 'download':
      try {
        const blob = await downloadDocument(row.id!);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = row.title;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        ElMessage.error('下载失败');
      }
      break;
    case 'reprocess':
      try {
        await ElMessageBox.confirm('确定要重新处理此文档吗？', '提示', { type: 'warning' });
        extractingId.value = row.id!;
        await reprocessDocument(row.id!, { auto_classify: true });
        ElMessage.success('重新处理已开始');
        loadDocuments();
      } catch (error: any) {
        if (error !== 'cancel') {
          ElMessage.error('重新处理失败');
        }
      } finally {
        extractingId.value = null;
      }
      break;
    case 'edit':
      ElMessage.info('编辑功能开发中');
      break;
    case 'delete':
      try {
        await ElMessageBox.confirm('确定要删除此文档吗？此操作不可恢复。', '确认删除', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        });
        await deleteDocument(row.id!);
        ElMessage.success('删除成功');
        loadDocuments();
        loadStats();
      } catch (error: any) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败');
        }
      }
      break;
  }
};

// Upload handlers
const handleFileChange = (file: UploadFile) => {
  selectedFile.value = file.raw || null;
  if (file.name && !uploadForm.title) {
    uploadForm.title = file.name;
  }
};

const handleFileRemove = () => {
  selectedFile.value = null;
};

const submitUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件');
    return;
  }
  
  uploading.value = true;
  try {
    const result = await uploadFile(selectedFile.value, {
      title: uploadForm.title,
      model_id: uploadForm.model_id || undefined,
      shared: uploadForm.shared,
      tags: uploadForm.tags
    });
    
    ElMessage.success('上传成功');
    showUploadDialog.value = false;
    
    // Reset form
    selectedFile.value = null;
    uploadForm.title = '';
    uploadForm.model_id = '';
    uploadForm.shared = false;
    uploadForm.tags = '';
    
    loadDocuments();
    loadStats();
  } catch (error) {
    ElMessage.error('上传失败');
  } finally {
    uploading.value = false;
  }
};

// Query handlers
const submitQuery = async () => {
  if (!queryForm.query.trim()) {
    ElMessage.warning('请输入查询内容');
    return;
  }
  
  querying.value = true;
  queried.value = false;
  try {
    const response = await queryKnowledge({
      query: queryForm.query,
      threshold: queryForm.threshold,
      limit: queryForm.limit
    });
    queryResults.value = response.results;
    queried.value = true;
  } catch (error) {
    ElMessage.error('查询失败');
  } finally {
    querying.value = false;
  }
};

// Format helpers
const formatStatus = (status: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    extracting: '提取中',
    extracted: '已提取',
    processing: '处理中',
    processed: '已完成',
    failed: '失败'
  };
  return map[status] || status;
};

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    extracting: 'warning',
    extracted: 'warning',
    processing: 'warning',
    processed: 'success',
    failed: 'danger'
  };
  return map[status] || 'info';
};

const formatContentType = (type: string) => {
  const map: Record<string, string> = {
    text: '文本',
    pdf: 'PDF',
    doc: '文档',
    image: '图片',
    video: '视频',
    audio: '音频',
    rss: 'RSS',
    web: '网页'
  };
  return map[type] || type;
};

const formatDate = (date: string) => {
  if (!date) return '-';
  return new Date(date).toLocaleString('zh-CN');
};

const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  }
  return num.toLocaleString();
};

const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
  if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB';
  return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
};

// Lifecycle
onMounted(() => {
  loadDocuments();
  loadStats();
  loadVirtualModels();
});
</script>

<style scoped lang="scss">
.knowledge-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h1 {
    margin: 0;
    font-size: 24px;
    color: #303133;
  }
  
  .subtitle {
    margin: 5px 0 0;
    color: #909399;
    font-size: 14px;
  }
}

.stats-row {
  margin-bottom: 20px;
  
  .stat-card {
    text-align: center;
    
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #409EFF;
      margin-bottom: 5px;
    }
    
    .stat-label {
      font-size: 12px;
      color: #909399;
    }
  }
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  .doc-title {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .doc-icon {
      color: #909399;
    }
  }
  
  .topic-tag {
    margin-right: 5px;
    margin-bottom: 3px;
  }
  
  .text-muted {
    color: #909399;
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

.content-preview {
  max-height: 300px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  
  pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 13px;
    line-height: 1.6;
    color: #606266;
  }
}

.query-fab {
  position: fixed;
  right: 40px;
  bottom: 40px;
  z-index: 100;
  width: 56px;
  height: 56px;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.query-results {
  margin-top: 20px;
  
  h4 {
    margin-bottom: 15px;
    color: #303133;
  }
  
  .result-card {
    margin-bottom: 10px;
    
    .result-content {
      font-size: 14px;
      line-height: 1.6;
      color: #303133;
      margin-bottom: 10px;
      white-space: pre-wrap;
    }
    
    .result-meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
  }
}

.form-hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
