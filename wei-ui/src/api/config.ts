import { request } from './request'

export interface ConfigNode {
  key: string
  path: string
  value: any
  type: string
  children?: ConfigNode[]
  description?: string
  editable: boolean
  modifiable: boolean
}

export interface ConfigTreeResponse {
  tree: ConfigNode
  config_path: string
  total_nodes: number
}

export const getConfigTree = async (): Promise<ConfigTreeResponse> => {
  const res = await request.get('/config')
  return res.data  // request interceptor already returns response.data
}

export const getConfigSection = async (path: string): Promise<{
  path: string
  value: any
  type: string
}> => {
  const res = await request.get(`/config/section/${path}`)
  return res.data
}

export const getVirtualModels = async (): Promise<{
  models: Record<string, any>
  count: number
  modifiable: boolean
}> => {
  const res = await request.get('/config/virtual-models')
  return res.data
}

export const getDatabaseConfig = async (): Promise<{
  mongodb: any
  redis: any
  qdrant: any
}> => {
  const res = await request.get('/config/databases')
  return res.data
}

export const getAppConfig = async (): Promise<any> => {
  const res = await request.get('/config/app')
  return res.data
}

export const getLoggingConfig = async (): Promise<{
  system: any
  operation: any
}> => {
  const res = await request.get('/config/logging')
  return res.data
}
