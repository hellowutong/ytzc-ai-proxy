import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { VirtualModel, ModelConfig, KnowledgeConfig, WebSearchConfig } from '@/types'

export const useModelStore = defineStore('models', () => {
  // State
  const models = ref<VirtualModel[]>([])
  const currentModel = ref<VirtualModel | null>(null)
  const loading = ref(false)

  // Getters
  const enabledModels = computed(() => models.value.filter(m => m.use))
  const modelNames = computed(() => models.value.map(m => m.name))

  // Actions
  async function fetchModels() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/virtual-models')
      const result = await response.json()
      if (result.code === 200) {
        models.value = result.data
      }
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      loading.value = false
    }
  }

  async function createModel(model: Omit<VirtualModel, 'proxy_key'>) {
    try {
      const response = await fetch('/admin/ai/v1/virtual-models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(model)
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchModels()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to create model:', error)
      return false
    }
  }

  async function updateModel(name: string, model: Partial<VirtualModel>) {
    try {
      const response = await fetch(`/admin/ai/v1/virtual-models/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(model)
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchModels()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to update model:', error)
      return false
    }
  }

  async function deleteModel(name: string) {
    try {
      const response = await fetch(`/admin/ai/v1/virtual-models/${name}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchModels()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete model:', error)
      return false
    }
  }

  async function switchModel(name: string, size: 'small' | 'big') {
    try {
      const response = await fetch(`/admin/ai/v1/virtual-models/${name}/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: size })
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchModels()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to switch model:', error)
      return false
    }
  }

  function setCurrentModel(model: VirtualModel) {
    currentModel.value = model
  }

  return {
    models,
    currentModel,
    loading,
    enabledModels,
    modelNames,
    fetchModels,
    createModel,
    updateModel,
    deleteModel,
    switchModel,
    setCurrentModel
  }
})
