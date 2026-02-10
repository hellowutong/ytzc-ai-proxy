import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RSSFeed, RSSArticle } from '@/types'

export const useRSSStore = defineStore('rss', () => {
  // State
  const feeds = ref<RSSFeed[]>([])
  const articles = ref<RSSArticle[]>([])
  const loading = ref(false)

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

  async function fetchArticles(feedId?: string) {
    try {
      const url = feedId
        ? `/admin/ai/v1/rss/articles?feed_id=${feedId}`
        : '/admin/ai/v1/rss/articles'
      const response = await fetch(url)
      const result = await response.json()
      if (result.code === 200) {
        articles.value = result.data.items
      }
    } catch (error) {
      console.error('Failed to fetch articles:', error)
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
    loading,
    fetchFeeds,
    fetchArticles,
    createFeed,
    updateFeed,
    deleteFeed,
    fetchFeedNow,
    importOPML
  }
})
