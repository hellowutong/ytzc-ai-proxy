import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RSSFeed, RSSArticle } from '@/types'

export const useRSSStore = defineStore('rss', () => {
  // State
  const feeds = ref<RSSFeed[]>([])
  const articles = ref<RSSArticle[]>([])
  const loading = ref(false)
  const discoverFeeds = ref<Array<{name: string, url: string, icon: string, subscribers: string}>>([])

  // Actions
  async function fetchFeeds() {
    loading.value = true
    try {
      const response = await fetch('/admin/ai/v1/rss/feeds')
      const result = await response.json()
      if (result.code === 200) {
        feeds.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch feeds:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchArticles(feedId?: string, isRead?: boolean) {
    try {
      let url = '/admin/ai/v1/rss/articles'
      const params = new URLSearchParams()
      if (feedId) params.append('feed_id', feedId)
      if (isRead !== undefined) params.append('is_read', String(isRead))
      if (params.toString()) url += '?' + params.toString()
      
      const response = await fetch(url)
      const result = await response.json()
      if (result.code === 200) {
        articles.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch articles:', error)
    }
  }

  async function getArticle(id: string): Promise<RSSArticle | null> {
    try {
      const response = await fetch(`/admin/ai/v1/rss/articles/${id}`)
      const result = await response.json()
      if (result.code === 200) {
        return result.data
      }
      return null
    } catch (error) {
      console.error('Failed to get article:', error)
      return null
    }
  }

  async function markArticleRead(id: string, isRead: boolean = true): Promise<boolean> {
    try {
      const response = await fetch(`/admin/ai/v1/rss/articles/${id}/read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: isRead })
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to mark article read:', error)
      return false
    }
  }

  async function fetchDiscover(): Promise<Array<{name: string, url: string, icon: string, subscribers: string}>> {
    try {
      const response = await fetch('/admin/ai/v1/rss/discover')
      const result = await response.json()
      if (result.code === 200) {
        discoverFeeds.value = result.data.items
        return result.data.items
      }
      return []
    } catch (error) {
      console.error('Failed to fetch discover feeds:', error)
      return []
    }
  }

  async function createFeed(feed: Omit<RSSFeed, 'id' | 'article_count'>) {
    try {
      const response = await fetch('/admin/ai/v1/rss/feeds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feed)
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchFeeds()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to create feed:', error)
      return false
    }
  }

  async function updateFeed(id: string, feed: Partial<RSSFeed>) {
    try {
      const response = await fetch(`/admin/ai/v1/rss/feeds/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feed)
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchFeeds()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to update feed:', error)
      return false
    }
  }

  async function deleteFeed(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/rss/feeds/${id}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchFeeds()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete feed:', error)
      return false
    }
  }

  async function deleteArticle(id: string): Promise<boolean> {
    try {
      const response = await fetch(`/admin/ai/v1/rss/articles/${id}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        // 从本地列表中移除
        articles.value = articles.value.filter(a => a.id !== id)
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete article:', error)
      return false
    }
  }

  async function batchDeleteArticles(ids: string[]): Promise<{ success: boolean; count: number }> {
    try {
      const response = await fetch(`/admin/ai/v1/rss/articles/batch?ids=${ids.join(',')}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      if (result.code === 200) {
        // 从本地列表中移除已删除的文章
        articles.value = articles.value.filter(a => !ids.includes(a.id))
        return { success: true, count: result.data?.success_count || ids.length }
      }
      return { success: false, count: 0 }
    } catch (error) {
      console.error('Failed to batch delete articles:', error)
      return { success: false, count: 0 }
    }
  }

  async function fetchFeedNow(id: string) {
    try {
      const response = await fetch(`/admin/ai/v1/rss/feeds/${id}/fetch`, {
        method: 'POST'
      })
      const result = await response.json()
      return result.code === 200
    } catch (error) {
      console.error('Failed to fetch feed:', error)
      return false
    }
  }

  async function importOPML(file: File) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/admin/ai/v1/rss/import', {
        method: 'POST',
        body: formData
      })
      const result = await response.json()
      if (result.code === 200) {
        await fetchFeeds()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to import OPML:', error)
      return false
    }
  }

  return {
    feeds,
    articles,
    discoverFeeds,
    loading,
    fetchFeeds,
    fetchArticles,
    getArticle,
    markArticleRead,
    deleteArticle,
    batchDeleteArticles,
    fetchDiscover,
    createFeed,
    updateFeed,
    deleteFeed,
    fetchFeedNow,
    importOPML
  }
})
