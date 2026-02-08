import { request } from './request'
import type { AxiosResponse } from 'axios'
import type {
  RSSProject,
  RSSItem,
  RSSItemDetail,
  RSSFetchResponse,
  RSSExtractResponse,
  RSSBatchResponse,
  RSSStats,
  RSSSearchResponse
} from '@/types/rss'

const API_PREFIX = '/proxy/admin/rss'

// Projects
export async function listRSSProjects(): Promise<RSSProject[]> {
  const response: AxiosResponse<RSSProject[]> = await request.get(`${API_PREFIX}/projects`)
  return response.data
}

export async function createRSSProject(data: {
  name: string
  url: string
  enabled?: boolean
  description?: string
  icon?: string
}): Promise<RSSProject> {
  const response: AxiosResponse<RSSProject> = await request.post(`${API_PREFIX}/projects`, data)
  return response.data
}

export async function getRSSProject(name: string): Promise<RSSProject> {
  const response: AxiosResponse<RSSProject> = await request.get(`${API_PREFIX}/projects/${name}`)
  return response.data
}

export async function updateRSSProject(
  name: string,
  data: {
    description?: string
    icon?: string
  }
): Promise<RSSProject> {
  const response: AxiosResponse<RSSProject> = await request.put(`${API_PREFIX}/projects/${name}`, data)
  return response.data
}

// Items
export async function listRSSItems(params: {
  project_name?: string
  status?: string
  is_permanent?: boolean
  extracted?: boolean
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
} = {}): Promise<RSSItem[]> {
  const response: AxiosResponse<RSSItem[]> = await request.get(`${API_PREFIX}/items`, { params })
  return response.data
}

export async function getRSSItem(itemId: string): Promise<RSSItemDetail> {
  const response: AxiosResponse<RSSItemDetail> = await request.get(`${API_PREFIX}/items/${itemId}`)
  return response.data
}

export async function updateRSSItem(
  itemId: string,
  data: {
    status?: string
    is_permanent?: boolean
    tags?: string[]
    read_duration?: number
  }
): Promise<RSSItem> {
  const response: AxiosResponse<RSSItem> = await request.put(`${API_PREFIX}/items/${itemId}`, data)
  return response.data
}

export async function deleteRSSItem(itemId: string): Promise<{ success: boolean; message: string }> {
  const response: AxiosResponse<{ success: boolean; message: string }> = await request.delete(
    `${API_PREFIX}/items/${itemId}`
  )
  return response.data
}

// Actions
export async function markAsRead(
  itemId: string,
  duration?: number
): Promise<RSSItem> {
  const response: AxiosResponse<RSSItem> = await request.post(
    `${API_PREFIX}/items/${itemId}/read`,
    { duration }
  )
  return response.data
}

export async function extractToKnowledge(
  itemId: string,
  model?: string
): Promise<RSSExtractResponse> {
  const response: AxiosResponse<RSSExtractResponse> = await request.post(
    `${API_PREFIX}/items/${itemId}/extract`,
    { model }
  )
  return response.data
}

// Fetch
export async function fetchRSSFeeds(projectName?: string): Promise<RSSFetchResponse> {
  const response: AxiosResponse<RSSFetchResponse> = await request.post(
    `${API_PREFIX}/fetch`,
    { project_name: projectName }
  )
  return response.data
}

// Batch operations
export async function batchOperation(
  itemIds: string[],
  operation: 'read' | 'archive' | 'delete' | 'extract' | 'permanent' | 'unpermanent'
): Promise<RSSBatchResponse> {
  const response: AxiosResponse<RSSBatchResponse> = await request.post(`${API_PREFIX}/batch`, {
    item_ids: itemIds,
    operation
  })
  return response.data
}

// Stats
export async function getRSSStats(): Promise<RSSStats> {
  const response: AxiosResponse<RSSStats> = await request.get(`${API_PREFIX}/stats`)
  return response.data
}

// Search
export async function searchRSSItems(params: {
  query: string
  project_name?: string
  status?: string
  page?: number
  page_size?: number
}): Promise<RSSSearchResponse> {
  const response: AxiosResponse<RSSSearchResponse> = await request.post(`${API_PREFIX}/search`, params)
  return response.data
}

// Cleanup
export async function cleanupOldItems(days: number = 30): Promise<{
  success: boolean
  deleted_count: number
  message: string
}> {
  const response: AxiosResponse<{
    success: boolean
    deleted_count: number
    message: string
  }> = await request.post(`${API_PREFIX}/cleanup?days=${days}`)
  return response.data
}

// Helper functions
export function getStatusType(status: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const statusMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    'unread': 'danger',
    'reading': 'warning',
    'read': 'success',
    'extracted': 'info',
    'archived': ''
  }
  return statusMap[status] || ''
}

export function getStatusLabel(status: string): string {
  const statusMap: Record<string, string> = {
    'unread': '未读',
    'reading': '阅读中',
    'read': '已读',
    'extracted': '已提取',
    'archived': '已归档'
  }
  return statusMap[status] || status
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  } else {
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
  }
}

export function formatRelativeTime(date: Date | string | undefined): string {
  if (!date) return '-'
  
  const now = new Date()
  const then = new Date(date)
  const diff = now.getTime() - then.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return then.toLocaleDateString()
}

export function truncateText(text: string, maxLength: number = 200): string {
  if (!text || text.length <= maxLength) return text || ''
  return text.substring(0, maxLength) + '...'
}
