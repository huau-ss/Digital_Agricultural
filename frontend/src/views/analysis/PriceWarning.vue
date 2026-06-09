<template>
  <div class="price-warning">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>价格预警</h2>
      <p class="subtitle">基于LSTM预测模型，实时监控农产品价格异常波动</p>
    </div>

    <!-- 预警阈值说明卡片 -->
    <el-row :gutter="20" class="threshold-cards">
      <el-col :xs="24" :sm="12">
        <div class="threshold-card rise">
          <div class="threshold-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="threshold-content">
            <div class="threshold-value">≥ {{ riseThreshold }}%</div>
            <div class="threshold-label">涨幅预警阈值</div>
            <div class="threshold-desc">预测价格较当前价格上涨超过此阈值时触发</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12">
        <div class="threshold-card drop">
          <div class="threshold-icon">
            <el-icon><Bottom /></el-icon>
          </div>
          <div class="threshold-content">
            <div class="threshold-value">≥ {{ dropThreshold }}%</div>
            <div class="threshold-label">跌幅预警阈值</div>
            <div class="threshold-desc">预测价格较当前价格下跌超过此阈值时触发</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选和操作区域 -->
    <div class="filter-section">
      <div class="filter-left">
        <el-radio-group v-model="filterStatus" @change="handleFilterChange">
          <el-radio-button label="all">全部消息</el-radio-button>
          <el-radio-button label="unread">
            未读消息
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="badge" />
          </el-radio-button>
          <el-radio-button label="read">已读消息</el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-right">
        <el-select v-model="filterPriority" placeholder="优先级" clearable @change="loadWarnings">
          <el-option label="紧急" value="urgent" />
          <el-option label="重要" value="high" />
          <el-option label="一般" value="medium" />
        </el-select>
        <el-button type="primary" @click="markAllRead" :disabled="unreadCount === 0">
          <el-icon><Check /></el-icon>
          全部已读
        </el-button>
      </div>
    </div>

    <!-- 预警消息列表 -->
    <div class="warning-list" v-loading="loading">
      <template v-if="warnings.length > 0">
        <div
          v-for="warning in warnings"
          :key="warning.id"
          class="warning-item"
          :class="[warning.priority, { unread: !warning.is_read }]"
          @click="handleWarningClick(warning)"
        >
          <!-- 优先级标签 -->
          <div class="priority-tag" :class="warning.priority">
            <el-icon v-if="warning.priority === 'urgent'"><WarningFilled /></el-icon>
            <el-icon v-else-if="warning.priority === 'high'"><StarFilled /></el-icon>
            <el-icon v-else><InfoFilled /></el-icon>
            <span>{{ getPriorityText(warning.priority) }}</span>
          </div>

          <!-- 消息主体 -->
          <div class="warning-body">
            <div class="warning-header">
              <span class="warning-title">{{ warning.title }}</span>
              <span class="warning-time">{{ formatTime(warning.created_at) }}</span>
            </div>

            <div class="warning-content">
              <!-- 价格信息展示 -->
              <div class="price-info">
                <div class="price-item">
                  <span class="price-label">当前价格</span>
                  <span class="price-value">{{ warning.current_price?.toFixed(2) || '-' }} 元/斤</span>
                </div>
                <div class="price-arrow">
                  <el-icon v-if="warning.change_direction === '上涨'"><Top /></el-icon>
                  <el-icon v-else-if="warning.change_direction === '下跌'"><Bottom /></el-icon>
                  <span>{{ Math.abs(warning.price_change_percent) || 0 }}%</span>
                </div>
                <div class="price-item">
                  <span class="price-label">{{ warning.change_direction === '上涨' ? '预测最高价' : '预测最低价' }}</span>
                  <span class="price-value highlight">{{ warning.predicted_price?.toFixed(2) || '-' }} 元/斤</span>
                </div>
                <div class="price-item">
                  <span class="price-label">预计时间</span>
                  <span class="price-value">{{ warning.change_days || 0 }} 天后</span>
                </div>
              </div>

              <!-- 建议内容 -->
              <div class="suggestion" v-if="warning.suggestion">
                <el-icon><Memo /></el-icon>
                <span>{{ warning.suggestion }}</span>
              </div>
            </div>
          </div>

          <!-- 未读红点 -->
          <div class="unread-dot" v-if="!warning.is_read"></div>
        </div>
      </template>

      <!-- 空状态 -->
      <el-empty v-else description="暂无预警消息" :image-size="120">
        <template #image>
          <el-icon :size="60" color="#c0c4cc"><Bell /></el-icon>
        </template>
      </el-empty>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadWarnings"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 消息详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="selectedWarning?.title"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="warning-detail" v-if="selectedWarning">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="产品名称" :span="2">
            {{ selectedWarning.related_product_name }}
          </el-descriptions-item>
          <el-descriptions-item label="预警类型">
            <el-tag :type="selectedWarning.change_direction === '上涨' ? 'danger' : 'warning'" size="small">
              {{ selectedWarning.change_direction || '未知' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityTagType(selectedWarning.priority)" size="small">
              {{ getPriorityText(selectedWarning.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前价格">
            {{ selectedWarning.current_price?.toFixed(2) || '-' }} 元/斤
          </el-descriptions-item>
          <el-descriptions-item label="预测价格">
            {{ selectedWarning.predicted_price?.toFixed(2) || '-' }} 元/斤
          </el-descriptions-item>
          <el-descriptions-item label="变化幅度">
            <span :class="selectedWarning.change_direction === '上涨' ? 'text-rise' : 'text-drop'">
              {{ selectedWarning.change_direction === '上涨' ? '+' : '-' }}{{ Math.abs(selectedWarning.price_change_percent) || 0 }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="预计时间">
            {{ selectedWarning.change_days || 0 }} 天后
          </el-descriptions-item>
          <el-descriptions-item label="发送时间" :span="2">
            {{ formatDateTime(selectedWarning.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="消息内容" :span="2">
            {{ selectedWarning.content }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="markAsRead">标记已读</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts, Bottom, Check, WarningFilled, StarFilled,
  InfoFilled, Top, Memo, Bell
} from '@element-plus/icons-vue'
import { getWarningMessages, markWarningRead, markAllWarningsRead } from '@/api/warning'

// ========== 状态定义 ==========
const loading = ref(false)
const warnings = ref([])
const unreadCount = ref(0)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const filterStatus = ref('all')
const filterPriority = ref('')
const dialogVisible = ref(false)
const selectedWarning = ref(null)

// 预警阈值（默认15%涨幅，10%跌幅）
const riseThreshold = ref(15)
const dropThreshold = ref(10)

// ========== 加载预警消息 ==========
const loadWarnings = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      message_type: 'price_warning'
    }

    if (filterPriority.value) {
      params.priority = filterPriority.value
    }

    if (filterStatus.value === 'unread') {
      params.is_read = false
    } else if (filterStatus.value === 'read') {
      params.is_read = true
    }

    const res = await getWarningMessages(params)

    // 处理返回数据
    if (res.data && res.data.results) {
      warnings.value = res.data.results.map(item => ({
        ...item,
        // 确保数字类型正确处理
        current_price: Number(item.current_price) || 0,
        predicted_price: Number(item.predicted_price) || 0,
        price_change_percent: Number(item.price_change_percent) || 0,
        change_days: Number(item.change_days) || 0,
        suggestion: extractSuggestion(item.content)
      }))
      total.value = res.data.count || res.data.results.length

      // 计算未读数量
      unreadCount.value = res.data.results.filter(w => !w.is_read).length
    }
  } catch (error) {
    console.error('加载预警消息失败:', error)
    ElMessage.error('加载预警消息失败')
  } finally {
    loading.value = false
  }
}

// ========== 从内容中提取建议 ==========
const extractSuggestion = (content) => {
  if (!content) return ''
  const match = content.match(/建议[：:](.+?)(?:\n|$)/)
  return match ? match[1].trim() : ''
}

// ========== 筛选状态变化 ==========
const handleFilterChange = () => {
  currentPage.value = 1
  loadWarnings()
}

// ========== 分页大小变化 ==========
const handleSizeChange = () => {
  currentPage.value = 1
  loadWarnings()
}

// ========== 点击预警消息 ==========
const handleWarningClick = async (warning) => {
  selectedWarning.value = warning
  dialogVisible.value = true

  // 如果未读，自动标记为已读
  if (!warning.is_read) {
    await markAsRead()
  }
}

// ========== 标记单条已读 ==========
const markAsRead = async () => {
  if (!selectedWarning.value) return

  try {
    await markWarningRead(selectedWarning.value.id)
    selectedWarning.value.is_read = true

    // 更新列表中的状态
    const index = warnings.value.findIndex(w => w.id === selectedWarning.value.id)
    if (index !== -1) {
      warnings.value[index].is_read = true
    }

    // 更新未读数量
    if (unreadCount.value > 0) {
      unreadCount.value--
    }
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// ========== 全部已读 ==========
const markAllRead = async () => {
  try {
    await ElMessageBox.confirm('确定要将所有预警消息标记为已读吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    await markAllWarningsRead()
    ElMessage.success('已全部标记为已读')

    // 刷新列表
    loadWarnings()
    unreadCount.value = 0
  } catch {
    // 取消操作
  }
}

// ========== 工具函数 ==========

// 获取优先级文本
const getPriorityText = (priority) => {
  const map = {
    urgent: '紧急',
    high: '重要',
    medium: '一般'
  }
  return map[priority] || '一般'
}

// 获取优先级标签类型
const getPriorityTagType = (priority) => {
  const map = {
    urgent: 'danger',
    high: 'warning',
    medium: 'info'
  }
  return map[priority] || 'info'
}

// 格式化时间（相对时间）
const formatTime = (timeStr) => {
  if (!timeStr) return ''

  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return timeStr.split('T')[0]
}

// 格式化完整日期时间
const formatDateTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ========== 生命周期 ==========
let refreshTimer = null

onMounted(() => {
  loadWarnings()

  // 每分钟刷新一次未读数
  refreshTimer = setInterval(() => {
    if (!dialogVisible.value) {
      loadWarnings()
    }
  }, 60000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.price-warning {
  padding: 20px;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

/* 阈值卡片 */
.threshold-cards {
  margin-bottom: 20px;
}

.threshold-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.threshold-card.rise {
  border-left: 4px solid #f56c6c;
}

.threshold-card.drop {
  border-left: 4px solid #e6a23c;
}

.threshold-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 16px;
  font-size: 24px;
}

.threshold-card.rise .threshold-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.threshold-card.drop .threshold-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.threshold-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.threshold-card.rise .threshold-value {
  color: #f56c6c;
}

.threshold-card.drop .threshold-value {
  color: #e6a23c;
}

.threshold-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.threshold-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 筛选区域 */
.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.badge {
  margin-left: 4px;
}

/* 预警列表 */
.warning-list {
  min-height: 400px;
}

.warning-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.warning-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.warning-item.unread {
  background: linear-gradient(135deg, #f0f9ff 0%, #fff 100%);
  border-left: 3px solid #409eff;
}

.warning-item.urgent {
  border-left: 3px solid #f56c6c;
}

.warning-item.high {
  border-left: 3px solid #e6a23c;
}

.warning-item.medium {
  border-left: 3px solid #909399;
}

/* 优先级标签 */
.priority-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-right: 16px;
  flex-shrink: 0;
}

.priority-tag.urgent {
  background: #fef0f0;
  color: #f56c6c;
}

.priority-tag.high {
  background: #fdf6ec;
  color: #e6a23c;
}

.priority-tag.medium {
  background: #f4f4f5;
  color: #909399;
}

/* 消息主体 */
.warning-body {
  flex: 1;
  min-width: 0;
}

.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.warning-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.warning-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

/* 价格信息 */
.price-info {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 12px;
}

.price-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.price-label {
  font-size: 12px;
  color: #909399;
}

.price-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.price-value.highlight {
  color: #409eff;
}

.price-arrow {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 18px;
  font-weight: 700;
  color: #67c23a;
}

.text-rise {
  color: #f56c6c;
  font-weight: 600;
}

.text-drop {
  color: #67c23a;
  font-weight: 600;
}

/* 建议 */
.suggestion {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  padding: 8px 12px;
  background: #fdf6ec;
  border-radius: 4px;
}

.suggestion .el-icon {
  color: #e6a23c;
}

/* 未读红点 */
.unread-dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 8px;
  height: 8px;
  background: #f56c6c;
  border-radius: 50%;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

/* 详情对话框 */
.warning-detail {
  padding: 10px 0;
}

.text-rise {
  color: #f56c6c;
  font-weight: 600;
}

.text-drop {
  color: #67c23a;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .filter-section {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .filter-right {
    width: 100%;
    justify-content: space-between;
  }

  .price-info {
    flex-wrap: wrap;
    gap: 12px;
  }

  .warning-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
