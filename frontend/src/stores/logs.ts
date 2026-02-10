import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LogEntry } from '@/types'

export const useLogStore = defineStore('logs', () => {
  // State
  const logs = ref<LogEntry[]>([])
  const loading = ref(false)
  const filters = ref({
    level: [] as string[],
    module: '',
    start_time: '',
    end_time: '',
    keyword: ''
  })

  // Actions
  async function fetchLogs(type: 'system' | 'operation' | 'skill') {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (filters.value.level.length) {
        params.append('level', filters.value.level.join(','))
      }
      if (filters.value.module) {
        params.append('module', filters.value.module)
      }
      if (filters.value.start_time) {
        params.append('start_time', filters.value.start_time)
      }
      if (filters.value.end_time) {
        params.append('end_time', filters.value.end_time)
      }
      if (filters.value.keyword) {
        params.append('keyword', filters.value.keyword)
      }

      const response = await fetch(`/admin/ai/v1/logs/${type}?${params}`)
      const result = await response.json()
      if (result.code === 200) {
        logs.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    } finally {
      loading.value = false
    }
  }

  async function exportLogs(type: 'system' | 'operation' | 'skill', format: 'json' | 'csv') {
    try {
      const params = new URLSearchParams()
      params.append('format', format)
      
      const response = await fetch(`/admin/ai/v1/logs/${type}/export?${params}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `logs_${type}_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      return true
    } catch (error) {
      console.error('Failed to export logs:', error)
      return false
    }
  }

  function setFilters(newFilters: Partial<typeof filters.value>) {
    filters.value = { ...filters.value, ...newFilters }
  }

  return {
    logs,
    loading,
    filters,
    fetchLogs,
    exportLogs,
    setFilters
  }
})
