// Type definitions for AI Gateway

export interface KeywordConfig {
  enabled: boolean
  small_keywords: string[]
  big_keywords: string[]
}

// 新增：关键词规则
export interface KeywordRule {
  pattern: string
  target: 'small' | 'big'
}

// 新增：路由关键词配置
export interface RoutingKeywordsConfig {
  enable: boolean
  rules: KeywordRule[]
}

// 新增：路由Skill配置
export interface RoutingSkillConfig {
  enabled: boolean
  version: string
  custom: {
    enabled: boolean
    version: string
  }
}

// 新增：虚拟模型路由配置（替代全局router）
export interface RoutingConfig {
  keywords: RoutingKeywordsConfig
  skill: RoutingSkillConfig
}

export interface VirtualModel {
  name: string
  proxy_key: string
  current: 'small' | 'big'
  force_current: boolean
  use: boolean
  small: ModelConfig
  big: ModelConfig
  routing: RoutingConfig  // 新增：虚拟模型独立路由配置
  knowledge: KnowledgeConfig
  web_search: WebSearchConfig
  keyword_switching: KeywordConfig
}

export interface ModelConfig {
  model: string
  api_key: string
  base_url: string
}

export interface KnowledgeConfig {
  enabled: boolean
  shared: boolean
  system_default_skill: string | null  // null = 不选择系统Skill
  custom_skill: string | null          // null = 不选择自定义Skill
  use_system_default: boolean
  use_custom: boolean
}

export interface WebSearchConfig {
  enabled: boolean
  system_default_skill: string | null  // null = 不选择系统Skill
  custom_skill: string | null          // null = 不选择自定义Skill
  use_system_default: boolean
  use_custom: boolean
  targets: string[]
}

export interface Skill {
  id: string
  category: string
  name: string
  type: 'system' | 'custom'
  version: string
  enabled: boolean
  description?: string
}

export interface Conversation {
  id: string
  model: string
  messages: Message[]
  created_at: string
  updated_at: string
  metadata?: {                    // 新增: 对话元数据
    source?: 'webchat' | 'rss'
    title?: string
    article_id?: string
    article_title?: string
    feed_id?: string
    feed_name?: string
  }
}

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
}

export interface KnowledgeDoc {
  id: string
  filename: string
  type: string
  source: string
  vectorized: boolean
  created_at: string
}

export interface MediaFile {
  id: string
  filename: string
  type: 'video' | 'audio' | 'text'
  size: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  created_at: string
}

export interface RSSFeed {
  id: string
  name: string
  url: string
  enabled: boolean
  update_interval: string
  article_count: number
  retention_days: number
  permanent: boolean
  model: string
}

export interface RSSArticle {
  id: string
  subscription_id: string
  title: string
  url: string
  published_at: string
  content: string
  fetch_status: 'full' | 'summary' | 'failed'
  content_length: number
  is_read?: boolean
  fetched_at?: string
  author?: string
}

export interface LogEntry {
  id: string
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  module: string
  message: string
  details?: Record<string, unknown>
}

export interface DashboardStats {
  virtual_models: number
  today_conversations: number
  knowledge_docs: number
  media_queue: number
  rss_feeds: number
  system_status: 'healthy' | 'degraded' | 'unhealthy'
}

export interface SystemActivity {
  id: string
  timestamp: string
  type: string
  action: string
  status: 'success' | 'failed'
}

export interface ChatSettings {
  temperature: number
  max_tokens: number
  stream: boolean
  knowledge_enabled: boolean
  web_search_enabled: boolean
  dark_theme: boolean
  code_highlight: boolean
  show_thinking: boolean
}

export interface ConfigSection {
  [key: string]: unknown
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
