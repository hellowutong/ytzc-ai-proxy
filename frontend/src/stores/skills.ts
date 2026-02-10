import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Skill } from '@/types'

export const useSkillStore = defineStore('skills', () => {
  // State
  const skills = ref<Skill[]>([])
  const categories = ref<string[]>([
    'router',
    'virtual_models/knowledge',
    'virtual_models/web_search',
    'knowledge',
    'rss',
    'audio',
    'video',
    'text'
  ])
  const loading = ref(false)

  // Actions
  async function fetchSkills() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/skills')
      const result = await response.json()
      if (result.code === 200) {
        skills.value = result.data
      }
    } catch (error) {
      console.error('Failed to fetch skills:', error)
    } finally {
      loading.value = false
    }
  }

  async function updateSkill(id: string, data: Partial<Skill>) {
    try {
      const response = await fetch(`/admin/ai/v1/skills/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchSkills()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to update skill:', error)
      return false
    }
  }

  async function getSkillContent(category: string, name: string, type: string) {
    try {
      const response = await fetch(`/admin/ai/v1/skills/${category}/${name}/${type}/content`)
      const result = await response.json()
      if (result.code === 200) {
        return result.data
      }
      return null
    } catch (error) {
      console.error('Failed to get skill content:', error)
      return null
    }
  }

  async function saveSkillContent(category: string, name: string, content: string) {
    try {
      const response = await fetch(`/admin/ai/v1/skills/${category}/${name}/custom/content`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to save skill content:', error)
      return false
    }
  }

  async function reloadSkill(category: string, name: string) {
    try {
      const response = await fetch(`/admin/ai/v1/skills/${category}/${name}/reload`, {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to reload skill:', error)
      return false
    }
  }

  return {
    skills,
    categories,
    loading,
    fetchSkills,
    updateSkill,
    getSkillContent,
    saveSkillContent,
    reloadSkill
  }
})
