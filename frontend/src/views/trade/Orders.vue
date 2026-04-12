<template>
  <div class="order-management">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>我的订单</span>
          <el-button type="primary" size="small" @click="$router.push('/dashboard/trade-hall')">
            去供需大厅采购
          </el-button>
        </div>
      </template>

      <!-- 状态筛选 -->
      <div class="filter-bar">
        <el-radio-group v-model="statusFilter" @change="handleFilterChange">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待确认</el-radio-button>
          <el-radio-button value="confirmed">已确认</el-radio-button>
          <el-radio-button value="shipped">已发货</el-radio-button>
          <el-radio-button value="completed">已完成</el-radio-button>
          <el-radio-button value="cancelled">已取消</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 订单列表 -->
      <div v-if="orders.length > 0" class="order-list" v-loading="loading">
        <div v-for="order in orders" :key="order.id" class="order-item">
          <div class="order-header">
            <span class="order-no">订单号: {{ order.order_no }}</span>
            <el-tag :type="getStatusType(order.status)" size="small">
              {{ order.status_display }}
            </el-tag>
          </div>

          <div class="order-body">
            <div class="order-info">
              <div class="product-name">
                <el-icon><Box /></el-icon>
                {{ order.product_name }}
              </div>
              <div class="order-detail">
                <span>数量: {{ order.quantity }}{{ order.unit }}</span>
                <span>单价: {{ order.unit_price }}元/{{ order.unit }}</span>
              </div>
              <div class="order-amount">
                总金额: <span class="amount">¥{{ order.total_amount }}</span>
              </div>
            </div>

            <div class="order-parties">
              <div class="party-item">
                <span class="label">卖方:</span>
                <span>{{ order.seller_name }}</span>
              </div>
              <div class="party-item">
                <span class="label">买方:</span>
                <span>{{ order.buyer_name }}</span>
              </div>
              <div class="party-item my-role">
                <span class="label">您的角色:</span>
                <el-tag size="small" :type="isSeller(order) ? 'success' : 'primary'">
                  {{ isSeller(order) ? '卖方' : '买方' }}
                </el-tag>
              </div>
            </div>

            <div class="order-time">
              <span>创建时间: {{ formatDate(order.created_at) }}</span>
            </div>
          </div>

          <div class="order-actions">
            <!-- 待确认状态 - 显示给卖方 -->
            <template v-if="order.status === 'pending' && isSeller(order)">
              <el-button type="success" size="small" @click="handleConfirm(order.id)">
                确认订单
              </el-button>
              <el-button type="primary" size="small" @click="handleShip(order.id)">
                发货
              </el-button>
            </template>

            <!-- 已确认状态 - 显示给卖方 -->
            <template v-if="order.status === 'confirmed' && isSeller(order)">
              <el-button type="primary" size="small" @click="handleShip(order.id)">
                发货
              </el-button>
            </template>

            <!-- 已发货状态 - 显示给买方 -->
            <template v-if="order.status === 'shipped' && isBuyer(order)">
              <el-button type="success" size="small" @click="handleComplete(order.id)">
                确认收货
              </el-button>
            </template>

            <!-- 待确认状态 - 显示给买方 -->
            <template v-if="order.status === 'pending' && isBuyer(order)">
              <span class="action-tip">等待卖方确认...</span>
            </template>

            <!-- 未完成状态 - 可取消 -->
            <template v-if="order.status !== 'completed' && order.status !== 'cancelled'">
              <el-button type="danger" size="small" plain @click="handleCancel(order.id)">
                取消订单
              </el-button>
            </template>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无订单" :image-size="100">
        <el-button type="primary" @click="$router.push('/dashboard/trade-hall')">
          去供需大厅看看
        </el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box } from '@element-plus/icons-vue'
import { getOrders, confirmOrder, shipOrder, completeOrder, cancelOrder } from '@/api/order'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const orders = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const statusFilter = ref('')
const loading = ref(false)

const isSeller = (order) => Number(order.seller_id || order.seller) === Number(userStore.userId)
const isBuyer = (order) => Number(order.buyer_id || order.buyer) === Number(userStore.userId)

const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    confirmed: 'primary',
    shipped: 'info',
    completed: 'success',
    cancelled: 'info'
  }
  return typeMap[status] || ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    const res = await getOrders(params)

    if (res && res.results) {
      orders.value = res.results
      total.value = res.count || res.results.length
    } else if (res && Array.isArray(res)) {
      orders.value = res
      total.value = res.length
    } else if (res && res.data) {
      orders.value = res.data.results || res.data
      total.value = res.data.count || orders.value.length
    } else {
      orders.value = []
      total.value = 0
    }

    // 调试信息
    console.log('========== 订单调试 ==========')
    console.log('当前用户ID:', userStore.userId)
    console.log('用户角色:', userStore.userRole)
    console.log('API响应:', res)
    console.log('订单列表:', orders.value)
    orders.value.forEach((order, index) => {
      console.log(`订单${index + 1}:`, {
        id: order.id,
        order_no: order.order_no,
        status: order.status,
        status_display: order.status_display,
        buyer: order.buyer,
        buyer_id: order.buyer_id,
        buyer_name: order.buyer_name,
        seller: order.seller,
        seller_id: order.seller_id,
        seller_name: order.seller_name,
        isSeller: isSeller(order),
        isBuyer: isBuyer(order)
      })
    })
    console.log('================================')
  } catch (error) {
    console.error('获取订单失败:', error)
    ElMessage.error('获取订单失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchOrders()
}

const handlePageChange = () => {
  fetchOrders()
}

const handleConfirm = async (orderId) => {
  try {
    await ElMessageBox.confirm('确认此订单?', '确认订单', { type: 'info' })
    await confirmOrder(orderId)
    ElMessage.success('订单已确认')
    fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleShip = async (orderId) => {
  try {
    await ElMessageBox.confirm('确认发货?', '发货', { type: 'info' })
    await shipOrder(orderId)
    ElMessage.success('已发货')
    fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleComplete = async (orderId) => {
  try {
    await ElMessageBox.confirm('确认收货?', '完成订单', { type: 'info' })
    await completeOrder(orderId)
    ElMessage.success('订单已完成')
    fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleCancel = async (orderId) => {
  try {
    await ElMessageBox.confirm('确定取消此订单?', '取消订单', { type: 'warning' })
    await cancelOrder(orderId)
    ElMessage.success('订单已取消')
    fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 20px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.3s;
}

.order-item:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.order-no {
  font-size: 14px;
  color: #909399;
  font-family: monospace;
}

.order-body {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .order-body {
    grid-template-columns: 1fr;
  }
}

.order-info .product-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-detail {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.order-detail span {
  margin-right: 16px;
}

.order-amount {
  font-size: 14px;
  color: #606266;
}

.amount {
  color: #f56c6c;
  font-weight: bold;
  font-size: 18px;
}

.order-parties {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.party-item {
  font-size: 14px;
  color: #606266;
}

.party-item .label {
  color: #909399;
}

.party-item.my-role {
  margin-top: 4px;
}

.order-time {
  font-size: 13px;
  color: #909399;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.action-tip {
  color: #909399;
  font-size: 13px;
  font-style: italic;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
