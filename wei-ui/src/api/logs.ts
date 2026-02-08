import { request } from './request'

export interface LogEntry {
  id: string
  timestamp: string
  level: string
  message: string
  source: string
  log_type: string
  metadata?: any
  trace_id?: string
  component?: string
  operation?: string
  status?: string
}

export interface LogPagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface LogsResponse {
  logs: LogEntry[]
  pagination: LogPagination
}

export interface LogStats {
  period_hours: number
  start_time: string
  end_time: string
  system_logs: {
    by_level: Record<string, number>
    total: number
  }
  operation_logs: {
    by_level: Record<string, number>
    total: number
  }
  recent_errors: Array<{
    id: string
    timestamp: string
    message: string
    source: string
  }>
}

export const getLogs = async (params: {
  log_type?: string
  level?: string
  source?: string
  start_time?: string
  end_time?: string
  search?: string
  page?: number
  page_size?: number
} = {}): Promise<LogsResponse> => {
  const res = await request.get('/logs', { params })
  return res.data.data
}

export const getSystemLogs = async (params: {
  level?: string
  component?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
} = {}): Promise<LogsResponse> => {
  const res = await request.get('/logs/system', { params })
  return res.data.data
}

export const getOperationLogs = async (params: {
  level?: string
  operation?: string
  status?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
} = {}): Promise<LogsResponse> => {
  const res = await request.get('/logs/operation', { params })
  return res.data.data
}

export const getLogStats = async (hours: number = 24): Promise<LogStats> => {
  const res = await request.get('/logs/stats', { params: { hours } })
  return res.data.data
}

export const clearOldLogs = async (days: number = 30): Promise<{
  deleted_count: number
  system_logs_deleted: number
  operation_logs_deleted: number
}> => {
  const res = await request.delete('/logs', { params: { days } })
  return res.data.data
}
