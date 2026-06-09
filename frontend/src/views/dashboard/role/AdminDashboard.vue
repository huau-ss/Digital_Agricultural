<template>
  <div class="admin-dashboard">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 总览仪表盘 -->
      <el-tab-pane label="总览" name="overview">
        <h3 class="section-title">系统总览</h3>
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="8" :md="6" v-for="item in overviewStats" :key="item.label">
            <div class="stat-card" :style="{ borderLeft: `4px solid ${item.color}` }">
              <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="section-header">
          <h3 class="section-title">用户管理</h3>
          <div class="filter-row">
            <el-input v-model="userSearch" placeholder="搜索用户名/邮箱/手机号" style="width: 240px;" clearable @clear="loadUsers" @keyup.enter="loadUsers" />
            <el-select v-model="userRoleFilter" placeholder="角色" clearable style="width: 120px;" @change="loadUsers">
              <el-option label="全部" value="" />
              <el-option label="农户" value="farmer" />
              <el-option label="采购商" value="buyer" />
              <el-option label="管理员" value="admin" />
            </el-select>
            <el-select v-model="userStatusFilter" placeholder="状态" clearable style="width: 120px;" @change="loadUsers">
              <el-option label="全部" value="" />
              <el-option label="正常" value="active" />
              <el-option label="已禁用" value="inactive" />
              <el-option label="待审核" value="pending" />
            </el-select>
            <el-button type="primary" @click="loadUsers">查询</el-button>
          </div>
        </div>

        <el-table :data="userList" v-loading="userLoading" stripe style="width: 100%; margin-top: 16px;">
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="email" label="邮箱" min-width="160" />
          <el-table-column prop="role_display" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="roleTagType(row.role)" size="small">{{ row.role_display }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="140" />
          <el-table-column prop="is_active" label="账号状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '正常' : '已禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_approved" label="审核状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="!row.is_approved" type="warning" size="small">待审核</el-tag>
              <el-tag v-else type="success" size="small">已通过</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="170">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button v-if="!row.is_approved" type="success" size="small" link @click="handleUserAction(row, 'approve')">通过</el-button>
              <el-button v-if="!row.is_approved" type="danger" size="small" link @click="handleUserAction(row, 'reject')">拒绝</el-button>
              <el-button v-if="row.is_approved && row.is_active" type="warning" size="small" link @click="handleUserAction(row, 'disable')">禁用</el-button>
              <el-button v-if="row.is_approved && !row.is_active" type="success" size="small" link @click="handleUserAction(row, 'enable')">启用</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="userPage"
          :page-size="userPageSize"
          :total="userTotal"
          layout="total, prev, pager, next"
          style="margin-top: 16px; justify-content: flex-end;"
          @current-change="loadUsers"
        />
      </el-tab-pane>

      <!-- 预警管理 -->
      <el-tab-pane label="预警管理" name="warnings">
        <h3 class="section-title">预警参数配置</h3>
        <el-form :model="warningSettings" label-width="140px" style="max-width: 500px; margin-top: 16px;">
          <el-form-item label="价格跌幅阈值 (%)">
            <el-input-number v-model="warningSettings.price_drop_threshold" :min="0" :max="100" :step="1" />
            <span style="margin-left: 8px; color: #909399;">低于此值触发跌价预警</span>
          </el-form-item>
          <el-form-item label="价格涨幅阈值 (%)">
            <el-input-number v-model="warningSettings.price_rise_threshold" :min="0" :max="100" :step="1" />
            <span style="margin-left: 8px; color: #909399;">高于此值触发涨价预警</span>
          </el-form-item>
          <el-form-item label="推送策略">
            <el-select v-model="warningSettings.push_strategy" style="width: 200px;">
              <el-option label="全员推送" value="all" />
              <el-option label="仅农户" value="farmers_only" />
              <el-option label="仅采购商" value="buyers_only" />
              <el-option label="关闭推送" value="none" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveWarningSettings" :loading="settingsLoading">保存设置</el-button>
            <el-button @click="loadWarningSettings">重置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 数据管理 -->
      <el-tab-pane label="数据管理" name="data">
        <h3 class="section-title">数据管理</h3>
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="8">
            <div class="stat-card" style="border-left: 4px solid #409EFF;">
              <div class="stat-value">{{ dataStats.total }}</div>
              <div class="stat-label">总记录数</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="8">
            <div class="stat-card" style="border-left: 4px solid #67C23A;">
              <div class="stat-value">{{ dataStats.clean }}</div>
              <div class="stat-label">正常记录</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="8">
            <div class="stat-card" style="border-left: 4px solid #E6A23C;">
              <div class="stat-value">{{ dataStats.outliers }}</div>
              <div class="stat-label">异常记录</div>
            </div>
          </el-col>
        </el-row>

        <div style="margin-top: 24px;">
          <h4>手动任务</h4>
          <div style="margin-top: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <el-date-picker
              v-model="collectDate"
              type="date"
              placeholder="选择采集日期（默认昨天）"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="(date) => date >= new Date()"
              style="width: 200px;"
            />
            <el-button type="primary" @click="handleCollect(collectDate)" :loading="collectLoading">触发数据采集</el-button>
            <el-button type="warning" @click="handleClean" :loading="cleanLoading">触发数据清洗</el-button>
          </div>
          <p v-if="taskResult" style="margin-top: 12px; color: #67C23A; font-size: 14px;">{{ taskResult }}</p>
        </div>
      </el-tab-pane>

      <!-- 模型管理 -->
      <el-tab-pane label="模型管理" name="models">
        <h3 class="section-title">LSTM 模型状态</h3>
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="6">
            <div class="stat-card" style="border-left: 4px solid #409EFF;">
              <div class="stat-value">{{ modelStats.total }}</div>
              <div class="stat-label">产品总数</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card" style="border-left: 4px solid #67C23A;">
              <div class="stat-value">{{ modelStats.trained }}</div>
              <div class="stat-label">已训练模型</div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card" style="border-left: 4px solid #909399;">
              <div class="stat-value">{{ modelStats.total - modelStats.trained }}</div>
              <div class="stat-label">未训练</div>
            </div>
          </el-col>
        </el-row>

        <el-table :data="modelList" v-loading="modelLoading" stripe style="margin-top: 16px;" :max-height="400">
          <el-table-column prop="product_name" label="产品" min-width="120" />
          <el-table-column prop="category" label="类别" width="100" />
          <el-table-column label="模型状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.model_exists ? 'success' : 'info'" size="small">
                {{ row.model_exists ? '已训练' : '未训练' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="模型大小" width="120">
            <template #default="{ row }">
              {{ row.model_size_bytes > 0 ? formatBytes(row.model_size_bytes) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="RMSE" width="100">
            <template #default="{ row }">
              {{ typeof row.metrics?.rmse === 'number' ? row.metrics.rmse.toFixed(4) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="MAE" width="100">
            <template #default="{ row }">
              {{ typeof row.metrics?.mae === 'number' ? row.metrics.mae.toFixed(4) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="R2" width="100">
            <template #default="{ row }">
              {{ typeof row.metrics?.r2 === 'number' ? row.metrics.r2.toFixed(4) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="MAPE (%)" width="100">
            <template #default="{ row }">
              {{ typeof row.metrics?.mape === 'number' ? row.metrics.mape.toFixed(2) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
// =============================================
// 引入 Vue 组合式 API 和第三方库
// =============================================
import { ref, reactive, onMounted, watch } from 'vue'        // Vue 3 组合式 API
import { useRoute } from 'vue-router'                        // 路由操作
import { ElMessage, ElMessageBox } from 'element-plus'      // 消息提示和确认框
// 引入管理员模块的 API 方法
import {
  getUserList, getUserStats, userAction,                   // 用户管理 API
  getAdminSettings, updateAdminSettings,                  // 系统设置 API
  triggerDataCollection, triggerDataCleaning, getCleanedStats,  // 数据管理 API
  getModelRegistry                                         // 模型管理 API
} from '@/api/admin'

// =============================================
// Tab 页签状态管理
// =============================================
// activeTab: 控制当前显示的 Tab 页，取值：overview(总览)、users(用户管理)、
//            warnings(预警管理)、data(数据管理)、models(模型管理)
const activeTab = ref('overview')

// =============================================
// 总览模块
// =============================================
// overviewStats: 总览页面的统计数据，包含用户数量、审核状态、阈值配置等
// 数组中每个对象包含：label(标签)、value(数值)、color(颜色，用于样式区分)
const overviewStats = ref([])

/**
 * 加载总览数据
 * 使用 Promise.all 并行请求多个 API，提升加载速度
 * 任何一个请求失败不影响其他数据展示（使用 catch 返回 null）
 */
async function loadOverview() {
  try {
    // 并行请求：用户统计、系统设置、数据清洗统计
    const [userRes, settingsRes, cleanedRes] = await Promise.all([
      getUserStats().catch(() => null),        // 失败返回 null，避免中断
      getAdminSettings().catch(() => null),
      getCleanedStats().catch(() => null),
    ])

    // 安全获取数据，避免后端返回空数据导致报错
    const u = userRes?.data || {}    // 用户统计数据
    const s = settingsRes?.data || {}  // 系统设置数据
    const c = cleanedRes?.data || {}   // 数据清洗统计

    // 构建设计器展示数据，每项包含标签、数值、颜色
    overviewStats.value = [
      { label: '用户总数', value: u.total || 0, color: '#409EFF' },           // 蓝色
      { label: '待审核', value: u.pending_approval || 0, color: '#E6A23C' },  // 橙色
      { label: '农户', value: u.farmer_count || 0, color: '#67C23A' },        // 绿色
      { label: '采购商', value: u.buyer_count || 0, color: '#F56C6C' },       // 红色
      { label: '跌价阈值', value: `${s.price_drop_threshold ?? 10}%`, color: '#909399' },   // 灰色
      { label: '涨价阈值', value: `${s.price_rise_threshold ?? 15}%`, color: '#909399' },   // 灰色
      { label: '清洗数据', value: c.total_count || 0, color: '#409EFF' },     // 蓝色
      { label: '异常数据', value: c.outlier_count || 0, color: '#F56C6C' },    // 红色
    ]
  } catch (e) {
    console.error('loadOverview failed:', e)
  }
}

// =============================================
// 用户管理模块
// =============================================
// userList: 用户列表数据
// userLoading: 表格加载状态，用于控制 loading 动画
// userSearch: 搜索关键词（用户名/邮箱/手机号）
// userRoleFilter: 角色筛选（farmer/buyer/admin）
// userStatusFilter: 状态筛选（active/inactive/pending）
// userPage/userPageSize: 分页参数
// userTotal: 总用户数，用于分页显示
const userList = ref([])
const userLoading = ref(false)
const userSearch = ref('')
const userRoleFilter = ref('')
const userStatusFilter = ref('')
const userPage = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)

/**
 * 加载用户列表
 * 支持搜索、筛选、分页
 * 请求参数根据筛选条件动态构建
 */
async function loadUsers() {
  userLoading.value = true  // 开始加载，显示 loading
  try {
    // 构建查询参数
    const params = {
      page: userPage.value,              // 当前页码
      page_size: userPageSize.value,     // 每页条数
      search: userSearch.value || undefined,      // 搜索关键词（空值不传）
      role: userRoleFilter.value || undefined,    // 角色筛选（空值不传）
    }

    // 状态筛选需要特殊处理：将中文筛选条件转换为 API 参数
    if (userStatusFilter.value === 'active') {
      params.is_active = 'true'          // 正常用户
    } else if (userStatusFilter.value === 'inactive') {
      params.is_active = 'false'         // 已禁用用户
    } else if (userStatusFilter.value === 'pending') {
      params.is_approved = 'false'       // 待审核用户
    }
    // 如果是'全部'，不添加任何筛选参数

    const res = await getUserList(params)
    // 兼容两种返回格式（DRF 自动分页 / 普通列表）
    userList.value = res.results || res.data || []
    userTotal.value = res.count || res.total || userList.value.length
  } catch (e) {
    ElMessage.error('加载用户列表失败')
  } finally {
    userLoading.value = false  // 加载完成，关闭 loading
  }
}

/**
 * 根据用户角色返回对应的标签颜色类型
 * farmer: 默认蓝色、buyer: 绿色、admin: 红色、其他: 灰色
 * @param {string} role - 用户角色
 * @returns {string} - Element Plus 的 tag type
 */
function roleTagType(role) {
  const map = { farmer: '', buyer: 'success', admin: 'danger' }
  return map[role] || 'info'
}

/**
 * 格式化日期字符串
 * 将 ISO 格式的时间转换为 'YYYY-MM-DD HH:mm:ss' 格式
 * @param {string} dateStr - ISO 格式的日期字符串
 * @returns {string} - 格式化后的日期
 */
function formatDate(dateStr) {
  if (!dateStr) return '-'
  // 截取前19位（精确到秒），将 T 替换为空格
  return dateStr.slice(0, 19).replace('T', ' ')
}

/**
 * 处理用户操作（启用/禁用/审核通过/审核拒绝）
 * @param {Object} row - 当前行的用户数据
 * @param {string} action - 操作类型：enable/disable/approve/reject
 */
async function handleUserAction(row, action) {
  // 操作类型对应的中文标签
  const actionLabels = { enable: '启用', disable: '禁用', approve: '通过审核', reject: '拒绝' }

  // 弹出确认框，用户取消则直接返回
  try {
    await ElMessageBox.confirm(
      `确定要${actionLabels[action]}用户「${row.username}」吗？`,
      '操作确认'
    )
  } catch {
    return  // 用户点击取消
  }

  try {
    // 发送操作请求
    await userAction({ user_id: row.id, action })
    ElMessage.success(`${actionLabels[action]}成功`)
    loadUsers()  // 刷新列表
  } catch (e) {
    ElMessage.error(e.message || `${actionLabels[action]}失败`)
  }
}

// =============================================
// 预警管理模块
// =============================================
// warningSettings: 预警参数配置
// price_drop_threshold: 价格跌幅阈值（百分比），低于此值触发跌价预警
// price_rise_threshold: 价格涨幅阈值（百分比），高于此值触发涨价预警
// push_strategy: 推送策略，可选值：all(全员)、farmers_only(仅农户)、buyers_only(仅采购商)、none(关闭)
const warningSettings = reactive({
  price_drop_threshold: 10,    // 默认跌价阈值 10%
  price_rise_threshold: 15,   // 默认涨价阈值 15%
  push_strategy: 'all',       // 默认全员推送
})
const settingsLoading = ref(false)  // 保存按钮的加载状态

/**
 * 加载预警设置
 * 从后端获取当前配置，填充到表单中
 */
async function loadWarningSettings() {
  try {
    const res = await getAdminSettings()
    const d = res.data || res  // 兼容两种返回格式
    // 使用空值合并运算符，如果后端返回 null/undefined 则使用默认值
    warningSettings.price_drop_threshold = d.price_drop_threshold ?? 10
    warningSettings.price_rise_threshold = d.price_rise_threshold ?? 15
    warningSettings.push_strategy = d.push_strategy ?? 'all'
  } catch (e) {
    ElMessage.error('加载设置失败')
  }
}

/**
 * 保存预警设置
 * 将表单数据提交到后端
 */
async function saveWarningSettings() {
  settingsLoading.value = true  // 显示加载状态，防止重复提交
  try {
    await updateAdminSettings(warningSettings)
    ElMessage.success('设置保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    settingsLoading.value = false
  }
}

// =============================================
// 数据管理模块
// =============================================
// dataStats: 数据统计，包含总记录数、正常记录数、异常记录数
// collectLoading/cleanLoading: 按钮加载状态
// taskResult: 任务执行结果提示文本
// collectDate: 数据采集的目标日期，默认昨天
const dataStats = reactive({ total: 0, clean: 0, outliers: 0 })
const collectLoading = ref(false)
const cleanLoading = ref(false)
const taskResult = ref('')
const collectDate = ref('')

/**
 * 加载数据统计
 */
async function loadDataStats() {
  try {
    const res = await getCleanedStats()
    const d = res.data || res
    dataStats.total = d.total_count || 0    // 总记录数
    dataStats.clean = d.clean_count || 0    // 正常记录数
    dataStats.outliers = d.outlier_count || 0  // 异常记录数
  } catch (e) {
    console.error('loadDataStats failed:', e)
  }
}

/**
 * 触发数据采集任务
 * 调用后端爬虫脚本，开始采集农产品价格数据
 */
async function handleCollect(date) {
  collectLoading.value = true
  taskResult.value = ''  // 清空上一次的结果
  try {
    const params = date ? { date } : {}
    const res = await triggerDataCollection(params)
    const d = res.data || res
    taskResult.value = `采集完成：处理 ${d.products_processed ?? 0} 个产品，新增 ${d.new_records ?? 0} 条价格记录`
    ElMessage.success(taskResult.value)
    loadDataStats()  // 刷新统计数据
  } catch (e) {
    ElMessage.error('触发采集失败')
  } finally {
    collectLoading.value = false
  }
}

/**
 * 触发数据清洗任务
 * 对最近30天的数据进行清洗，标记异常值
 * @param {number} days_back - 回溯天数，默认30天
 */
async function handleClean() {
  cleanLoading.value = true
  taskResult.value = ''
  try {
    // 发送清洗请求，指定回溯30天
    const res = await triggerDataCleaning({ days_back: 30 })
    const d = res.data || res
    // 显示清洗结果：处理了多少条，标记了多少异常
    taskResult.value = `清洗完成：处理 ${d.processed ?? 0} 条，标记 ${d.outliers_marked ?? 0} 条异常`
    ElMessage.success(taskResult.value)
    loadDataStats()  // 刷新统计数据
  } catch (e) {
    ElMessage.error('触发清洗失败: ' + (e.message || ''))
  } finally {
    cleanLoading.value = false
  }
}

// =============================================
// 模型管理模块
// =============================================
// modelStats: 模型统计，包含产品总数、已训练模型数
// modelList: 模型列表数据
const modelStats = reactive({ total: 0, trained: 0 })
const modelList = ref([])
const modelLoading = ref(false)

/**
 * 加载模型注册表
 * 获取所有农产品的 LSTM 模型训练状态和评估指标
 */
async function loadModelRegistry() {
  modelLoading.value = true
  try {
    const res = await getModelRegistry()
    const d = res.data || res
    modelStats.total = d.total_products || 0   // 产品总数
    modelStats.trained = d.trained_models || 0  // 已训练模型数
    modelList.value = d.products || []        // 产品列表
  } catch (e) {
    ElMessage.error('加载模型列表失败')
  } finally {
    modelLoading.value = false
  }
}

/**
 * 格式化文件大小
 * 将字节数转换为人类可读的单位（B/KB/MB）
 * @param {number} bytes - 字节数
 * @returns {string} - 格式化后的大小字符串
 */
function formatBytes(bytes) {
  if (!bytes) return '-'              // 空值返回 '-'
  if (bytes < 1024) return bytes + ' B'                    // 小于1KB
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'  // 小于1MB
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'         // MB
}

// =============================================
// 路由与生命周期
// =============================================
const route = useRoute()

/**
 * 组件挂载时的初始化
 * 1. 检查路由路径，如果是 /dashboard/users 则显示用户管理 Tab
 * 2. 加载所有模块的初始数据
 */
onMounted(() => {
  // 根据路由切换 tab
  if (route.path === '/dashboard/users') {
    activeTab.value = 'users'
  }

  // 加载各模块数据
  loadOverview()          // 总览数据
  loadUsers()             // 用户列表
  loadWarningSettings()   // 预警设置
  loadDataStats()         // 数据统计
  loadModelRegistry()     // 模型列表
})

/**
 * 监听路由变化
 * 当路由路径变化时，更新当前激活的 Tab
 * 用于处理用户通过侧边栏导航切换 Tab 的场景
 */
watch(() => route.path, (path) => {
  if (path === '/dashboard/users') {
    activeTab.value = 'users'
  }
})
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  min-height: calc(100vh - 120px);
}

.section-title {
  margin: 0 0 16px;
  font-size: 16px;
  color: #303133;
  border-left: 4px solid #409EFF;
  padding-left: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header .section-title {
  margin: 0;
}

.filter-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 12px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}
</style>
