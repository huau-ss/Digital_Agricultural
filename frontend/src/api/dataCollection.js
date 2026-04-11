import request from '@/utils/request'

// 获取农产品列表
export function getProducts(params) {
  return request({
    url: '/data-collection/products/',
    method: 'get',
    params
  })
}

// 获取单个产品
export function getProduct(id) {
  return request({
    url: `/data-collection/products/${id}/`,
    method: 'get'
  })
}

// 获取仪表盘摘要数据
export function getDashboardSummary() {
  return request({
    url: '/data-collection/visualization/dashboard_summary/',
    method: 'get'
  })
}

// 获取价格走势数据
export function getPriceTrend(params) {
  return request({
    url: '/data-collection/visualization/price_trend/',
    method: 'get',
    params
  })
}

// 获取按市场分组的价格走势
export function getPriceTrendByMarket(params) {
  return request({
    url: '/data-collection/visualization/price_trend_by_market/',
    method: 'get',
    params
  })
}

// 获取省份热力图数据
export function getProvinceHeatmap(params) {
  return request({
    url: '/data-collection/visualization/province_heatmap/',
    method: 'get',
    params
  })
}

// 获取产品对比数据
export function getProductComparison(params) {
  return request({
    url: '/data-collection/visualization/product_comparison/',
    method: 'get',
    params
  })
}

// 获取清洗后价格数据列表
export function getCleanedPrices(params) {
  return request({
    url: '/data-collection/cleaned-prices/',
    method: 'get',
    params
  })
}

// 获取清洗后数据统计
export function getCleanedPricesStatistics() {
  return request({
    url: '/data-collection/cleaned-prices/statistics/',
    method: 'get'
  })
}

// 获取异常值列表
export function getOutliers(params) {
  return request({
    url: '/data-collection/cleaned-prices/outliers/',
    method: 'get',
    params
  })
}

// 获取市场价格对比
export function getMarketComparison(params) {
  return request({
    url: '/data-collection/cleaned-prices/market_comparison/',
    method: 'get',
    params
  })
}

// 获取同一产品在不同地区的价格对比
export function getRegionComparison(params) {
  return request({
    url: '/data-collection/visualization/region_comparison/',
    method: 'get',
    params
  })
}
