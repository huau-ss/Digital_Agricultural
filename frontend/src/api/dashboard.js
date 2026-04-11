import api from '@/utils/request'

// 获取 Dashboard 汇总数据
export function getDashboardSummary() {
  return api.get('/data-analysis/dashboard/summary/')
}