/**
 * Virtual Models API Client
 * 
 * Provides CRUD operations for virtual model management
 * Base URL: /proxy/admin/virtual-models
 */

import { request } from './request'
import type { AxiosResponse } from 'axios'

export interface ModelConfig {
  model: string
  api_key?: string
  base_url: string
  embedding_model?: string
}

export interface SkillConfig {
  enabled: boolean
  version: string
}

export interface CustomSkillConfig {
  enabled: boolean
  version: string
}

export interface VirtualModelSkillConfig {
  enabled: boolean
  version: string
  custom: CustomSkillConfig
}

export interface KnowledgeConfig {
  enabled: boolean
  shared: boolean
  skill: VirtualModelSkillConfig
}

export interface WebSearchConfig {
  enabled: boolean
  skill: VirtualModelSkillConfig
  target: any[]
}

export interface VirtualModel {
  proxy_key: string
  base_url: string
  current: 'small' | 'big'
  force_current?: boolean
  use: boolean
  small: ModelConfig
  big: ModelConfig
  knowledge: KnowledgeConfig
  web_search: WebSearchConfig
}

export interface VirtualModelSummary {
  name: string
  enabled: boolean
  current: string
  force_current: boolean
  base_url: string
  small_model: string
  big_model: string
  knowledge_enabled: boolean
  web_search_enabled: boolean
}

export interface VirtualModelListResponse {
  models: VirtualModelSummary[]
  total: number
  enabled: number
}

export interface VirtualModelStats {
  model_name: string
  last_24h: {
    total_requests: number
    errors: number
    success_rate: number
  }
  config: {
    enabled: boolean
    current: string
    knowledge: boolean
    web_search: boolean
  }
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
}

/**
 * List all virtual models
 */
export const listVirtualModels = (): Promise<AxiosResponse<ApiResponse<VirtualModelListResponse>>> => {
  return request.get('/virtual-models')
}

/**
 * Get a specific virtual model
 */
export const getVirtualModel = (modelName: string): Promise<AxiosResponse<ApiResponse<{name: string, config: VirtualModel}>>> => {
  return request.get(`/virtual-models/${encodeURIComponent(modelName)}`)
}

/**
 * Create a new virtual model
 */
export const createVirtualModel = (
  modelName: string,
  config: VirtualModel
): Promise<AxiosResponse<ApiResponse<{name: string, config: VirtualModel}>>> => {
  return request.post('/virtual-models', {
    model_name: modelName,
    config: config
  })
}

/**
 * Update a virtual model
 */
export const updateVirtualModel = (
  modelName: string, 
  config: Partial<VirtualModel>
): Promise<AxiosResponse<ApiResponse<{name: string, config: VirtualModel}>>> => {
  return request.put(`/virtual-models/${encodeURIComponent(modelName)}`, config)
}

/**
 * Delete a virtual model
 */
export const deleteVirtualModel = (modelName: string): Promise<AxiosResponse<ApiResponse<void>>> => {
  return request.delete(`/virtual-models/${encodeURIComponent(modelName)}`)
}

/**
 * Enable/disable a virtual model
 */
export const toggleVirtualModel = (
  modelName: string, 
  enabled: boolean
): Promise<AxiosResponse<ApiResponse<void>>> => {
  return request.post(`/virtual-models/${encodeURIComponent(modelName)}/enable`, { enabled })
}

/**
 * Switch current model (small/big)
 */
export const switchCurrentModel = (
  modelName: string, 
  target: 'small' | 'big'
): Promise<AxiosResponse<ApiResponse<void>>> => {
  return request.post(`/virtual-models/${encodeURIComponent(modelName)}/switch-model`, { target })
}

/**
 * Get virtual model statistics
 */
export const getVirtualModelStats = (modelName: string): Promise<AxiosResponse<ApiResponse<VirtualModelStats>>> => {
  return request.get(`/virtual-models/${encodeURIComponent(modelName)}/stats`)
}

/**
 * Skill information
 */
export interface SkillInfo {
  id: string
  name: string
  category: string
  enabled: boolean
  version: string
  has_custom: boolean
  custom_version?: string
}

/**
 * Search target information
 */
export interface SearchTargetInfo {
  id: string
  name: string
  enabled: boolean
  description?: string
}

/**
 * Get available skills
 */
export const getSkills = (): Promise<AxiosResponse<{success: boolean, message: string, data: SkillInfo[]}>> => {
  return request.get('/config/skills')
}

/**
 * Get available search targets
 */
export const getSearchTargets = (): Promise<AxiosResponse<{success: boolean, message: string, data: SearchTargetInfo[]}>> => {
  return request.get('/config/search-targets')
}

/**
 * Get proxy URL for client connections
 */
export interface ProxyUrlResponse {
  proxy_url: string
  host: string
  port: number
}

export const getProxyUrl = (): Promise<AxiosResponse<{success: boolean, message: string, data: ProxyUrlResponse}>> => {
  return request.get('/config/proxy-url')
}

/**
 * Test model connection
 */
export interface TestConnectionParams {
  model: string
  base_url: string
  api_key?: string
}

export interface TestConnectionResult {
  success: boolean
  message: string
  connected: boolean
  status_code?: number
  error?: string
}

export const testConnection = (params: TestConnectionParams): Promise<AxiosResponse<TestConnectionResult>> => {
  return request.post('/virtual-models/test-connection', params)
}

export default {
  listVirtualModels,
  getVirtualModel,
  createVirtualModel,
  updateVirtualModel,
  deleteVirtualModel,
  toggleVirtualModel,
  switchCurrentModel,
  getVirtualModelStats,
  getSkills,
  getSearchTargets,
  getProxyUrl,
  testConnection
}
