import api from '@/utils/request'

// 获取 Dashboard 汇总数据
export function getDashboardSummary() {
  return api.get('/data-analysis/dashboard/summary/')
}

// 获取监控产品列表
export function getMonitoredProducts() {
  return api.get('/data-collection/products/')
}

// 获取今日预警列表
export function getTodayWarnings() {
  return api.get('/data-analysis/warning/recent/')
}

// 获取供需信息列表
export function getSupplyDemandList(params) {
  return api.get('/decision-support/trade-info/', { params })
}