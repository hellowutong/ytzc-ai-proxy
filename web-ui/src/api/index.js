import request from './request'

export const healthApi = {
  getHealth: () => request.get('/health'),
  getVersion: () => request.get('/version')
}

export const connectionsApi = {
  list: () => request.get('/api/v1/connections'),
  create: (data) => request.post('/api/v1/connections', data),
  update: (id, data) => request.put(`/api/v1/connections/${id}`, data),
  delete: (id) => request.delete(`/api/v1/connections/${id}`),
  test: (id) => request.post(`/api/v1/connections/${id}/test`),
  enable: (id) => request.put(`/api/v1/connections/${id}/enable`),
  disable: (id) => request.put(`/api/v1/connections/${id}/disable`)
}

export const providersApi = {
  list: () => request.get('/api/v1/providers'),
  reload: () => request.post('/api/v1/providers/reload')
}

export const sessionsApi = {
  list: (params) => request.get('/api/v1/sessions', { params }),
  get: (id) => request.get(`/api/v1/sessions/${id}`),
  create: (data) => request.post('/api/v1/sessions', data),
  update: (id, data) => request.put(`/api/v1/sessions/${id}`, data),
  delete: (id) => request.delete(`/api/v1/sessions/${id}`),
  deleteBatch: (ids) => request.post('/api/v1/sessions/batch-delete', { ids }),
  getMessages: (id) => request.get(`/api/v1/sessions/${id}/messages`),
  addMessage: (id, data) => request.post(`/api/v1/sessions/${id}/messages`, data),
  deleteMessage: (id, messageId) => request.delete(`/api/v1/sessions/${id}/messages/${messageId}`)
}

export const skillsApi = {
  list: (params) => request.get('/api/v1/skills', { params }),
  get: (id) => request.get(`/api/v1/skills/${id}`),
  create: (data) => request.post('/api/v1/skills', data),
  update: (id, data) => request.put(`/api/v1/skills/${id}`, data),
  delete: (id) => request.delete(`/api/v1/skills/${id}`),
  publish: (id) => request.post(`/api/v1/skills/${id}/publish`),
  rollback: (id, versionId) => request.post(`/api/v1/skills/${id}/rollback`, { version_id: versionId }),
  export: (id) => request.get(`/api/v1/skills/${id}/export`, { responseType: 'blob' }),
  upload: (formData) => request.post('/api/v1/skills/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  listVersions: (id) => request.get(`/api/v1/skills/${id}/versions`),
  getVersion: (id, versionId) => request.get(`/api/v1/skills/${id}/versions/${versionId}`),
  updateVersion: (id, versionId, data) => request.put(`/api/v1/skills/${id}/versions/${versionId}`, data)
}

export const vectorsApi = {
  listCollections: () => request.get('/api/v1/vectors/collections'),
  search: (params) => request.post('/api/v1/vectors/search', params),
  upsert: (data) => request.post('/api/v1/vectors/upsert', data),
  delete: (collection, ids) => request.post('/api/v1/vectors/delete', { collection, ids }),
  getCollectionInfo: (name) => request.get(`/api/v1/vectors/collections/${name}`)
}

export const backupsApi = {
  list: () => request.get('/api/v1/backups'),
  create: () => request.post('/api/v1/backups'),
  download: (id) => request.get(`/api/v1/backups/${id}/download`, { responseType: 'blob' }),
  delete: (id) => request.delete(`/api/v1/backups/${id}`),
  restore: (id) => request.post(`/api/v1/backups/${id}/restore`)
}

export const configApi = {
  get: () => request.get('/api/v1/config'),
  update: (data) => request.put('/api/v1/config', data)
}

export const baseskillsApi = {
  list: () => request.get('/api/v1/baseskills'),
  get: (id) => request.get(`/api/v1/baseskills/${id}`),
  create: (data) => request.post('/api/v1/baseskills', data),
  update: (id, data) => request.put(`/api/v1/baseskills/${id}`, data),
  delete: (id) => request.delete(`/api/v1/baseskills/${id}`),
  enable: (id) => request.put(`/api/v1/baseskills/${id}/enable`),
  disable: (id) => request.put(`/api/v1/baseskills/${id}/disable`),
  reload: () => request.post('/api/v1/baseskills/reload')
}

export const logsApi = {
  get: (params) => request.get('/api/v1/logs', { params })
}

export const filesApi = {
  list: (skillId) => request.get(`/api/v1/files/${skillId}`),
  read: (skillId, filePath) => request.get(`/api/v1/files/${skillId}/${filePath}`),
  update: (skillId, filePath, data) => request.put(`/api/v1/files/${skillId}/${filePath}`, data),
  delete: (skillId, filePath) => request.delete(`/api/v1/files/${skillId}/${filePath}`)
}
