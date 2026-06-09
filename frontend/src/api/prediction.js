import request from '@/utils/request'

// 获取价格预测数据
export function getPricePrediction(params) {
  return request({
    url: '/data-analysis/prediction/',
    method: 'get',
    params
  })
}

// 获取可预测的产品列表
export function getPredictableProducts() {
  return request({
    url: '/data-analysis/prediction/products/',
    method: 'get'
  })
}

// 获取指定产品的可用地区列表
export function getProductMarkets(productId) {
  return request({
    url: '/data-analysis/prediction/markets/',
    method: 'get',
    params: { product_id: productId }
  })
}

// 获取模型信息
export function getModelInfo() {
  return request({
    url: '/data-analysis/prediction/model-info/',
    method: 'get'
  })
}
