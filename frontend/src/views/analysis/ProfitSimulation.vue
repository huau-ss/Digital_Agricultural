<template>
  <div class="profit-simulation">
    <div class="page-header">
      <h2>{{ isBuyer ? '采购成本分析' : '利润模拟' }}</h2>
      <p class="subtitle">{{ isBuyer ? '基于 LSTM 价格预测的采购成本与销售收益分析' : '基于 LSTM 价格预测的种植成本与利润分析' }}</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧表单 -->
      <el-col :xs="24" :lg="10">
        <el-card class="form-card">
          <template #header>
            <div class="card-title">
              <el-icon><Edit /></el-icon>
              <span>{{ isBuyer ? '采购参数设置' : '种植成本参数' }}</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="110px"
            label-position="left"
          >
            <!-- 农户种植成本表单 -->
            <template v-if="!isBuyer">
              <el-form-item label="选择农产品" prop="product_id">
                <el-select
                  v-model="form.product_id"
                  placeholder="请选择农产品"
                  style="width: 100%"
                  @change="onProductChange"
                >
                  <el-option
                    v-for="product in products"
                    :key="product.id"
                    :label="product.name"
                    :value="product.id"
                  >
                    <span>{{ product.name }}</span>
                    <span class="category-tag">{{ product.category }}</span>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="种植面积" prop="area">
                <el-input-number
                  v-model="form.area"
                  :min="0.1"
                  :max="10000"
                  :precision="2"
                  :step="1"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>亩</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="种子成本" prop="seed_cost">
                <el-input-number
                  v-model="form.seed_cost"
                  :min="0"
                  :precision="2"
                  :step="10"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="化肥成本" prop="fertilizer_cost">
                <el-input-number
                  v-model="form.fertilizer_cost"
                  :min="0"
                  :precision="2"
                  :step="50"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="农药成本" prop="pesticide_cost">
                <el-input-number
                  v-model="form.pesticide_cost"
                  :min="0"
                  :precision="2"
                  :step="20"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="人工成本" prop="labor_cost">
                <el-input-number
                  v-model="form.labor_cost"
                  :min="0"
                  :precision="2"
                  :step="100"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="其他成本" prop="other_cost">
                <el-input-number
                  v-model="form.other_cost"
                  :min="0"
                  :precision="2"
                  :step="50"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="预估产量" prop="yield_per_acre">
                <el-input-number
                  v-model="form.yield_per_acre"
                  :min="0"
                  :precision="1"
                  :step="50"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>斤/亩</span>
                  </template>
                </el-input-number>
              </el-form-item>
            </template>

            <!-- 采购商采购成本表单 -->
            <template v-else>
              <el-form-item label="选择农产品" prop="product_id">
                <el-select
                  v-model="form.product_id"
                  placeholder="请选择农产品"
                  style="width: 100%"
                  @change="onProductChange"
                >
                  <el-option
                    v-for="product in products"
                    :key="product.id"
                    :label="product.name"
                    :value="product.id"
                  >
                    <span>{{ product.name }}</span>
                    <span class="category-tag">{{ product.category }}</span>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="采购数量" prop="area">
                <el-input-number
                  v-model="form.area"
                  :min="1"
                  :max="100000"
                  :precision="0"
                  :step="100"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>斤</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="采购单价" prop="seed_cost">
                <el-input-number
                  v-model="form.seed_cost"
                  :min="0"
                  :precision="2"
                  :step="0.1"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元/斤</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="物流成本" prop="fertilizer_cost">
                <el-input-number
                  v-model="form.fertilizer_cost"
                  :min="0"
                  :precision="2"
                  :step="50"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="仓储成本" prop="pesticide_cost">
                <el-input-number
                  v-model="form.pesticide_cost"
                  :min="0"
                  :precision="2"
                  :step="20"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="损耗率" prop="labor_cost">
                <el-input-number
                  v-model="form.labor_cost"
                  :min="0"
                  :max="50"
                  :precision="1"
                  :step="1"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>%</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="预期售价" prop="other_cost">
                <el-input-number
                  v-model="form.other_cost"
                  :min="0"
                  :precision="2"
                  :step="0.1"
                  style="width: 100%"
                >
                  <template #suffix>
                    <span>元/斤</span>
                  </template>
                </el-input-number>
              </el-form-item>
            </template>

            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="calculateProfit"
                style="width: 100%"
                size="large"
              >
                <el-icon v-if="!loading"><Search /></el-icon>
                {{ loading ? '分析中...' : (isBuyer ? '计算收益' : '计算利润') }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧结果 -->
      <el-col :xs="24" :lg="14">
        <!-- 价格预测图 -->
        <el-card class="chart-card" v-if="predictionResult">
          <template #header>
            <div class="card-title">
              <el-icon><TrendCharts /></el-icon>
              <span>LSTM 价格预测</span>
              <el-tag size="small" type="info" style="margin-left: 10px">
                预测周期: {{ predictionDays }} 天
              </el-tag>
            </div>
          </template>
          <div ref="predictionChartRef" style="width: 100%; height: 280px;"></div>
        </el-card>

        <!-- 利润对比卡片 -->
        <el-row :gutter="15" v-if="profitResult">
          <!-- 农户视角：当前出售 / 择期出售 -->
          <template v-if="!isBuyer">
            <el-col :xs="24" :sm="12">
              <div class="profit-card current">
                <div class="profit-header">
                  <el-icon><Sell /></el-icon>
                  <span>当前出售</span>
                </div>
                <div class="profit-price">
                  <span class="label">当前均价</span>
                  <span class="value">{{ profitResult.current_price }} 元/斤</span>
                </div>
                <div class="profit-amount">
                  <span class="label">预期利润</span>
                  <span class="value" :class="{ negative: profitResult.current_profit < 0 }">
                    {{ formatNumber(profitResult.current_profit) }} 元
                  </span>
                </div>
                <div class="profit-rate">
                  <span class="label">利润率</span>
                  <span class="value" :class="{ negative: profitResult.current_rate < 0 }">
                    {{ profitResult.current_rate }}%
                  </span>
                </div>
              </div>
            </el-col>

            <el-col :xs="24" :sm="12">
              <div class="profit-card future">
                <div class="profit-header">
                  <el-icon><Clock /></el-icon>
                  <span>择期出售</span>
                  <el-tag size="small" type="warning" style="margin-left: auto">
                    预测高点
                  </el-tag>
                </div>
                <div class="profit-price">
                  <span class="label">预测最高价</span>
                  <span class="value highlight">{{ profitResult.predicted_max_price }} 元/斤</span>
                </div>
                <div class="profit-amount">
                  <span class="label">预期利润</span>
                  <span class="value" :class="{ negative: profitResult.predicted_profit < 0 }">
                    {{ formatNumber(profitResult.predicted_profit) }} 元
                  </span>
                </div>
                <div class="profit-rate">
                  <span class="label">利润率</span>
                  <span class="value" :class="{ negative: profitResult.predicted_rate < 0 }">
                    {{ profitResult.predicted_rate }}%
                  </span>
                </div>
              </div>
            </el-col>
          </template>

          <!-- 采购商视角：立即采购 / 择期采购 -->
          <template v-else>
            <el-col :xs="24" :sm="12">
              <div class="profit-card current">
                <div class="profit-header">
                  <el-icon><ShoppingCartFull /></el-icon>
                  <span>立即采购</span>
                </div>
                <div class="profit-price">
                  <span class="label">当前均价</span>
                  <span class="value">{{ profitResult.current_price }} 元/斤</span>
                </div>
                <div class="profit-amount">
                  <span class="label">预估收益</span>
                  <span class="value" :class="{ negative: profitResult.current_profit < 0 }">
                    {{ formatNumber(profitResult.current_profit) }} 元
                  </span>
                </div>
                <div class="profit-rate">
                  <span class="label">收益率</span>
                  <span class="value" :class="{ negative: profitResult.current_rate < 0 }">
                    {{ profitResult.current_rate }}%
                  </span>
                </div>
              </div>
            </el-col>

            <el-col :xs="24" :sm="12">
              <div class="profit-card future">
                <div class="profit-header">
                  <el-icon><Sell /></el-icon>
                  <span>择期采购</span>
                  <el-tag size="small" type="warning" style="margin-left: auto">
                    预测低点
                  </el-tag>
                </div>
                <div class="profit-price">
                  <span class="label">预测最低价</span>
                  <span class="value highlight">{{ profitResult.predicted_max_price }} 元/斤</span>
                </div>
                <div class="profit-amount">
                  <span class="label">预估收益</span>
                  <span class="value" :class="{ negative: profitResult.predicted_profit < 0 }">
                    {{ formatNumber(profitResult.predicted_profit) }} 元
                  </span>
                </div>
                <div class="profit-rate">
                  <span class="label">收益率</span>
                  <span class="value" :class="{ negative: profitResult.predicted_rate < 0 }">
                    {{ profitResult.predicted_rate }}%
                  </span>
                </div>
              </div>
            </el-col>
          </template>
        </el-row>

        <!-- 成本明细 -->
        <el-card class="cost-card" v-if="profitResult">
          <template #header>
            <div class="card-title">
              <el-icon><Coin /></el-icon>
              <span>{{ isBuyer ? '采购成本明细' : '种植成本明细' }}</span>
            </div>
          </template>
          <!-- 农户成本明细 -->
          <div class="cost-summary" v-if="!isBuyer">
            <div class="cost-row">
              <span class="cost-label">种植总面积</span>
              <span class="cost-value">{{ form.area }} 亩</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">预估总产量</span>
              <span class="cost-value">{{ profitResult.total_yield }} 斤</span>
            </div>
            <div class="cost-divider"></div>
            <div class="cost-row">
              <span class="cost-label">种子成本</span>
              <span class="cost-value">{{ form.seed_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">化肥成本</span>
              <span class="cost-value">{{ form.fertilizer_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">农药成本</span>
              <span class="cost-value">{{ form.pesticide_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">人工成本</span>
              <span class="cost-value">{{ form.labor_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">其他成本</span>
              <span class="cost-value">{{ form.other_cost }} 元</span>
            </div>
            <div class="cost-divider"></div>
            <div class="cost-row total">
              <span class="cost-label">总成本</span>
              <span class="cost-value">{{ formatNumber(profitResult.total_cost) }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">单位成本</span>
              <span class="cost-value">{{ profitResult.unit_cost }} 元/斤</span>
            </div>
          </div>
          <!-- 采购商成本明细 -->
          <div class="cost-summary" v-else>
            <div class="cost-row">
              <span class="cost-label">采购数量</span>
              <span class="cost-value">{{ form.area }} 斤</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">采购单价</span>
              <span class="cost-value">{{ form.seed_cost }} 元/斤</span>
            </div>
            <div class="cost-divider"></div>
            <div class="cost-row">
              <span class="cost-label">采购总价</span>
              <span class="cost-value">{{ formatNumber(profitResult.purchase_total || 0) }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">物流成本</span>
              <span class="cost-value">{{ form.fertilizer_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">仓储成本</span>
              <span class="cost-value">{{ form.pesticide_cost }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">损耗率</span>
              <span class="cost-value">{{ form.labor_cost }}%</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">有效数量</span>
              <span class="cost-value">{{ profitResult.effective_quantity || 0 }} 斤</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">预期售价</span>
              <span class="cost-value">{{ form.other_cost }} 元/斤</span>
            </div>
            <div class="cost-divider"></div>
            <div class="cost-row total">
              <span class="cost-label">总采购成本</span>
              <span class="cost-value">{{ formatNumber(profitResult.total_cost) }} 元</span>
            </div>
            <div class="cost-row">
              <span class="cost-label">单位采购成本</span>
              <span class="cost-value">{{ profitResult.unit_cost }} 元/斤</span>
            </div>
          </div>
        </el-card>

        <!-- 经营建议 -->
        <el-card class="advice-card" v-if="advice">
          <template #header>
            <div class="card-title">
              <el-icon><Warning /></el-icon>
              <span>{{ isBuyer ? '采购建议' : '经营建议' }}</span>
            </div>
          </template>
          <div class="advice-content">
            <p class="advice-text">{{ advice }}</p>
            <div class="advice-highlight" v-if="profitResult">
              <template v-if="!isBuyer">
                <div class="highlight-row">
                  <span>建议推迟天数:</span>
                  <strong>{{ profitResult.suggested_delay_days }} 天</strong>
                </div>
                <div class="highlight-row">
                  <span>预估额外收益:</span>
                  <strong class="profit-highlight">
                    +{{ formatNumber(profitResult.profit_diff) }} 元
                  </strong>
                </div>
              </template>
              <template v-else>
                <div class="highlight-row">
                  <span>建议采购时机:</span>
                  <strong>{{ profitResult.suggested_delay_days }} 天后</strong>
                </div>
                <div class="highlight-row">
                  <span>预估节省成本:</span>
                  <strong class="profit-highlight">
                    {{ formatNumber(Math.abs(profitResult.profit_diff)) }} 元
                  </strong>
                </div>
              </template>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Edit, Search, TrendCharts, Sell, Clock, Coin, Warning, ShoppingCartFull } from '@element-plus/icons-vue'
import { getProducts } from '@/api/dataCollection'
import { getPricePrediction } from '@/api/prediction'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const isBuyer = computed(() => userStore.userRole === 'buyer')

const loading = ref(false)
const products = ref([])
const formRef = ref(null)
const predictionChartRef = ref(null)
let predictionChart = null

const predictionDays = ref(14)

const form = reactive({
  product_id: null,
  area: 10,
  seed_cost: 500,
  fertilizer_cost: 1500,
  pesticide_cost: 800,
  labor_cost: 3000,
  other_cost: 500,
  yield_per_acre: 3000
})

// 验证规则（根据角色动态计算）
const rules = computed(() => {
  if (isBuyer.value) {
    return {
      product_id: [{ required: true, message: '请选择农产品', trigger: 'change' }],
      area: [{ required: true, message: '请输入采购数量', trigger: 'blur' }]
    }
  } else {
    return {
      product_id: [{ required: true, message: '请选择农产品', trigger: 'change' }],
      area: [{ required: true, message: '请输入种植面积', trigger: 'blur' }],
      yield_per_acre: [{ required: true, message: '请输入预估产量', trigger: 'blur' }]
    }
  }
})

const predictionResult = ref(null)
const profitResult = ref(null)
const advice = ref('')

// 加载农产品列表
const loadProducts = async () => {
  try {
    const res = await getProducts()
    if (res && Array.isArray(res)) {
      products.value = res
      if (res.length > 0) {
        form.product_id = res[0].id
      }
    }
  } catch (error) {
    console.error('加载产品列表失败:', error)
  }
}

// 获取价格预测
const fetchPrediction = async () => {
  if (!form.product_id) {
    ElMessage.warning('请选择农产品')
    return null
  }
  try {
    const res = await getPricePrediction({
      product_id: form.product_id,
      days: predictionDays.value
    })
    console.log('API response:', res)
    if (res && res.success) {
      predictionResult.value = res
      await nextTick()
      initPredictionChart()
      return res
    } else if (res && res.error) {
      ElMessage.warning(res.error)
      return null
    } else {
      ElMessage.error('获取预测数据失败')
      return null
    }
  } catch (error) {
    console.error('获取预测数据失败:', error)
    ElMessage.error('获取预测数据失败，请检查网络或后端服务')
    return null
  }
}

// 根据角色设置表单默认值
const initFormDefaults = () => {
  if (isBuyer.value) {
    form.area = 1000      // 采购数量：斤
    form.seed_cost = 2.0  // 采购单价：元/斤
    form.fertilizer_cost = 200  // 物流成本
    form.pesticide_cost = 100   // 仓储成本
    form.labor_cost = 5        // 损耗率%
    form.other_cost = 3.5      // 预期售价
    form.yield_per_acre = 0    // 不使用
  } else {
    form.area = 10         // 种植面积：亩
    form.seed_cost = 500   // 种子成本
    form.fertilizer_cost = 1500  // 化肥成本
    form.pesticide_cost = 800    // 农药成本
    form.labor_cost = 3000       // 人工成本
    form.other_cost = 500        // 其他成本
    form.yield_per_acre = 3000   // 预估产量：斤/亩
  }
}

// 计算利润
const calculateProfit = async () => {
  if (!form.product_id) {
    ElMessage.warning('请选择农产品')
    return
  }

  loading.value = true
  profitResult.value = null
  advice.value = ''

  try {
    // 获取预测数据
    const res = await fetchPrediction()
    if (!res) {
      return
    }

    // 提取当前均价（历史数据最后一笔）
    const historical = res.historical || { dates: [], prices: [] }
    const prediction = res.prediction || { dates: [], prices: [] }

    const currentPrice = historical.prices?.length > 0
      ? historical.prices[historical.prices.length - 1] / 2  // 转为斤
      : 0

    const predictedPrices = prediction.prices || []

    let predictedMaxPrice = 0
    let suggestedDelayDays = 0
    let adviceText = ''
    let currentProfit = 0
    let currentRate = 0
    let predictedProfit = 0
    let predictedRate = 0
    let profitDiff = 0
    let totalCost = 0
    let unitCost = 0
    let totalYield = 0

    if (isBuyer.value) {
      // ========================================
      // 采购商视角：采购成本分析
      // ========================================

      // 采购数量（斤）
      const purchaseQuantity = form.area
      // 采购单价（元/斤）
      const purchaseUnitPrice = form.seed_cost
      // 采购总价
      const purchaseTotal = purchaseQuantity * purchaseUnitPrice
      // 物流成本
      const logisticsCost = form.fertilizer_cost
      // 仓储成本
      const storageCost = form.pesticide_cost
      // 损耗率
      const lossRate = form.labor_cost / 100
      // 损耗后有效数量
      const effectiveQuantity = purchaseQuantity * (1 - lossRate)
      // 预期售价（元/斤）
      const expectedSalePrice = form.other_cost

      // 总采购成本 = 采购总价 + 物流 + 仓储
      totalCost = purchaseTotal + logisticsCost + storageCost
      // 单位采购成本
      unitCost = effectiveQuantity > 0 ? totalCost / effectiveQuantity : 0

      // 预测最低价（采购商希望在低价时买入）
      predictedMaxPrice = predictedPrices.length > 0
        ? Math.min(...predictedPrices) / 2
        : currentPrice

      // 找到预测最低价对应的天数
      if (predictedPrices.length > 0) {
        const minIdx = predictedPrices.indexOf(Math.min(...predictedPrices))
        suggestedDelayDays = minIdx + 1
      }

      // 立即采购时的预估收益（按当前价格采购，按预期售价销售）
      const currentPurchaseCost = purchaseTotal + logisticsCost + storageCost
      const currentSaleRevenue = currentPrice * effectiveQuantity
      currentProfit = currentSaleRevenue - currentPurchaseCost
      currentRate = currentPurchaseCost > 0 ? (currentProfit / currentPurchaseCost * 100) : 0

      // 择期待购时的预估收益（按预测最低价采购，按预期售价销售）
      const predictedPurchaseCost = predictedMaxPrice * purchaseQuantity + logisticsCost + storageCost
      const predictedSaleRevenue = expectedSalePrice * effectiveQuantity
      predictedProfit = predictedSaleRevenue - predictedPurchaseCost
      predictedRate = predictedPurchaseCost > 0 ? (predictedProfit / predictedPurchaseCost * 100) : 0

      // 节省的成本差异（正值表示择期待购更划算）
      profitDiff = currentPurchaseCost - predictedPurchaseCost

      // 生成采购建议
      if (profitDiff > 0) {
        const percentDecrease = ((currentPrice - predictedMaxPrice) / currentPrice * 100).toFixed(1)
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格呈下降趋势。` +
                     `预测最低价将达到 ${predictedMaxPrice.toFixed(2)} 元/斤（当前均价 ${currentPrice.toFixed(2)} 元/斤，降幅约 ${percentDecrease}%）。` +
                     `建议推迟 ${suggestedDelayDays} 天采购，预计可节省成本 ${formatNumber(profitDiff)} 元。`
      } else if (profitDiff < 0) {
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格可能略有上涨。` +
                     `当前价格处于相对低点 ${currentPrice.toFixed(2)} 元/斤，建议立即采购锁定低成本。`
      } else {
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格走势平稳。` +
                     `可结合实际情况灵活安排采购时间。`
      }

      profitResult.value = {
        current_price: currentPrice.toFixed(2),
        predicted_max_price: predictedMaxPrice.toFixed(2),
        total_yield: Math.round(effectiveQuantity),
        purchase_total: purchaseTotal,
        effective_quantity: Math.round(effectiveQuantity),
        total_cost: totalCost,
        unit_cost: unitCost.toFixed(3),
        current_profit: currentProfit,
        current_rate: currentRate.toFixed(1),
        predicted_profit: predictedProfit,
        predicted_rate: predictedRate.toFixed(1),
        profit_diff: profitDiff,
        suggested_delay_days: suggestedDelayDays
      }

    } else {
      // ========================================
      // 农户视角：利润模拟（保持原有逻辑）
      // ========================================

      // 预测最高价（农户希望在高价时卖出）
      predictedMaxPrice = predictedPrices.length > 0
        ? Math.max(...predictedPrices) / 2
        : currentPrice

      // 找到预测最高价对应的天数
      if (predictedPrices.length > 0) {
        const maxIdx = predictedPrices.indexOf(Math.max(...predictedPrices))
        suggestedDelayDays = maxIdx + 1
      }

      // 计算总产量
      totalYield = form.area * form.yield_per_acre

      // 计算总成本
      totalCost = form.seed_cost + form.fertilizer_cost + form.pesticide_cost +
                   form.labor_cost + form.other_cost

      // 单位成本
      unitCost = totalYield > 0 ? totalCost / totalYield : 0

      // 当前出售利润
      const currentRevenue = currentPrice * totalYield
      currentProfit = currentRevenue - totalCost
      currentRate = totalCost > 0 ? (currentProfit / totalCost * 100) : 0

      // 择期出售利润（预测最高价）
      const predictedRevenue = predictedMaxPrice * totalYield
      predictedProfit = predictedRevenue - totalCost
      predictedRate = totalCost > 0 ? (predictedProfit / totalCost * 100) : 0

      // 生成建议
      profitDiff = predictedProfit - currentProfit

      if (profitDiff > 0) {
        const percentIncrease = ((predictedMaxPrice - currentPrice) / currentPrice * 100).toFixed(1)
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格呈上升趋势。` +
                     `预测最高价将达到 ${predictedMaxPrice.toFixed(2)} 元/斤（当前均价 ${currentPrice.toFixed(2)} 元/斤，涨幅约 ${percentIncrease}%）。` +
                     `建议延后 ${suggestedDelayDays} 天出售，预计可额外增加收益 ${formatNumber(profitDiff)} 元。`
      } else if (profitDiff < 0) {
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格可能略有下降。` +
                     `当前价格处于相对高点 ${currentPrice.toFixed(2)} 元/斤，建议及时出售锁定利润。`
      } else {
        adviceText = `基于 LSTM 模型预测，未来 ${predictionDays.value} 天内价格走势平稳。` +
                     `可结合实际情况灵活安排出售时间。`
      }

      profitResult.value = {
        current_price: currentPrice.toFixed(2),
        predicted_max_price: predictedMaxPrice.toFixed(2),
        total_yield: Math.round(totalYield),
        total_cost: totalCost,
        unit_cost: unitCost.toFixed(3),
        current_profit: currentProfit,
        current_rate: currentRate.toFixed(1),
        predicted_profit: predictedProfit,
        predicted_rate: predictedRate.toFixed(1),
        profit_diff: profitDiff,
        suggested_delay_days: suggestedDelayDays
      }
    }

    advice.value = adviceText

    ElMessage.success(isBuyer.value ? '采购分析完成' : '利润计算完成')

  } catch (error) {
    console.error('计算利润失败:', error)
    ElMessage.error('计算失败，请重试')
  } finally {
    loading.value = false
  }
}

// 初始化预测图表
const initPredictionChart = () => {
  if (!predictionChartRef.value) return
  if (predictionChart) predictionChart.dispose()

  predictionChart = echarts.init(predictionChartRef.value)

  const res = predictionResult.value
  const hist = res.historical || { dates: [], prices: [] }
  const pred = res.prediction || { dates: [], prices: [] }

  const histLength = hist.prices?.length || 0

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = params[0].name + '<br/>'
        params.forEach(p => {
          if (p.value !== null) {
            result += `${p.marker}${p.seriesName}: ${p.value.toFixed(2)} 元/公斤<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['历史价格', 'LSTM预测'],
      bottom: 0
    },
    grid: { left: '3%', right: '4%', bottom: '20%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [
        ...(hist.dates?.map(d => d.slice(5)) || []),
        ...(pred.dates?.map(d => d.slice(5)) || [])
      ],
      axisLabel: { rotate: 45, fontSize: 10 }
    },
    yAxis: { type: 'value', name: '价格(元/公斤)' },
    series: [
      {
        name: '历史价格',
        type: 'line',
        data: hist.prices || [],
        smooth: true,
        lineStyle: { color: '#409EFF', width: 2 },
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        }
      },
      {
        name: 'LSTM预测',
        type: 'line',
        data: [...Array(Math.max(0, histLength - 1)).fill(null), ...(pred.prices || [])],
        smooth: true,
        lineStyle: { color: '#F56C6C', width: 2, type: 'dashed' },
        itemStyle: { color: '#F56C6C' },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  predictionChart.setOption(option)
}

const onProductChange = () => {
  predictionResult.value = null
  profitResult.value = null
  advice.value = ''
}

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const handleResize = () => {
  if (predictionChart) predictionChart.resize()
}

onMounted(async () => {
  // 确保用户信息已加载
  if (!userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
  initFormDefaults()
  await loadProducts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (predictionChart) predictionChart.dispose()
})
</script>

<style scoped>
.profit-simulation {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
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

.form-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
}

.category-tag {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

/* 利润卡片 */
.profit-card {
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 15px;
  border: 2px solid;
}

.profit-card.current {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #409EFF;
}

.profit-card.future {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border-color: #F56C6C;
}

.profit-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.profit-price,
.profit-amount,
.profit-rate {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.profit-price .label,
.profit-amount .label,
.profit-rate .label {
  color: #606266;
  font-size: 14px;
}

.profit-price .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.profit-price .value.highlight {
  color: #F56C6C;
}

.profit-amount .value,
.profit-rate .value {
  font-size: 20px;
  font-weight: 700;
  color: #67C23A;
}

.profit-amount .value.negative,
.profit-rate .value.negative {
  color: #F56C6C;
}

/* 成本明细 */
.cost-card {
  margin-bottom: 20px;
}

.cost-summary {
  font-size: 14px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: #606266;
}

.cost-row.total {
  font-weight: 600;
  color: #303133;
  font-size: 15px;
}

.cost-divider {
  height: 1px;
  background: #ebeef5;
  margin: 8px 0;
}

/* 建议卡片 */
.advice-card {
  margin-bottom: 20px;
}

.advice-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.advice-text {
  margin: 0;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}

.advice-highlight {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 6px;
}

.highlight-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
}

.highlight-row strong {
  color: #303133;
}

.profit-highlight {
  color: #67C23A !important;
  font-size: 16px;
}

@media (max-width: 768px) {
  .profit-simulation {
    padding: 10px;
  }

  .profit-card {
    padding: 15px;
  }

  .profit-price .value {
    font-size: 16px;
  }

  .profit-amount .value,
  .profit-rate .value {
    font-size: 18px;
  }
}
</style>
