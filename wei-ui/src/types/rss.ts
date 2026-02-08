// RSS API Types for AI Gateway Frontend

export interface RSSProject {
  name: string
  url: string
  enabled: boolean
  description?: string | null
  icon?: string | null
  last_fetch_at?: string | null
  fetch_count: number
  item_count: number
  error_count: number
  last_error?: string | null
  created_at: string
  updated_at: string
}

export interface RSSItem {
  _id: string
  project_name: string
  title: string
  link: string
  description?: string | null
  author?: string | null
  published_at?: string | null
  fetched_at: string
  status: string
  is_permanent: boolean
  extracted: boolean
  extraction_doc_id?: string | null
  read_duration: number
  read_at?: string | null
  tags: string[]
  categories: string[]
  word_count?: number | null
}

export interface RSSItemDetail extends RSSItem {
  content?: string | null
  enclosure_url?: string | null
  enclosure_type?: string | null
}

export interface RSSFetchResult {
  project_name: string
  success: boolean
  new_items: number
  updated_items: number
  error?: string | null
  duration_ms: number
}

export interface RSSFetchResponse {
  success: boolean
  results: RSSFetchResult[]
  total_new: number
  total_updated: number
  duration_ms: number
}

export interface RSSExtractResponse {
  success: boolean
  document_id?: string | null
  chunks_count?: number | null
  message: string
}

export interface RSSBatchResponse {
  success: boolean
  processed: number
  failed: number
  message: string
}

export interface RSSStats {
  total_projects: number
  active_projects: number
  total_items: number
  unread_items: number
  reading_items: number
  read_items: number
  extracted_items: number
  archived_items: number
  permanent_items: number
  temporary_items: number
  today_items: number
  week_items: number
  projects: Record<string, unknown>[]
  timeline: Record<string, unknown>[]
}

export interface RSSSearchResponse {
  items: RSSItem[]
  total: number
  page: number
  page_size: number
}
