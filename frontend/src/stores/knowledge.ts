import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KnowledgeDoc } from '@/types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // State
  const docs = ref<KnowledgeDoc[]>([])
  const loading = ref(false)
  const config = ref({
    embedding_model: '',
    base_url: '',
    api_key: '',
    cron_expression: '*/30 * * * *',
    cron_enabled: false
  })

  // Actions
  async function fetchDocs() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/knowledge/docs')
      const result = await response.json()
      if (result.code === 200) {
        docs.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch docs:', error)
    } finally {
      loading.value = false
    }
  }

  async function uploadDoc(file: File, model: string, shared: boolean) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('model', model)
      formData.append('shared', String(shared))

      const response = await fetch('/admin/ai/v1/knowledge/docs/upload', {
        method: 'POST',
        body: formData
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to upload doc:', error)
      return false
    }
  }

  async function deleteDoc(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/knowledge/docs/${id}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchDocs()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete doc:', error)
      return false
    }
  }

  async function revectorizeDoc(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/knowledge/docs/${id}/revectorize`, {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to revectorize doc:', error)
      return false
    }
  }

  async function fetchConfig() {
    try {
      const response = await fetch('/admin/ai/v1/knowledge/config')
      const result = await response.json()
      if (result.code === 200) {
        config.value = { ...config.value, ...result.data }
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
    }
  }

  async function saveConfig() {
    try {
      const response = await fetch('/admin/ai/v1/knowledge/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config.value)
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to save config:', error)
      return false
    }
  }

  async function testVectorConnection() {
    try {
      const response = await fetch('/admin/ai/v1/knowledge/test-vector', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: config.value.embedding_model,
          base_url: config.value.base_url,
          api_key: config.value.api_key
        })
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to test vector connection:', error)
      return false
    }
  }

  return {
    docs,
    loading,
    config,
    fetchDocs,
    uploadDoc,
    deleteDoc,
    revectorizeDoc,
    fetchConfig,
    saveConfig,
    testVectorConnection
  }
})
