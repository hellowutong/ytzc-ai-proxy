import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardStats, SystemActivity } from '@/types'

export interface DependencyStatus {
  name: string
  icon: string
  color: string
  status: 'healthy' | 'warning' | 'unhealthy'
  statusText: string
  detail: string
  latency?: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref<DashboardStats>({
    virtual_models: 0,
    today_conversations: 0,
    knowledge_docs: 0,
    media_queue: 0,
    rss_feeds: 0,
    system_status: 'healthy'
  })
  
  const activities = ref<SystemActivity[]>([])
  const dependencies = ref<DependencyStatus[]>([])
  const loading = ref(false)

  // Actions
  async function fetchStats() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/dashboard/stats')
      const result = await response.json()
      if (result.code === 200) {
        stats.value = result.data
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchActivities() {
    try {
      const response = await fetch('/admin/ai/v1/dashboard/activities')
      const result = await response.json()
      if (result.code === 200) {
        activities.value = result.data
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error)
    }
  }

  async function fetchDependenciesStatus() {
    try {
      const response = await fetch('/admin/ai/v1/dashboard/dependencies')
      const result = await response.json()
      if (result.code === 200) {
        dependencies.value = result.data
      }
    } catch (error) {
      console.error('Failed to fetch dependencies status:', error)
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

  async function reloadSkills() {
    try {
      const response = await fetch('/admin/ai/v1/skills/reload', {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to reload skills:', error)
      return false
    }
  }

  return {
    stats,
    activities,
    dependencies,
    loading,
    fetchStats,
    fetchActivities,
    fetchDependenciesStatus,
    reloadConfig,
    reloadSkills
  }
})
