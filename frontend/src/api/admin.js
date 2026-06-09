import api from '@/utils/request'

// ==================== 用户管理 ====================

export function getUserList(params) {
  return api.get('/auth/admin/users/', { params })
}

export function getUserStats() {
  return api.get('/auth/admin/users/stats/')
}

export function userAction(data) {
  return api.post('/auth/admin/users/action/', data)
}

// ==================== 系统设置 ====================

export function getAdminSettings() {
  return api.get('/data-analysis/admin/settings/')
}

export function updateAdminSettings(data) {
  return api.post('/data-analysis/admin/settings/', data)
}

// ==================== 数据管理 ====================

export function triggerDataCollection(params) {
  return api.post('/data-collection/trigger/collect/', params || {})
}

export function triggerDataCleaning(data) {
  return api.post('/data-collection/trigger/clean/', data)
}

export function getCleanedStats() {
  return api.get('/data-collection/cleaned-prices/statistics/')
}

// ==================== 模型管理 ====================

export function getModelRegistry() {
  return api.get('/data-analysis/admin/models/')
}

export function getModelDetail(productId) {
  return api.get(`/data-analysis/admin/models/${productId}/`)
}
