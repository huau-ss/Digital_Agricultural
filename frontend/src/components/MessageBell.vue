<template>
  <div class="message-bell">
    <el-popover
      placement="bottom-end"
      :width="380"
      trigger="click"
      @show="fetchMessages"
    >
      <template #reference>
        <div class="bell-container">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-icon :size="22"><Bell /></el-icon>
          </el-badge>
        </div>
      </template>

      <div class="message-popover">
        <div class="popover-header">
          <span class="header-title">预警消息</span>
          <div class="header-actions">
            <el-button
              v-if="unreadCount > 0"
              type="primary"
              link
              size="small"
              @click="handleMarkAllRead"
            >
              全部已读
            </el-button>
          </div>
        </div>

        <div class="message-list" v-loading="loading">
          <template v-if="messages.length > 0">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message-item"
              :class="{ unread: !msg.is_read }"
              @click="handleMessageClick(msg)"
            >
              <div class="message-icon">
                <el-tag
                  :type="getPriorityType(msg.priority)"
                  size="small"
                  effect="dark"
                >
                  {{ getTypeIcon(msg.message_type) }}
                </el-tag>
              </div>
              <div class="message-content">
                <div class="message-title">{{ msg.title }}</div>
                <div class="message-text">{{ truncateContent(msg.content) }}</div>
                <div class="message-meta">
                  <span class="message-time">{{ msg.time_ago }}前</span>
                  <el-tag
                    v-if="msg.price_change_percent"
                    :type="getChangeType(msg.price_change_percent)"
                    size="small"
                  >
                    {{ formatChangePercent(msg.price_change_percent) }}
                  </el-tag>
                </div>
              </div>
              <div class="message-status">
                <span v-if="!msg.is_read" class="unread-dot"></span>
              </div>
            </div>
          </template>
          <el-empty
            v-else
            description="暂无消息"
            :image-size="60"
          />
        </div>

        <div class="popover-footer" v-if="messages.length > 0">
          <router-link to="/dashboard/messages" class="view-more">
            查看全部消息
          </router-link>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getMessages, getUnreadCount, markMessageRead, markAllMessagesRead } from '@/api/message'

const loading = ref(false)
const messages = ref([])
const unreadCount = ref(0)

const fetchMessages = async () => {
  loading.value = true
  try {
    const [msgRes, countRes] = await Promise.all([
      getMessages({ page_size: 10 }),
      getUnreadCount()
    ])

    if (msgRes && msgRes.results) {
      messages.value = msgRes.results
    } else if (msgRes && Array.isArray(msgRes)) {
      messages.value = msgRes
    }

    if (countRes && countRes.data) {
      unreadCount.value = countRes.data.unread_count || 0
    }
  } catch (error) {
    console.error('获取消息失败:', error)
  } finally {
    loading.value = false
  }
}

const handleMessageClick = async (msg) => {
  if (!msg.is_read) {
    try {
      await markMessageRead({ message_id: msg.id })
      msg.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
}

const handleMarkAllRead = async () => {
  try {
    await markAllMessagesRead()
    messages.value.forEach(msg => {
      msg.is_read = true
    })
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('标记全部已读失败:', error)
    ElMessage.error('操作失败')
  }
}

const getPriorityType = (priority) => {
  const typeMap = {
    urgent: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'info'
  }
  return typeMap[priority] || 'info'
}

const getTypeIcon = (type) => {
  const iconMap = {
    price_warning: '📊',
    price_alert: '📈',
    system: '🔔',
    order: '📦'
  }
  return iconMap[type] || '📌'
}

const getChangeType = (percent) => {
  return percent > 0 ? 'danger' : 'success'
}

const formatChangePercent = (percent) => {
  return percent > 0 ? `+${percent}%` : `${percent}%`
}

const truncateContent = (content) => {
  if (!content) return ''
  // 移除换行符并截断
  const plainText = content.replace(/\n/g, ' ').replace(/\s+/g, ' ')
  return plainText.length > 60 ? plainText.substring(0, 60) + '...' : plainText
}

// 定时刷新未读数量
let refreshInterval = null

onMounted(() => {
  fetchMessages()
  // 每30秒刷新一次未读数量
  refreshInterval = setInterval(() => {
    getUnreadCount().then(res => {
      if (res && res.data) {
        unreadCount.value = res.data.unread_count || 0
      }
    }).catch(() => {})
  }, 30000)
})

// 组件卸载时清除定时器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.message-bell {
  display: inline-block;
}

.bell-container {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.bell-container:hover {
  background-color: #f5f7fa;
}

.message-popover {
  margin: -12px;
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.message-list {
  max-height: 400px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  border-bottom: 1px solid #f0f0f0;
}

.message-item:last-child {
  border-bottom: none;
}

.message-item:hover {
  background-color: #f5f7fa;
}

.message-item.unread {
  background-color: #ecf5ff;
}

.message-icon {
  flex-shrink: 0;
  margin-right: 12px;
  padding-top: 2px;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.4;
}

.message-text {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-bottom: 6px;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
}

.message-status {
  flex-shrink: 0;
  padding-left: 8px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background-color: #f56c6c;
  border-radius: 50%;
  display: block;
}

.popover-footer {
  padding: 10px 16px;
  text-align: center;
  border-top: 1px solid #ebeef5;
}

.view-more {
  color: #409eff;
  text-decoration: none;
  font-size: 13px;
}

.view-more:hover {
  text-decoration: underline;
}
</style>
