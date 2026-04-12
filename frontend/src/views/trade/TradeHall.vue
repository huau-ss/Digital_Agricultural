<template>
  <div class="trade-hall">
    <div class="page-header">
      <h2>供需信息大厅</h2>
      <p class="subtitle">发布供应/求购信息，对接买卖双方</p>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="信息类型">
          <el-select v-model="searchForm.info_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="供应" value="supply" />
            <el-option label="求购" value="demand" />
          </el-select>
        </el-form-item>
        <el-form-item label="农产品">
          <el-select v-model="searchForm.product" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="进行中" value="active" />
            <el-option label="已成交" value="completed" />
            <el-option label="已过期" value="expired" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="搜索产地/描述" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="action-bar">
      <el-button type="primary" @click="openPublishDialog">
        <el-icon><Plus /></el-icon> 发布信息
      </el-button>
      <el-radio-group v-model="viewMode" style="margin-left: auto">
        <el-radio-button value="table">
          <el-icon><Grid /></el-icon> 表格
        </el-radio-button>
        <el-radio-button value="card">
          <el-icon><Menu /></el-icon> 卡片
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 表格视图 -->
    <el-card v-if="viewMode === 'table'" class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="info_type_display" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.info_type === 'supply' ? 'success' : 'warning'" size="small">
              {{ row.info_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="农产品" min-width="100" />
        <el-table-column prop="quantity" label="数量" width="100">
          <template #default="{ row }">
            {{ row.quantity }} {{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column prop="expected_price" label="期望价格" width="100">
          <template #default="{ row }">
            {{ row.expected_price ? row.expected_price + '元/斤' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="origin" label="产地" min-width="120" />
        <el-table-column prop="publisher_name" label="发布者" width="100">
          <template #default="{ row }">
            <span>{{ row.publisher_name }}</span>
            <el-tag size="small" :type="row.publisher_role === 'farmer' ? 'success' : 'primary'" style="margin-left: 4px">
              {{ row.publisher_role === 'farmer' ? '农户' : '采购商' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
            <!-- 采购商看到供应信息 - 可购买 -->
            <el-button link type="success" v-if="canBuy(row)" @click="openBuyDialog(row)">
              购买
            </el-button>
            <!-- 农户看到求购信息 - 可接受 -->
            <el-button link type="success" v-if="canAccept(row)" @click="openAcceptDialog(row)">
              接受订单
            </el-button>
            <el-button link type="danger" v-if="row.publisher === currentUserId" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 卡片视图 -->
    <div v-else class="card-grid">
      <el-card v-for="item in tableData" :key="item.id" class="trade-card" shadow="hover">
        <div class="card-header">
          <el-tag :type="item.info_type === 'supply' ? 'success' : 'warning'" size="small">
            {{ item.info_type_display }}
          </el-tag>
          <el-tag :type="getStatusType(item.status)" size="small">
            {{ item.status_display }}
          </el-tag>
        </div>
        <h3 class="card-title">{{ item.product_name }}</h3>
        <div class="card-info">
          <div class="info-row">
            <span class="label">数量</span>
            <span class="value">{{ item.quantity }} {{ item.unit }}</span>
          </div>
          <div class="info-row">
            <span class="label">价格</span>
            <span class="value price">{{ item.expected_price ? item.expected_price + '元/斤' : '面议' }}</span>
          </div>
          <div class="info-row">
            <span class="label">产地</span>
            <span class="value">{{ item.origin || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">发布者</span>
            <span class="value">{{ item.publisher_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">发布时间</span>
            <span class="value">{{ formatDate(item.created_at) }}</span>
          </div>
        </div>
        <div class="card-actions">
          <el-button type="primary" size="small" @click="viewDetail(item)">详情</el-button>
          <!-- 采购商看到供应信息 - 可购买 -->
          <el-button type="success" size="small" v-if="canBuy(item)" @click="openBuyDialog(item)">
            购买
          </el-button>
          <!-- 农户看到求购信息 - 可接受 -->
          <el-button type="success" size="small" v-if="canAccept(item)" @click="openAcceptDialog(item)">
            接受订单
          </el-button>
          <el-button type="danger" size="small" v-if="item.publisher === currentUserId" @click="handleDelete(item)">
            删除
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 发布信息弹窗 -->
    <el-dialog v-model="publishDialogVisible" :title="isEdit ? '编辑信息' : '发布信息'" width="600px">
      <el-form ref="publishFormRef" :model="publishForm" :rules="publishRules" label-width="100px">
        <el-form-item label="信息类型" prop="info_type">
          <el-radio-group v-model="publishForm.info_type" :disabled="isEdit">
            <el-radio value="supply" :disabled="userRole === 'buyer'">供应</el-radio>
            <el-radio value="demand" :disabled="userRole === 'farmer'">求购</el-radio>
          </el-radio-group>
          <div class="form-tip" v-if="userRole === 'farmer'">提示：农户只能发布供应信息</div>
          <div class="form-tip" v-if="userRole === 'buyer'">提示：采购商只能发布求购信息</div>
        </el-form-item>

        <el-form-item label="农产品" prop="product">
          <el-select v-model="publishForm.product" placeholder="请选择农产品" style="width: 100%">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数量" prop="quantity">
              <el-input-number v-model="publishForm.quantity" :min="1" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位" prop="unit">
              <el-select v-model="publishForm.unit" style="width: 100%">
                <el-option label="斤" value="斤" />
                <el-option label="公斤" value="公斤" />
                <el-option label="吨" value="吨" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="期望价格" prop="expected_price">
          <el-input-number v-model="publishForm.expected_price" :min="0" :precision="2" style="width: 100%">
            <template #suffix>
              <span>元/斤</span>
            </template>
          </el-input-number>
        </el-form-item>

        <el-form-item label="产地" prop="origin">
          <el-input v-model="publishForm.origin" placeholder="请输入产地" />
        </el-form-item>

        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="publishForm.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>

        <el-form-item label="详细信息">
          <el-input v-model="publishForm.description" type="textarea" :rows="3" placeholder="请输入详细信息" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="信息详情" width="500px">
      <div class="detail-content" v-if="currentItem">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="信息类型">
            <el-tag :type="currentItem.info_type === 'supply' ? 'success' : 'warning'">
              {{ currentItem.info_type_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentItem.status)">
              {{ currentItem.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="农产品">{{ currentItem.product_name }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ currentItem.quantity }} {{ currentItem.unit }}</el-descriptions-item>
          <el-descriptions-item label="期望价格">{{ currentItem.expected_price ? currentItem.expected_price + '元/斤' : '面议' }}</el-descriptions-item>
          <el-descriptions-item label="产地">{{ currentItem.origin || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发布者">{{ currentItem.publisher_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentItem.contact_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发布时间" :span="2">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="详细信息" :span="2">{{ currentItem.description || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <!-- 采购商看到供应信息 -->
        <el-button type="success" v-if="currentItem && canBuy(currentItem)" @click="openBuyDialog(currentItem)">
          购买
        </el-button>
        <!-- 农户看到求购信息 -->
        <el-button type="success" v-if="currentItem && canAccept(currentItem)" @click="openAcceptDialog(currentItem)">
          接受订单
        </el-button>
      </template>
    </el-dialog>

    <!-- 购买/接受订单弹窗 -->
    <el-dialog v-model="orderDialogVisible" :title="orderDialogTitle" width="500px">
      <el-form ref="orderFormRef" :model="orderForm" :rules="orderRules" label-width="100px">
        <el-form-item label="农产品">
          <span>{{ orderForm.product_name }}</span>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="orderForm.quantity" :min="1" :max="orderForm.max_quantity" :precision="2" style="width: 100%" />
          <span class="form-tip">最大: {{ orderForm.max_quantity }} {{ orderForm.unit }}</span>
        </el-form-item>
        <el-form-item label="单价(元/斤)" prop="unit_price">
          <el-input-number v-model="orderForm.unit_price" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收货地址" prop="delivery_address">
          <el-input v-model="orderForm.delivery_address" placeholder="请输入收货地址" />
        </el-form-item>
        <el-form-item label="联系电话" prop="buyer_contact">
          <el-input v-model="orderForm.buyer_contact" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="orderForm.remark" type="textarea" :rows="2" placeholder="选填备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="orderDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmitOrder">
          确认{{ orderDialogType === 'buy' ? '购买' : '接受' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Grid, Menu } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getTradeInfoList, createTradeInfo, updateTradeInfo, deleteTradeInfo } from '@/api/tradeInfo'
import { getProducts } from '@/api/dataCollection'
import { createOrder, acceptOrder } from '@/api/order'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.id)
const userRole = computed(() => userStore.userRole)

const loading = ref(false)
const submitLoading = ref(false)
const viewMode = ref('table')
const tableData = ref([])
const products = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const searchForm = reactive({
  info_type: '',
  product: '',
  status: 'active',
  keyword: ''
})

const publishDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const orderDialogVisible = ref(false)
const isEdit = ref(false)
const currentItem = ref(null)
const publishFormRef = ref(null)
const orderFormRef = ref(null)
const orderDialogType = ref('buy') // 'buy' 购买 或 'accept' 接受订单

const publishForm = reactive({
  info_type: 'supply',
  product: null,
  quantity: 1000,
  unit: '斤',
  expected_price: null,
  origin: '',
  contact_phone: '',
  description: ''
})

const orderForm = reactive({
  trade_info_id: null,
  product_id: null,
  product_name: '',
  quantity: 100,
  max_quantity: 0,
  unit: '斤',
  unit_price: null,
  delivery_address: '',
  buyer_contact: '',
  remark: ''
})

const publishRules = {
  info_type: [{ required: true, message: '请选择信息类型', trigger: 'change' }],
  product: [{ required: true, message: '请选择农产品', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

const orderRules = {
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
  delivery_address: [{ required: true, message: '请输入收货地址', trigger: 'blur' }],
  buyer_contact: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
}

// 判断采购商是否可以购买（看到农户的供应信息，且状态为进行中）
const canBuy = (item) => {
  return userRole.value === 'buyer' && item.info_type === 'supply' && item.status === 'active' && item.publisher !== currentUserId.value
}

// 判断农户是否可以接受（看到采购商的求购信息，且状态为进行中）
const canAccept = (item) => {
  return userRole.value === 'farmer' && item.info_type === 'demand' && item.status === 'active' && item.publisher !== currentUserId.value
}

const orderDialogTitle = computed(() => orderDialogType.value === 'buy' ? '购买商品' : '接受订单')

const loadProducts = async () => {
  try {
    const res = await getProducts()
    if (res && Array.isArray(res)) {
      products.value = res
    }
  } catch (error) {
    console.error('加载产品列表失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    const res = await getTradeInfoList(params)
    if (res.results) {
      tableData.value = res.results
      pagination.total = res.count
    } else if (Array.isArray(res)) {
      tableData.value = res
      pagination.total = res.length
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.info_type = ''
  searchForm.product = ''
  searchForm.status = 'active'
  searchForm.keyword = ''
  handleSearch()
}

const openPublishDialog = () => {
  isEdit.value = false
  publishForm.info_type = userRole.value === 'farmer' ? 'supply' : 'demand'
  publishForm.product = null
  publishForm.quantity = 1000
  publishForm.unit = '斤'
  publishForm.expected_price = null
  publishForm.origin = ''
  publishForm.contact_phone = ''
  publishForm.description = ''
  publishDialogVisible.value = true
}

const handleSubmit = async () => {
  if (!publishFormRef.value) return
  await publishFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      if (isEdit.value) {
        await updateTradeInfo(currentItem.value.id, publishForm)
        ElMessage.success('更新成功')
      } else {
        await createTradeInfo(publishForm)
        ElMessage.success('发布成功')
      }
      publishDialogVisible.value = false
      loadData()
    } catch (error) {
      const msg = error?.response?.data?.info_type?.[0] || error?.response?.data?.error || '操作失败'
      ElMessage.error(msg)
    } finally {
      submitLoading.value = false
    }
  })
}

const viewDetail = (row) => {
  currentItem.value = row
  detailDialogVisible.value = true
}

// 打开购买对话框
const openBuyDialog = (item) => {
  orderDialogType.value = 'buy'
  orderForm.trade_info_id = item.id
  orderForm.product_id = item.product
  orderForm.product_name = item.product_name
  orderForm.quantity = Number(item.quantity) || 100
  orderForm.max_quantity = Number(item.quantity) || 0
  orderForm.unit = item.unit || '斤'
  orderForm.unit_price = item.expected_price ? Number(item.expected_price) : null
  orderForm.delivery_address = ''
  orderForm.buyer_contact = userStore.userInfo?.phone || ''
  orderForm.remark = ''
  orderDialogVisible.value = true
}

// 打开接受订单对话框
const openAcceptDialog = (item) => {
  orderDialogType.value = 'accept'
  orderForm.trade_info_id = item.id
  orderForm.product_id = item.product
  orderForm.product_name = item.product_name
  orderForm.quantity = Number(item.quantity) || 100
  orderForm.max_quantity = Number(item.quantity) || 0
  orderForm.unit = item.unit || '斤'
  orderForm.unit_price = item.expected_price ? Number(item.expected_price) : null
  orderForm.delivery_address = ''
  orderForm.buyer_contact = userStore.userInfo?.phone || ''
  orderForm.remark = ''
  orderDialogVisible.value = true
}

// 提交订单
const handleSubmitOrder = async () => {
  if (!orderFormRef.value) return
  await orderFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const orderData = {
        trade_info: orderForm.trade_info_id,
        product: orderForm.product_id,
        quantity: orderForm.quantity,
        unit: orderForm.unit,
        unit_price: orderForm.unit_price,
        delivery_address: orderForm.delivery_address,
        buyer_contact: orderForm.buyer_contact,
        remark: orderForm.remark
      }

      if (orderDialogType.value === 'buy') {
        // 采购商购买
        await createOrder(orderData)
        ElMessage.success('购买成功')
      } else {
        // 农户接受订单
        await acceptOrder(orderData)
        ElMessage.success('订单已接受')
      }

      orderDialogVisible.value = false
      detailDialogVisible.value = false
      loadData()
    } catch (error) {
      const msg = error?.response?.data?.error || error?.response?.data?.detail || '操作失败'
      ElMessage.error(msg)
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条信息吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTradeInfo(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getStatusType = (status) => {
  const map = {
    active: 'success',
    completed: 'info',
    expired: 'warning',
    cancelled: 'danger'
  }
  return map[status] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadProducts()
  loadData()
})
</script>

<style scoped>
.trade-hall {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 22px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 15px;
}

.action-bar {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.trade-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.card-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.card-info {
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #909399;
}

.info-row .value {
  color: #303133;
}

.info-row .value.price {
  color: #F56C6C;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.detail-content {
  padding: 10px 0;
}

@media (max-width: 768px) {
  .trade-hall {
    padding: 10px;
  }

  .action-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
