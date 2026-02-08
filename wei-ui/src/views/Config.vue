<template>
  <div class="config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>系统配置</span>
          <el-button type="primary" @click="refreshConfig" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <div v-if="configTree.length" class="config-tree">
        <el-tree
          :data="configTree"
          :props="treeProps"
          node-key="key"
          default-expand-all
          highlight-current
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span class="node-key">{{ node.label }}</span>
              <span class="node-value" v-if="data.value !== undefined && data.value !== null">
                <el-tag :type="getValueType(data.value)" size="small">{{ formatValue(data.value) }}</el-tag>
              </span>
              <el-tag 
                v-if="data.modifiable" 
                type="success" 
                size="small" 
                effect="dark"
                class="modifiable-tag"
              >
                可修改
              </el-tag>
            </div>
          </template>
        </el-tree>
      </div>

      <el-empty v-else description="暂无配置数据" />

      <div class="config-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="配置文件路径">{{ configPath }}</el-descriptions-item>
          <el-descriptions-item label="配置节点总数">{{ totalNodes }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>配置说明</span>
        </div>
      </template>
      <el-alert
        title="配置管理规则"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <ul class="info-list">
            <li>所有配置存储在 <code>config.yml</code> 文件中</li>
            <li><strong>virtual_models</strong> 节点：可通过后台管理API进行增删改查</li>
            <li><strong>其他节点</strong>：仅可修改值，不可修改结构</li>
            <li>任何结构性修改必须通过配置文件手动完成</li>
            <li>配置修改后系统会自动热重载</li>
          </ul>
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getConfigTree, type ConfigNode } from '@/api/config'

interface TreeNode {
  key: string
  label: string
  value?: any
  children?: TreeNode[]
  modifiable?: boolean
}

const loading = ref(false)
const configTree = ref<TreeNode[]>([])
const configPath = ref('')
const totalNodes = ref(0)

const treeProps = {
  children: 'children',
  label: 'label'
}

const transformConfigNode = (node: ConfigNode): TreeNode => {
  const treeNode: TreeNode = {
    key: node.key,
    label: node.key,
    value: node.value,
    modifiable: node.modifiable
  }

  if (node.children && node.children.length > 0) {
    treeNode.children = node.children.map(child => transformConfigNode(child as ConfigNode))
  }

  return treeNode
}

const getValueType = (value: any): string => {
  if (value === null) return 'info'
  if (typeof value === 'boolean') return value ? 'success' : 'danger'
  if (typeof value === 'number') return 'warning'
  if (typeof value === 'string') return 'primary'
  if (Array.isArray(value)) return 'info'
  return 'info'
}

const formatValue = (value: any): string => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'string') {
    return value.length > 50 ? value.slice(0, 50) + '...' : value
  }
  if (Array.isArray(value)) return `[${value.length} items]`
  if (typeof value === 'object') {
    const str = JSON.stringify(value)
    return str.length > 50 ? str.slice(0, 50) + '...' : str
  }
  return String(value)
}

const fetchConfig = async () => {
  loading.value = true
  try {
    const data = await getConfigTree()
    configPath.value = data.config_path
    totalNodes.value = data.total_nodes
    
    if (data.tree && data.tree.children) {
      configTree.value = data.tree.children.map(child => transformConfigNode(child))
    }
  } catch (error) {
    console.error('Fetch config error:', error)
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const refreshConfig = () => {
  fetchConfig()
  ElMessage.success('配置已刷新')
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped lang="scss">
.config-container {
  padding: 20px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.config-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.config-tree {
  max-height: 600px;
  overflow-y: auto;
  margin-bottom: 20px;
  
  :deep(.el-tree) {
    background: transparent;
  }
}

.config-info {
  margin-top: 20px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  
  .node-key {
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
  
  .node-value {
    .el-tag {
      font-family: monospace;
    }
  }
  
  .modifiable-tag {
    margin-left: auto;
  }
}

.info-card {
  .info-list {
    margin: 0;
    padding-left: 20px;
    
    li {
      margin: 8px 0;
      line-height: 1.6;
    }
    
    code {
      background: var(--el-fill-color);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
    }
  }
}

@media (max-width: 1200px) {
  .config-container {
    grid-template-columns: 1fr;
  }
}
</style>