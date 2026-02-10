<template>
  <div class="skills">
    <el-row :gutter="20">
      <!-- Category Tree -->
      <el-col :span="6">
        <el-card class="category-card">
          <template #header>
            <span>Skill分类</span>
          </template>
          
          <el-tree
            :data="categoryTree"
            :props="{ label: 'name', children: 'children' }"
            @node-click="handleNodeClick"
            highlight-current
            default-expand-all
          />
        </el-card>
      </el-col>

      <!-- Skill Detail -->
      <el-col :span="18">
        <el-card class="detail-card" v-loading="skillStore.loading">
          <template #header>
            <div class="detail-header">
              <span>{{ selectedSkill?.name || '请选择Skill' }}</span>
              <el-button-group v-if="selectedSkill">
                <el-button @click="handleReloadSkill">
                  <el-icon><Refresh /></el-icon>重载
                </el-button>
                <el-button @click="showLogs">
                  <el-icon><Document /></el-icon>日志
                </el-button>
              </el-button-group>
            </div>
          </template>
          
          <div v-if="selectedSkill" class="skill-detail">
            <!-- System Default Skill -->
            <div class="skill-section">
              <h4>系统默认Skill</h4>
              <el-form label-width="120px">
                <el-form-item label="启用">
                  <el-switch v-model="skillConfig.system_enabled" />
                </el-form-item>
                <el-form-item label="版本">
                  <el-select v-model="skillConfig.system_version">
                    <el-option label="v1" value="v1" />
                    <el-option label="v2" value="v2" />
                    <el-option label="v3" value="v3" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button @click="viewSkillContent('system')">查看SKILL.md</el-button>
                </el-form-item>
              </el-form>
            </div>

            <el-divider />

            <!-- Custom Skill -->
            <div class="skill-section">
              <h4>自定义Skill</h4>
              <el-form label-width="120px">
                <el-form-item label="启用">
                  <el-switch v-model="skillConfig.custom_enabled" />
                </el-form-item>
                <el-form-item label="版本">
                  <el-select v-model="skillConfig.custom_version">
                    <el-option label="v1" value="v1" />
                    <el-option label="v2" value="v2" />
                    <el-option label="v3" value="v3" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="editSkillContent">编辑Skill</el-button>
                </el-form-item>
              </el-form>
            </div>

            <el-divider />

            <!-- Actions -->
            <div class="skill-actions">
              <el-button type="primary" @click="saveSkillConfig">保存配置</el-button>
            </div>
          </div>
          
          <el-empty v-else description="请从左侧选择Skill分类" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Skill Editor Dialog -->
    <SkillEditorDialog
      v-model="showEditor"
      :category="selectedSkill?.category"
      :name="selectedSkill?.name"
      @save="handleSaveSkill"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Document } from '@element-plus/icons-vue'
import { useSkillStore } from '@/stores'
import type { Skill } from '@/types'
import SkillEditorDialog from '@/components/SkillEditorDialog.vue'

const router = useRouter()
const skillStore = useSkillStore()

const selectedSkill = ref<Skill | null>(null)
const showEditor = ref(false)

const skillConfig = ref({
  system_enabled: false,
  system_version: 'v1',
  custom_enabled: false,
  custom_version: 'v1'
})

const categoryTree = computed(() => {
  const categories = [
    {
      name: 'router',
      label: '模型路由',
      children: []
    },
    {
      name: 'virtual_models',
      label: '虚拟模型',
      children: [
        { name: 'virtual_models/knowledge', label: '知识库' },
        { name: 'virtual_models/web_search', label: '联网搜索' }
      ]
    },
    {
      name: 'knowledge',
      label: '知识提取',
      children: []
    },
    {
      name: 'rss',
      label: 'RSS处理',
      children: []
    },
    {
      name: 'audio',
      label: '音频处理',
      children: []
    },
    {
      name: 'video',
      label: '视频处理',
      children: []
    },
    {
      name: 'text',
      label: '文本处理',
      children: []
    }
  ]
  return categories
})

const handleNodeClick = (data: any) => {
  const skill = skillStore.skills.find(s => s.category === data.name)
  if (skill) {
    selectedSkill.value = skill
    skillConfig.value.system_enabled = skill.type === 'system' || skill.enabled
    skillConfig.value.custom_enabled = skill.type === 'custom'
  }
}

const handleReloadSkill = async () => {
  if (!selectedSkill.value) return
  const success = await skillStore.reloadSkill(
    selectedSkill.value.category,
    selectedSkill.value.name
  )
  if (success) {
    ElMessage.success('Skill重载成功')
  } else {
    ElMessage.error('Skill重载失败')
  }
}

const showLogs = () => {
  router.push('/admin/logs')
}

const viewSkillContent = async (type: string) => {
  if (!selectedSkill.value) return
  const content = await skillStore.getSkillContent(
    selectedSkill.value.category,
    selectedSkill.value.name,
    type
  )
  if (content) {
    ElMessage.info('SKILL.md内容已加载')
  }
}

const editSkillContent = () => {
  showEditor.value = true
}

const saveSkillConfig = async () => {
  if (!selectedSkill.value) return
  const success = await skillStore.updateSkill(selectedSkill.value.id, {
    enabled: skillConfig.value.custom_enabled
  })
  if (success) {
    ElMessage.success('配置保存成功')
  } else {
    ElMessage.error('配置保存失败')
  }
}

const handleSaveSkill = async (content: string) => {
  if (!selectedSkill.value) return
  const success = await skillStore.saveSkillContent(
    selectedSkill.value.category,
    selectedSkill.value.name,
    content
  )
  if (success) {
    ElMessage.success('Skill保存成功')
    showEditor.value = false
  } else {
    ElMessage.error('Skill保存失败')
  }
}

onMounted(() => {
  skillStore.fetchSkills()
})
</script>

<style scoped>
.skills {
  padding: 0;
}

.category-card,
.detail-card {
  background: #252526;
  border: 1px solid #3C3C3C;
  height: calc(100vh - 140px);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-section {
  margin-bottom: 24px;
}

.skill-section h4 {
  color: #CCCCCC;
  margin-bottom: 16px;
  font-weight: 500;
}

.skill-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #3C3C3C;
  color: #CCCCCC;
}

:deep(.el-tree) {
  background: transparent;
  color: #CCCCCC;
}

:deep(.el-tree-node__content:hover) {
  background: #2D2D30;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #007ACC;
}
</style>
