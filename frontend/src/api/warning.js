import api from '@/utils/request'

// ============================================
// 价格预警 API
// 后端接口：backend/apps/data_analysis/warning_views.py
// ============================================

/**
 * 触发所有产品的价格预警检测
 * POST /api/data-analysis/warning/check/
 *
 * 返回：{ code: 200, message: '价格预警检测完成', data: { messages_generated: number } }
 */
export function triggerWarningCheck() {
    return api.post('/data-analysis/warning/check/')
}

/**
 * 检测单个产品的价格预警
 * POST /api/data-analysis/warning/check-product/
 *
 * @param {number} productId - 农产品ID
 * 返回：{ code: 200, message: '检测完成', data: { has_warning: boolean, warning_info: {...}, messages_sent: number } }
 */
export function checkProductWarning(productId) {
    return api.post('/data-analysis/warning/check-product/', {
        product_id: productId
    })
}

/**
 * 获取可检测预警的产品列表
 * GET /api/data-analysis/warning/products/
 *
 * 返回：{ code: 200, message: '获取成功', data: [{ id, name, category }, ...] }
 */
export function getWarningProducts() {
    return api.get('/data-analysis/warning/products/')
}

// ============================================
// 预警消息 API（复用 message.js 的接口）
// ============================================

/**
 * 获取预警消息列表（筛选 message_type = 'price_warning'）
 * GET /api/auth/messages/
 *
 * @param {object} params - 查询参数
 * @param {string} params.message_type - 消息类型，传入 'price_warning' 获取预警消息
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export function getWarningMessages(params) {
    return api.get('/auth/messages/', {
        params: {
            ...params,
            message_type: 'price_warning'
        }
    })
}

/**
 * 获取预警消息未读数量
 */
export function getWarningUnreadCount() {
    return api.get('/auth/messages/unread-count/', {
        params: { message_type: 'price_warning' }
    })
}

/**
 * 标记预警消息已读
 * @param {number} messageId - 消息ID
 */
export function markWarningRead(messageId) {
    return api.post('/auth/messages/mark-read/', {
        message_id: messageId,
        message_type: 'price_warning'
    })
}

/**
 * 标记所有预警消息已读
 */
export function markAllWarningsRead() {
    return api.post('/auth/messages/mark-read/', {
        message_type: 'price_warning'
    })
}
