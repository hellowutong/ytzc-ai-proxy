import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfigStore = defineStore('config', () => {
  // State
  const config = ref<Record<string, unknown>>({})
  const rawYaml = ref('')
  const loading = ref(false)

  // Actions
  async function fetchConfig() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/config')
      const result = await response.json()
      if (result.code === 200) {
        config.value = result.data
        rawYaml.value = result.data._raw || ''
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      loading.value = false
    }
  }

  async function updateConfig(path: string, value: unknown) {
    try {
      const response = await fetch('/admin/ai/v1/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, value })
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchConfig()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to update config:', error)
      return false
    }
  }

  async function saveRawYaml(yaml: string) {
    try {
      const response = await fetch('/admin/ai/v1/config/raw', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml })
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchConfig()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to save config:', error)
      return false
    }
  }

  async function reloadConfig() {
    try {
      const response = await fetch('/admin/ai/v1/config/reload', {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to reload config:', error)
      return false
    }
  }

  function getConfigValue(path: string): unknown {
    const keys = path.split('.')
    let value: unknown = config.value
    for (const key of keys) {
      if (value && typeof value === 'object') {
        value = (value as Record<string, unknown>)[key]
      } else {
        return undefined
      }
    }
    return value
  }

  return {
    config,
    rawYaml,
    loading,
    fetchConfig,
    updateConfig,
    saveRawYaml,
    reloadConfig,
    getConfigValue
  }
})
