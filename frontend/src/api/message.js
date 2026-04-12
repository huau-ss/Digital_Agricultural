import api from '@/utils/request'

// 获取消息列表
export function getMessages(params) {
  return api.get('/auth/messages/', { params })
}

// 获取未读消息数量
export function getUnreadCount() {
  return api.get('/auth/messages/unread-count/')
}

// 标记消息已读
export function markMessageRead(data) {
  return api.post('/auth/messages/mark-read/', data)
}

// 标记所有消息已读
export function markAllMessagesRead() {
  return api.post('/auth/messages/mark-read/', {})
}

// 删除消息
export function deleteMessage(messageId) {
  return api.delete(`/auth/messages/delete/`, { data: { message_id: messageId } })
}
