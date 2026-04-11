import request from '@/utils/request'

export function getTradeInfoList(params) {
  return request({
    url: '/decision-support/trade-info/',
    method: 'get',
    params
  })
}

export function createTradeInfo(data) {
  return request({
    url: '/decision-support/trade-info/',
    method: 'post',
    data
  })
}

export function updateTradeInfo(id, data) {
  return request({
    url: `/decision-support/trade-info/${id}/`,
    method: 'put',
    data
  })
}

export function deleteTradeInfo(id) {
  return request({
    url: `/decision-support/trade-info/${id}/`,
    method: 'delete'
  })
}

export function getMyPosts(params) {
  return request({
    url: '/decision-support/trade-info/my_posts/',
    method: 'get',
    params
  })
}

export function completeTradeInfo(id) {
  return request({
    url: `/decision-support/trade-info/${id}/complete/`,
    method: 'post'
  })
}

export function cancelTradeInfo(id) {
  return request({
    url: `/decision-support/trade-info/${id}/cancel/`,
    method: 'post'
  })
}
