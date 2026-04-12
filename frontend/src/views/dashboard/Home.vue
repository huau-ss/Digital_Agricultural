<template>
  <div class="dashboard-home">
    <h2>欢迎使用数字农业平台</h2>

    <!-- 用户信息卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409EFF;">
              <el-icon :size="30"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ userInfo?.username || '-' }}</div>
              <div class="stat-label">当前用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67C23A;">
              <el-icon :size="30"><Postcard /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ userInfo?.role_display || '-' }}</div>
              <div class="stat-label">用户角色</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #E6A23C;">
              <el-icon :size="30"><Message /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ userInfo?.email || '-' }}</div>
              <div class="stat-label">绑定邮箱</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #F56C6C;">
              <el-icon :size="30"><Phone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ userInfo?.phone || '-' }}</div>
              <div class="stat-label">手机号码</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增数据模块 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：监控产品 + 今日预警 + 供需信息 -->
      <el-col :span="14">
        <!-- 监控产品 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>监控产品</span>
              <span class="count-badge">共 {{ monitoredProducts.length }} 种</span>
            </div>
          </template>
          <div v-if="monitoredProducts.length > 0" class="product-grid">
            <div
              v-for="product in monitoredProducts.slice(0, 12)"
              :key="product.id"
              class="product-item"
            >
              <span class="product-name">{{ product.name }}</span>
              <span class="product-category">{{ getCategoryLabel(product.category) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无监控产品" :image-size="60" />
        </el-card>

        <!-- 供需信息 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>供需信息</span>
              <el-button type="primary" size="small" text @click="$router.push('/trade')">查看更多</el-button>
            </div>
          </template>
          <div v-if="supplyDemandList.length > 0" class="trade-list">
            <div
              v-for="item in supplyDemandList"
              :key="item.id"
              class="trade-item"
            >
              <div class="trade-left">
                <el-tag :type="getTradeTypeTag(item.info_type)" size="small">
                  {{ item.info_type_display }}
                </el-tag>
                <span class="trade-product">{{ item.product_name }}</span>
              </div>
              <div class="trade-right">
                <span class="trade-qty">{{ item.quantity }}{{ item.unit }}</span>
                <span class="trade-price">{{ item.expected_price }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无供需信息" :image-size="60" />
        </el-card>
      </el-col>

      <!-- 右侧：今日预警 + AI涨势预测 -->
      <el-col :span="10">
        <!-- 今日预警 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>今日预警</span>
              <span class="count-badge warning" v-if="warnings.length > 0">{{ warnings.length }}条</span>
            </div>
          </template>
          <div v-if="warnings.length > 0" class="warning-list">
            <div
              v-for="w in warnings"
              :key="w.id"
              class="warning-item"
              :class="'warning-' + w.level"
            >
              <div class="warning-header">
                <el-icon v-if="w.level === 'high'" color="#F56C6C"><WarningFilled /></el-icon>
                <el-icon v-else-if="w.level === 'medium'" color="#E6A23C"><WarningFilled /></el-icon>
                <el-icon v-else color="#909399"><WarningFilled /></el-icon>
                <span class="warning-title">{{ w.title }}</span>
                <span class="warning-time">{{ w.created_at }}</span>
              </div>
              <div class="warning-content">{{ w.content }}</div>
            </div>
          </div>
          <el-empty v-else description="今日暂无预警" :image-size="60" />
        </el-card>

        <!-- AI涨势预测 Top5 -->
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>AI涨势预测 Top5</span>
              <el-icon color="#409EFF"><TrendCharts /></el-icon>
            </div>
          </template>
          <div v-if="predictTop5.length > 0" class="predict-list">
            <div
              v-for="(item, index) in predictTop5"
              :key="item.product_id"
              class="predict-item"
            >
              <div class="predict-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
              <div class="predict-info">
                <div class="predict-name">{{ item.product_name }}</div>
                <div class="predict-meta">
                  <span>{{ getCategoryLabel(item.category) }}</span>
                  <span>现价: {{ item.current_price }}{{ item.unit }}</span>
                </div>
              </div>
              <div class="predict-change">
                <div class="change-value">+{{ item.change_percent }}%</div>
                <div class="change-label">预计涨幅</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无预测数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新产销动态 -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最新产销动态</span>
              <el-button type="primary" size="small" text @click="$router.push('/trade')">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentTrades.length > 0" class="news-table">
            <el-table :data="recentTrades" stripe style="width: 100%" size="small">
              <el-table-column prop="info_type_display" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getTradeTypeTag(row.info_type)" size="small">
                    {{ row.info_type_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="产品" width="120" />
              <el-table-column prop="publisher" label="发布者" width="100" />
              <el-table-column prop="origin" label="产地" width="120" />
              <el-table-column prop="quantity" label="数量" width="100" />
              <el-table-column prop="expected_price" label="期望价格" width="100" />
              <el-table-column prop="contact_phone" label="联系方式" width="140" />
              <el-table-column prop="created_at" label="发布时间" width="120" />
            </el-table>
          </div>
          <el-empty v-else description="暂无最新动态" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="30"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { User, Postcard, Message, Phone, WarningFilled, TrendCharts, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getDashboardSummary, getMonitoredProducts, getTodayWarnings, getSupplyDemandList } from '@/api/dashboard'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const loading = ref(false)
const monitoredProducts = ref([])
const warnings = ref([])
const supplyDemandList = ref([])
const predictTop5 = ref([])
const recentTrades = ref([])

// 分类标签映射
const categoryMap = {
  vegetable: { label: '蔬菜', type: 'success' },
  fruit: { label: '水果', type: 'warning' },
  grain: { label: '粮食', type: '' },
  meat: { label: '肉类', type: 'danger' },
  aquatic: { label: '水产', type: 'info' },
}

function getCategoryLabel(category) {
  return categoryMap[category]?.label || category || '其他'
}

// 供需类型标签
function getTradeTypeTag(type) {
  const map = {
    supply: 'success',
    demand: 'danger',
    cooperation: 'warning',
  }
  return map[type] || ''
}

// 加载所有数据
const loadAllData = async () => {
  loading.value = true
  console.log('开始加载所有数据...')
  try {
    await Promise.all([
      loadMonitoredProducts(),
      loadTodayWarnings(),
      loadSupplyDemand(),
      loadDashboardSummary(),
    ])
    console.log('数据加载完成')
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const loadMonitoredProducts = async () => {
  try {
    const res = await getMonitoredProducts()
    console.log('监控产品响应:', res)
    if (res && Array.isArray(res)) {
      monitoredProducts.value = res
    } else if (res && res.data) {
      monitoredProducts.value = res.data.results || res.data
    }
  } catch (error) {
    console.error('加载监控产品失败:', error)
  }
}

const loadTodayWarnings = async () => {
  try {
    const res = await getTodayWarnings()
    console.log('今日预警响应:', res)
    // 兼容多种响应格式
    if (res && Array.isArray(res.data)) {
      warnings.value = res.data
    } else if (res && res.data && Array.isArray(res.data.data)) {
      warnings.value = res.data.data
    } else if (res && Array.isArray(res)) {
      warnings.value = res
    }
  } catch (error) {
    console.error('加载今日预警失败:', error)
  }
}

const loadSupplyDemand = async () => {
  try {
    const res = await getSupplyDemandList({ page: 1, page_size: 10 })
    console.log('供需信息原始响应:', res)
    // 兼容分页和非分页格式
    let data = []
    if (res && res.results) {
      data = res.results
    } else if (res && Array.isArray(res)) {
      data = res
    } else if (res && res.data) {
      data = res.data.results || res.data
    } else if (res && res.data && res.data.results) {
      data = res.data.results
    }
    console.log('处理后数据:', data)
    supplyDemandList.value = data.slice(0, 5)
    recentTrades.value = data
  } catch (error) {
    console.error('加载供需信息失败:', error)
  }
}

const loadDashboardSummary = async () => {
  try {
    const res = await getDashboardSummary()
    console.log('仪表盘摘要响应:', res)
    if (res && res.data) {
      predictTop5.value = res.data.predict_top5 || []
    }
  } catch (error) {
    console.error('加载仪表盘摘要失败:', error)
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.dashboard-home {
  padding: 20px;
  position: relative;
}

.dashboard-home h2 {
  margin-bottom: 20px;
  color: #303133;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

/* 新增样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 15px;
}

.count-badge {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.count-badge.warning {
  background: #fef0f0;
  color: #F56C6C;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 监控产品网格 */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.product-item {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.product-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.product-category {
  font-size: 11px;
  color: #909399;
}

/* 供需列表 */
.trade-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trade-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.trade-item:last-child {
  border-bottom: none;
}

.trade-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trade-product {
  font-weight: 600;
  color: #303133;
}

.trade-right {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #606266;
  font-size: 13px;
}

.trade-price {
  color: #F56C6C;
  font-weight: 600;
}

/* 预警列表 */
.warning-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.warning-item {
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid;
}

.warning-high {
  background: #fef0f0;
  border-left-color: #F56C6C;
}

.warning-medium {
  background: #fdf6ec;
  border-left-color: #E6A23C;
}

.warning-low {
  background: #f4f4f5;
  border-left-color: #909399;
}

.warning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.warning-title {
  flex: 1;
  font-weight: 600;
  font-size: 13px;
  color: #303133;
}

.warning-time {
  font-size: 11px;
  color: #909399;
}

.warning-content {
  font-size: 12px;
  color: #606266;
  padding-left: 22px;
}

/* AI预测列表 */
.predict-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.predict-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.predict-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #fff;
  background: #909399;
  flex-shrink: 0;
}

.rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); }
.rank-2 { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); }
.rank-3 { background: linear-gradient(135deg, #CD7F32, #B87333); }

.predict-info {
  flex: 1;
}

.predict-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.predict-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #909399;
}

.predict-change {
  text-align: center;
}

.change-value {
  font-size: 16px;
  font-weight: 700;
  color: #67C23A;
}

.change-label {
  font-size: 10px;
  color: #909399;
}

/* 最新动态 */
.news-table {
  min-height: 100px;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  font-size: 16px;
  color: #409EFF;
}

.loading-overlay .el-icon {
  font-size: 36px;
  margin-bottom: 10px;
}
</style>
