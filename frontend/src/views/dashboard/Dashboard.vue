<template>
  <div class="dashboard-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">
        <el-icon class="title-icon"><DataAnalysis /></el-icon>
        数据概览
      </h2>
      <div class="header-time">{{ currentTime }}</div>
    </div>

    <!-- 顶部统计数据卡片 -->
    <el-row :gutter="20" class="stats-row" :class="{ 'fade-in': mounted }">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-products">
          <div class="stat-icon">
            <el-icon><Goods /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.product_count || 0 }}</div>
            <div class="stat-label">监控产品</div>
          </div>
          <div class="stat-trend up" v-if="stats.product_count > 0">
            <el-icon><TrendCharts /></el-icon>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-warnings">
          <div class="stat-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.warning_count || 0 }}</div>
            <div class="stat-label">今日预警</div>
          </div>
          <div class="stat-trend" :class="stats.warning_count > 0 ? 'alert' : 'stable'">
            <el-icon><Warning /></el-icon>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-trades">
          <div class="stat-icon">
            <el-icon><Shop /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.trade_count || 0 }}</div>
            <div class="stat-label">供需信息</div>
          </div>
          <div class="stat-trend up" v-if="stats.trade_count > 0">
            <el-icon><DataLine /></el-icon>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card stat-user">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ greeting }}</div>
            <div class="stat-label">{{ userInfo?.username || '用户' }}</div>
          </div>
          <div class="stat-trend online">
            <el-icon><CircleCheckFilled /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 中部两列布局 -->
    <el-row :gutter="20" class="main-row" :class="{ 'fade-in': mounted }">
      <!-- 左侧：AI 涨势预测 TOP 5 -->
      <el-col :xs="24" :lg="14">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon rise"><TrendCharts /></el-icon>
                <span>AI 涨势预测 TOP 5</span>
              </div>
              <el-tag type="success" size="small" effect="dark">LSTM 模型</el-tag>
            </div>
          </template>

          <div class="predict-list" v-loading="loading">
            <template v-if="predictTop5.length > 0">
              <div
                v-for="(item, index) in predictTop5"
                :key="item.product_id || index"
                class="predict-item"
                :class="{ 'sample-data': item.is_sample }"
              >
                <div class="predict-rank" :class="getRankClass(index)">
                  {{ index + 1 }}
                </div>
                <div class="predict-info">
                  <div class="predict-name">
                    {{ item.product_name }}
                    <el-tag size="small" type="info">{{ getCategoryLabel(item.category) }}</el-tag>
                    <el-tag v-if="item.is_sample" size="small" type="warning">示例</el-tag>
                  </div>
                  <div class="predict-detail">
                    当前价: <span class="price">¥{{ item.current_price }}/{{ item.unit }}</span>
                    <span class="separator">|</span>
                    预计峰值: <span class="price rise">¥{{ item.predicted_max_price }}</span>
                  </div>
                </div>
                <div class="predict-change">
                  <div class="change-value rise">+{{ item.change_percent }}%</div>
                  <div class="change-label">{{ item.change_day }}天后达峰</div>
                </div>
                <div class="predict-bar">
                  <div
                    class="bar-fill rise"
                    :style="{ width: getBarWidth(item.change_percent) + '%' }"
                  ></div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无预测数据" :image-size="80" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：最新产销动态 -->
      <el-col :xs="24" :lg="10">
        <el-card class="trade-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon news"><Connection /></el-icon>
                <span>最新产销动态</span>
              </div>
              <el-button type="primary" link size="small" @click="$router.push('/dashboard/trade-hall')">
                查看更多
                <el-icon class="el-icon--right"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>

          <div class="trade-list" v-loading="loading">
            <template v-if="recentTrades.length > 0">
              <div
                v-for="trade in recentTrades"
                :key="trade.id"
                class="trade-item"
                @click="handleTradeClick(trade)"
              >
                <div class="trade-type">
                  <el-tag :type="trade.type === 'supply' ? 'success' : 'warning'" effect="dark" size="small">
                    {{ trade.type_display }}
                  </el-tag>
                </div>
                <div class="trade-content">
                  <div class="trade-product">
                    <span class="product-name">{{ trade.product_name }}</span>
                    <span class="trade-quantity">{{ trade.quantity }}{{ trade.unit }}</span>
                  </div>
                  <div class="trade-meta">
                    <span class="publisher">
                      <el-icon><User /></el-icon>
                      {{ trade.publisher }}
                    </span>
                    <span class="origin">
                      <el-icon><Location /></el-icon>
                      {{ trade.origin }}
                    </span>
                  </div>
                </div>
                <div class="trade-info">
                  <div class="trade-price">{{ trade.expected_price }}</div>
                  <div class="trade-time">{{ trade.created_at }}</div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无供需信息" :image-size="80" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部快捷入口 -->
    <el-row :gutter="20" class="quick-entry-row" :class="{ 'fade-in': mounted }">
      <el-col :span="24">
        <el-card class="quick-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon class="header-icon"><Grid /></el-icon>
                <span>快捷入口</span>
              </div>
            </div>
          </template>
          <div class="quick-buttons">
            <el-button
              type="primary"
              size="large"
              class="quick-btn"
              @click="$router.push('/dashboard/profit-simulation')"
            >
              <el-icon class="btn-icon"><Money /></el-icon>
              <span class="btn-text">利润模拟测算</span>
              <span class="btn-desc">智能计算种植收益</span>
            </el-button>

            <el-button
              type="success"
              size="large"
              class="quick-btn"
              @click="$router.push('/dashboard/data-screen')"
            >
              <el-icon class="btn-icon"><DataBoard /></el-icon>
              <span class="btn-text">数据大屏分析</span>
              <span class="btn-desc">可视化市场数据</span>
            </el-button>

            <el-button
              type="warning"
              size="large"
              class="quick-btn"
              @click="$router.push('/dashboard/trade-hall')"
            >
              <el-icon class="btn-icon"><Sell /></el-icon>
              <span class="btn-text">发布农产品</span>
              <span class="btn-desc">快速发布供需信息</span>
            </el-button>

            <el-button
              type="danger"
              size="large"
              class="quick-btn"
              @click="$router.push('/dashboard/profile')"
            >
              <el-icon class="btn-icon"><UserFilled /></el-icon>
              <span class="btn-text">个人中心</span>
              <span class="btn-desc">设置与消息通知</span>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataAnalysis, Goods, Bell, Shop, User, TrendCharts, Warning,
  CircleCheckFilled, Connection, ArrowRight, Location, Grid,
  Money, DataBoard, Sell, UserFilled, DataLine
} from '@element-plus/icons-vue'
import { getDashboardSummary } from '@/api/dashboard'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const mounted = ref(false)
const loading = ref(false)
const stats = ref({})
const predictTop5 = ref([])
const recentTrades = ref([])

// 当前时间
const currentTime = ref('')
let timeInterval = null

const updateTime = () => {
  const now = new Date()
  const options = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
    hour: '2-digit',
    minute: '2-digit'
  }
  currentTime.value = now.toLocaleDateString('zh-CN', options)
}

// 问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '凌晨好'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

// 用户信息
const userInfo = computed(() => userStore.userInfo)


// 获取排名样式
const getRankClass = (index) => {
  const classes = ['gold', 'silver', 'bronze']
  return index < 3 ? classes[index] : ''
}

// 获取分类标签
const getCategoryLabel = (category) => {
  const labels = {
    vegetable: '蔬菜',
    fruit: '水果',
    livestock: '畜禽',
    aquatic: '水产',
    grain: '粮油',
    other: '其他'
  }
  return labels[category] || '其他'
}

// 计算进度条宽度
const getBarWidth = (percent) => {
  const maxPercent = Math.max(...predictTop5.value.map(p => p.change_percent))
  if (maxPercent === 0) return 0
  return (percent / maxPercent) * 100
}

// 处理供需信息点击
const handleTradeClick = (trade) => {
  router.push('/dashboard/trade-hall')
}

// 获取仪表盘数据
const fetchDashboardData = async () => {
  loading.value = true
  try {
    const res = await getDashboardSummary()
    if (res && res.data) {
      stats.value = res.data.stats || {}
      predictTop5.value = res.data.predict_top5 || []
      recentTrades.value = res.data.recent_trades || []
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    // 设置默认值
    stats.value = {
      product_count: 0,
      warning_count: 0,
      trade_count: 0
    }
    predictTop5.value = []
    recentTrades.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  mounted.value = true
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  fetchDashboardData()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  min-height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 8px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-icon {
  font-size: 28px;
}

.header-time {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.stat-products::before { background: linear-gradient(180deg, #409eff, #66b1ff); }
.stat-warnings::before { background: linear-gradient(180deg, #f56c6c, #f78989); }
.stat-trades::before { background: linear-gradient(180deg, #67c23a, #85ce61); }
.stat-user::before { background: linear-gradient(180deg, #909399, #a6a9ad); }

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 28px;
  margin-right: 16px;
}

.stat-products .stat-icon { background: linear-gradient(135deg, #409eff, #66b1ff); color: #fff; }
.stat-warnings .stat-icon { background: linear-gradient(135deg, #f56c6c, #f78989); color: #fff; }
.stat-trades .stat-icon { background: linear-gradient(135deg, #67c23a, #85ce61); color: #fff; }
.stat-user .stat-icon { background: linear-gradient(135deg, #909399, #a6a9ad); color: #fff; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-trend {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 20px;
}

.stat-trend.up { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.stat-trend.alert { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }
.stat-trend.stable { background: rgba(144, 147, 153, 0.1); color: #909399; }
.stat-trend.online { background: rgba(64, 158, 255, 0.1); color: #409eff; }

/* 主内容行 */
.main-row {
  margin-bottom: 20px;
}

/* 卡片样式 */
.chart-card,
.trade-card,
.quick-card {
  border: none;
  border-radius: 16px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  font-size: 20px;
}

.header-icon.rise { color: #67c23a; }
.header-icon.news { color: #409eff; }

/* 预测列表 */
.predict-list {
  padding: 8px 0;
}

.predict-item {
  display: grid;
  grid-template-columns: 48px 1fr auto 120px;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin-bottom: 12px;
  background: #f5f7fa;
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
}

.predict-item:hover {
  background: #ecf5ff;
  transform: translateX(4px);
}

.predict-item.sample-data {
  border: 1px dashed #e6a23c;
}

.predict-rank {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 700;
  font-size: 16px;
  color: #fff;
  background: #909399;
}

.predict-rank.gold { background: linear-gradient(135deg, #ffd700, #ffb800); box-shadow: 0 2px 8px rgba(255, 184, 0, 0.4); }
.predict-rank.silver { background: linear-gradient(135deg, #c0c0c0, #a8a8a8); box-shadow: 0 2px 8px rgba(168, 168, 168, 0.4); }
.predict-rank.bronze { background: linear-gradient(135deg, #cd7f32, #b8722d); box-shadow: 0 2px 8px rgba(184, 114, 45, 0.4); }

.predict-info {
  min-width: 0;
}

.predict-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
}

.predict-detail {
  font-size: 12px;
  color: #909399;
}

.predict-detail .price {
  font-weight: 500;
  color: #606266;
}

.predict-detail .price.rise {
  color: #67c23a;
}

.predict-detail .separator {
  margin: 0 6px;
  color: #dcdfe6;
}

.predict-change {
  text-align: right;
}

.change-value {
  font-size: 22px;
  font-weight: 700;
}

.change-value.rise {
  color: #f56c6c;
}

.change-label {
  font-size: 11px;
  color: #909399;
}

.predict-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #ebeef5;
  border-radius: 0 0 12px 12px;
}

.bar-fill {
  height: 100%;
  border-radius: 0 0 12px 12px;
  transition: width 0.8s ease;
}

.bar-fill.rise {
  background: linear-gradient(90deg, #67c23a, #85ce61);
}

/* 供需列表 */
.trade-list {
  max-height: 420px;
  overflow-y: auto;
}

.trade-item {
  display: flex;
  align-items: flex-start;
  padding: 14px 8px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin-bottom: 4px;
}

.trade-item:hover {
  background: #f5f7fa;
  padding-left: 12px;
}

.trade-item:last-child {
  border-bottom: none;
}

.trade-type {
  flex-shrink: 0;
  margin-right: 12px;
  padding-top: 2px;
}

.trade-content {
  flex: 1;
  min-width: 0;
}

.trade-product {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.product-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.trade-quantity {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.trade-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.trade-meta span {
  display: flex;
  align-items: center;
  gap: 3px;
}

.trade-info {
  flex-shrink: 0;
  text-align: right;
}

.trade-price {
  font-weight: 600;
  font-size: 14px;
  color: #f56c6c;
}

.trade-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 2px;
}

/* 快捷入口 */
.quick-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.quick-btn {
  height: auto;
  padding: 20px 24px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  transition: all 0.3s ease;
}

.quick-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.btn-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.btn-text {
  font-size: 15px;
  font-weight: 600;
}

.btn-desc {
  font-size: 12px;
  opacity: 0.8;
}

/* 动画 */
.fade-in {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .page-title {
    font-size: 20px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }

  .stat-value {
    font-size: 24px;
  }

  .predict-item {
    grid-template-columns: 40px 1fr;
    gap: 12px;
  }

  .predict-change,
  .predict-bar {
    grid-column: 2;
  }

  .predict-change {
    text-align: left;
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .quick-buttons {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .quick-buttons {
    grid-template-columns: 1fr;
  }
}

/* 滚动条样式 */
.trade-list::-webkit-scrollbar {
  width: 6px;
}

.trade-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.trade-list::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 3px;
}
</style>
