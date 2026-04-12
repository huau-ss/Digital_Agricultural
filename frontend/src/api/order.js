import api from '@/utils/request'

// 获取订单列表
export function getOrders(params) {
  return api.get('/decision-support/orders/my_orders/', { params })
}

// 获取订单详情
export function getOrderDetail(orderId) {
  return api.get(`/decision-support/orders/${orderId}/`)
}

// 创建订单（采购商购买）
export function createOrder(data) {
  return api.post('/decision-support/orders/', data)
}

// 接受订单（农户接受采购商的需求）
export function acceptOrder(data) {
  return api.post('/decision-support/orders/accept_order/', data)
}

// 确认订单（卖方）
export function confirmOrder(orderId) {
  return api.post(`/decision-support/orders/${orderId}/confirm/`)
}

// 发货（卖方）
export function shipOrder(orderId) {
  return api.post(`/decision-support/orders/${orderId}/ship/`)
}

// 完成订单（买方）
export function completeOrder(orderId) {
  return api.post(`/decision-support/orders/${orderId}/complete/`)
}

// 取消订单
export function cancelOrder(orderId) {
  return api.post(`/decision-support/orders/${orderId}/cancel/`)
}
