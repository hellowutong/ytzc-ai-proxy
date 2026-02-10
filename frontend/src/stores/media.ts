import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MediaFile } from '@/types'

export const useMediaStore = defineStore('media', () => {
  // State
  const files = ref<MediaFile[]>([])
  const loading = ref(false)

  // Actions
  async function fetchFiles(type?: 'video' | 'audio' | 'text') {
    loading.value = true
    try {
      const url = type 
        ? `/admin/ai/v1/media?type=${type}`
        : '/admin/ai/v1/media'
      const response = await fetch(url)
      const result = await response.json()
      if (result.code === 200) {
        files.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch media files:', error)
    } finally {
      loading.value = false
    }
  }

  async function uploadFile(file: File, type: 'video' | 'audio' | 'text', config: Record<string, unknown>) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', type)
      formData.append('config', JSON.stringify(config))

      const response = await fetch('/admin/ai/v1/media/upload', {
        method: 'POST',
        body: formData
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to upload media:', error)
      return false
    }
  }

  async function downloadFromUrl(url: string, type: 'video' | 'audio', config: Record<string, unknown>) {
    try {
      const response = await fetch('/admin/ai/v1/media/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, type, config })
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to download media:', error)
      return false
    }
  }

  async function deleteFile(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/media/${id}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchFiles()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete media:', error)
      return false
    }
  }

  async function reprocessFile(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/media/${id}/reprocess`, {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to reprocess media:', error)
      return false
    }
  }

  return {
    files,
    loading,
    fetchFiles,
    uploadFile,
    downloadFromUrl,
    deleteFile,
    reprocessFile
  }
})
