import { request } from './request'

export interface SystemOverview {
  total_virtual_models: number
  total_routes: number
  databases: Record<string, string>
  services_status: Record<string, string>
}

export interface RecentActivity {
  recent_logs_24h: number
  recent_errors_24h: number
  last_error: {
    timestamp: string
    message: string
    source: string
    level: string
  } | null
}

export interface DashboardOverview {
  overview: SystemOverview
  activity: RecentActivity
  timestamp: string
}

export interface HourlyStat {
  hour: string
  system_logs: number
  operation_logs: number
  total: number
}

export interface DashboardStats {
  hourly_distribution: HourlyStat[]
  level_distribution: Record<string, number>
  top_sources: Array<{ source: string; count: number }>
}

export interface ServiceStatus {
  status: string
  connected: boolean
  error?: string
  [key: string]: any
}

export interface ServicesStatus {
  mongodb: ServiceStatus
  redis: ServiceStatus
  qdrant: ServiceStatus
}

export interface VirtualModelSummary {
  name: string
  description: string
  route_count: number
  enabled: boolean
  routes: Array<{
    provider: string
    model: string
    weight: number
  }>
}

export const getDashboardOverview = async (): Promise<DashboardOverview> => {
  const res = await request.get('/dashboard/overview')
  return res.data.data
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const res = await request.get('/dashboard/stats')
  return res.data.data
}

export const getServicesStatus = async (): Promise<ServicesStatus> => {
  const res = await request.get('/dashboard/services')
  return res.data.data
}

export const getVirtualModelsSummary = async (): Promise<{
  models: VirtualModelSummary[]
  total: number
  enabled: number
}> => {
  const res = await request.get('/dashboard/virtual-models')
  return res.data.data
}
