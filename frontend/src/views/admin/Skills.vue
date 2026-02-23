<template>
  <div class="skills">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="category-card">
          <template #header><span>Skill分类</span></template>
          <el-tree :data="categoryTree" :props="{ label: 'label', children: 'children' }" @node-click="handleNodeClick" highlight-current default-expand-all />
        </el-card>
      </el-col>
      <el-col :span="18">
        <div v-if="selectedCategory" class="skills-container">
          <el-card class="skills-section">
            <template #header><div class="section-header"><span>系统默认 Skills</span><el-tag type="info">只读</el-tag></div></template>
            <div class="skills-grid">
              <div v-for="skill in systemSkills" :key="skill.name" class="skill-card">
                <div class="skill-header"><h4>{{ skill.name }}</h4></div>
                <p class="skill-desc">{{ skill.description || '暂无描述' }}</p>
                <div class="skill-actions">
                  <el-select v-model="skill.current_version" size="small" style="width: 100px">
                    <el-option v-for="v in skill.all_versions" :key="v" :label="v" :value="v" />
                  </el-select>
                  <el-button size="small" @click="viewSkill(skill, 'system')">查看</el-button>
                </div>
              </div>
            </div>
          </el-card>
          <el-card class="skills-section">
            <template #header><div class="section-header"><span>自定义 Skills</span><el-button type="primary" size="small" @click="showCreateDialog"><el-icon><Plus /></el-icon>新增</el-button></div></template>
            <div v-if="customSkills.length === 0" class="empty-custom"><el-empty description="暂无自定义Skill"><el-button type="primary" @click="showCreateDialog">创建</el-button></el-empty></div>
            <div v-else class="skills-grid">
              <div v-for="skill in customSkills" :key="skill.name" class="skill-card custom">
                <div class="skill-header"><h4>{{ skill.name }}</h4><el-button type="danger" link size="small" @click="deleteSkill(skill)">删除</el-button></div>
                <p class="skill-desc">{{ skill.description || '暂无描述' }}</p>
                <div class="skill-actions">
                  <el-select v-model="skill.current_version" size="small" style="width: 100px"><el-option v-for="v in skill.all_versions" :key="v" :label="v" :value="v" /><el-option value="__new__" divided>+ 新增版本</el-option></el-select>
                  <el-button size="small" @click="viewSkill(skill, 'custom')">查看</el-button>
                  <el-button type="primary" size="small" @click="editSkill(skill)">编辑</el-button>
                </div>
              </div>
            </div>
          </el-card>
        </div>
        <el-empty v-else description="请从左侧选择Skill分类" />
      </el-col>
    </el-row>
    <!-- 对话框 -->
    <el-dialog v-model="showCreate" title="新增自定义Skill" width="500px">
      <el-form label-width="100px">
        <el-form-item label="Skill名称"><el-input v-model="newSkillForm.name" placeholder="如: MyRouter" /></el-form-item>
        <el-form-item label="初始版本"><el-input v-model="newSkillForm.version" placeholder="v1" /></el-form-item>
        <el-form-item label="复制来源"><el-radio-group v-model="newSkillForm.copyFrom"><el-radio label="blank">空白创建</el-radio><el-radio label="system">系统默认</el-radio></el-radio-group></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreate = false">取消</el-button><el-button type="primary" @click="createSkill" :disabled="!newSkillForm.name">创建</el-button></template>
    </el-dialog>
    <SkillEditorDialog v-model="showEditor" :category="selectedCategory" :skill="editingSkill" :mode="editorMode" @save="onSkillSaved" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import SkillEditorDialog from '@/components/SkillEditorDialog.vue'

// ==================== 类型定义 ====================
interface Skill {
  name: string
  is_system: boolean
  current_version: string
  all_versions?: string[]
  description: string
  type: string
  enabled: boolean
}

interface CategoryNode {
  label: string
  value: string
  children?: CategoryNode[]
}

// ==================== 分类树数据 ====================
const categoryTree = ref<CategoryNode[]>([
  {
    label: 'virtual_models (虚拟模型)',
    value: 'virtual_models',
    children: [
      { label: 'routing (模型路由)', value: 'virtual_models/routing' },
      { label: 'vm_knowledge (知识库)', value: 'virtual_models/vm_knowledge' },
      { label: 'web_search (联网搜索)', value: 'virtual_models/web_search' }
    ]
  },
  {
    label: 'knowledge (知识提取)',
    value: 'knowledge',
    children: [
      { label: 'topics (主题分类)', value: 'knowledge/topics' }
    ]
  },
  {
    label: 'media (媒体处理)',
    value: 'media',
    children: [
      { label: 'audio (音频处理)', value: 'media/audio' },
      { label: 'video (视频处理)', value: 'media/video' },
      { label: 'text (文本处理)', value: 'media/text' }
    ]
  },
  { label: 'rss (RSS处理)', value: 'rss' }
])

// ==================== 响应式状态 ====================
const selectedCategory = ref<string>('')
const systemSkills = ref<Skill[]>([])
const customSkills = ref<Skill[]>([])
const loading = ref(false)

// 新增Skill对话框
const showCreate = ref(false)
const newSkillForm = ref({
  name: '',
  version: 'v1',
  copyFrom: 'blank'
})

// 编辑器对话框
const showEditor = ref(false)
const editingSkill = ref<Skill | null>(null)
const editorMode = ref<'view' | 'edit'>('view')

// ==================== 方法 ====================

// 处理分类节点点击 - 所有节点点击都加载 skills（包括有子分类的节点）
const handleNodeClick = (data: CategoryNode) => {
  selectedCategory.value = data.value
  loadSkills(data.value)
}

// 加载Skills数据
const loadSkills = async (category: string) => {
  loading.value = true
  try {
    const response = await fetch(`/admin/ai/v1/skills/${category}`)
    const result = await response.json()
    
    if (result.code === 200) {
      const skills: Skill[] = result.data || []
      systemSkills.value = skills.filter(s => s.is_system)
      customSkills.value = skills.filter(s => !s.is_system)
    } else {
      ElMessage.error(result.message || '加载失败')
      useMockData()
    }
  } catch (error) {
    console.error('加载Skills失败:', error)
    ElMessage.error('加载失败，使用模拟数据')
    useMockData()
  } finally {
    loading.value = false
  }
}

// 模拟数据（开发测试用）
const useMockData = () => {
  systemSkills.value = [
    {
      name: 'keyword_router',
      is_system: true,
      current_version: 'v1',
      all_versions: ['v1'],
      description: '基于关键词的模型路由',
      type: 'rule-based',
      enabled: true
    },
    {
      name: 'intent_router',
      is_system: true,
      current_version: 'v1',
      all_versions: ['v1'],
      description: '基于意图识别的模型路由',
      type: 'llm-based',
      enabled: true
    }
  ]
  
  customSkills.value = [
    {
      name: 'MyRouter',
      is_system: false,
      current_version: 'v2',
      all_versions: ['v1', 'v2'],
      description: '我的自定义路由规则',
      type: 'hybrid',
      enabled: true
    }
  ]
}

// 显示创建对话框
const showCreateDialog = () => {
  if (!selectedCategory.value) {
    ElMessage.warning('请先选择Skill分类')
    return
  }
  newSkillForm.value = { name: '', version: 'v1', copyFrom: 'blank' }
  showCreate.value = true
}

// 创建Skill
const createSkill = async () => {
  if (!newSkillForm.value.name) {
    ElMessage.warning('请输入Skill名称')
    return
  }
  
  try {
    const response = await fetch(`/admin/ai/v1/skills/${selectedCategory.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newSkillForm.value.name,
        version: newSkillForm.value.version,
        copy_from: newSkillForm.value.copyFrom === 'system' ? 'system_default' : null
      })
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      ElMessage.success('创建成功')
      showCreate.value = false
      loadSkills(selectedCategory.value)
    } else {
      ElMessage.error(result.message || '创建失败')
    }
  } catch (error) {
    console.error('创建Skill失败:', error)
    ElMessage.error('创建失败')
    customSkills.value.push({
      name: newSkillForm.value.name,
      is_system: false,
      current_version: newSkillForm.value.version,
      all_versions: [newSkillForm.value.version],
      description: '新创建的自定义Skill',
      type: 'rule-based',
      enabled: true
    })
    showCreate.value = false
    ElMessage.success('创建成功（模拟）')
  }
}

// 删除Skill
const deleteSkill = async (skill: Skill) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 Skill "${skill.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await fetch(
      `/admin/ai/v1/skills/${selectedCategory.value}/${skill.name}`,
      { method: 'DELETE' }
    )
    
    const result = await response.json()
    
    if (result.code === 200) {
      ElMessage.success('删除成功')
      loadSkills(selectedCategory.value)
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除Skill失败:', error)
      const index = customSkills.value.findIndex(s => s.name === skill.name)
      if (index > -1) {
        customSkills.value.splice(index, 1)
        ElMessage.success('删除成功（模拟）')
      }
    }
  }
}

// 查看Skill
const viewSkill = (skill: Skill, _type: 'system' | 'custom') => {
  editingSkill.value = { ...skill }
  editorMode.value = 'view'
  showEditor.value = true
}

// 编辑Skill
const editSkill = (skill: Skill) => {
  editingSkill.value = { ...skill }
  editorMode.value = 'edit'
  showEditor.value = true
}

// Skill保存成功回调
const onSkillSaved = async (data: { content: string; version: string; isNewVersion: boolean }) => {
  if (!editingSkill.value || !selectedCategory.value) {
    showEditor.value = false
    return
  }

  const skillName = editingSkill.value.name
  
  try {
    let response
    
    if (data.isNewVersion) {
      // 创建新版本
      response = await fetch(`/admin/ai/v1/skills/${selectedCategory.value}/${skillName}/versions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_version: data.version,
          copy_from_version: editingSkill.value.current_version
        })
      })
      
      const result = await response.json()
      if (result.code !== 200) {
        ElMessage.error(result.message || '创建版本失败')
        return
      }
    }
    
    // 保存内容
    response = await fetch(`/admin/ai/v1/skills/${selectedCategory.value}/${skillName}?version=${data.version}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: data.content,
        save_mode: 'update_current'
      })
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      ElMessage.success('保存成功')
      showEditor.value = false
      loadSkills(selectedCategory.value)
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  if (categoryTree.value.length > 0) {
    const firstLeaf = categoryTree.value[0].children?.[0] || categoryTree.value[0]
    selectedCategory.value = firstLeaf.value
    loadSkills(firstLeaf.value)
  }
})

// 监听版本选择变化（新增版本）
watch(
  () => customSkills.value,
  (newSkills) => {
    newSkills.forEach(skill => {
      if (skill.current_version === '__new__') {
        editingSkill.value = { ...skill }
        showEditor.value = true
        skill.current_version = skill.all_versions?.[0] || 'v1'
      }
    })
  },
  { deep: true }
)
</script>

<style scoped>
.skills {
  padding: 20px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.category-card {
  height: calc(100vh - 160px);
}

.category-card :deep(.el-card__body) {
  padding: 10px;
  height: calc(100% - 60px);
  overflow-y: auto;
}

.skills-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skills-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header span {
  font-weight: 600;
  font-size: 16px;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 10px 0;
}

.skill-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  min-height: 160px;
}

.skill-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.skill-card.custom {
  border-left: 4px solid #409eff;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.skill-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.skill-desc {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.skill-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.empty-custom {
  padding: 40px 0;
}

@media (prefers-color-scheme: dark) {
  .skill-card {
    background: #2b2b2b;
    border-color: #444;
  }
  
  .skill-header h4 {
    color: #e0e0e0;
  }
  
  .skill-desc {
    color: #a0a0a0;
  }
}
</style>
