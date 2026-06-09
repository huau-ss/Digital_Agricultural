<template>
  <div class="data-dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon"><i class="el-icon-document"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.total_records || 0 }}</div>
            <div class="stat-label">数据总量</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon"><i class="el-icon-goods"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.total_products || 0 }}</div>
            <div class="stat-label">农产品种类</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon"><i class="el-icon-location-information"></i></div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.province_count || 0 }}</div>
            <div class="stat-label">覆盖省份</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：地图 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="card-header">
            <h3>全国农产品价格热力图</h3>
            <el-select v-model="selectedProductId" placeholder="选择农产品" size="small" @change="onProductChange" style="width: 150px;">
              <el-option
                v-for="product in products"
                :key="product.id"
                :label="product.name"
                :value="product.id"
              />
            </el-select>
          </div>
          <div class="card-body">
            <div ref="mapChartRef" style="width: 100%; height: 380px;"></div>
          </div>
          <div class="card-footer">
            <span>平均价格: {{ priceStats.avg_price || '-' }} 元/公斤</span>
            <span>最高: {{ priceStats.max_price || '-' }} | 最低: {{ priceStats.min_price || '-' }}</span>
          </div>
        </div>
      </el-col>

      <!-- 右侧：价格预测 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="card-header">
            <h3>价格预测 (LSTM)</h3>
            <div class="header-actions">
              <el-select v-model="selectedProductId" placeholder="选择农产品" size="small" @change="onProductChange" style="width: 130px;">
                <el-option
                  v-for="product in products"
                  :key="product.id"
                  :label="product.name"
                  :value="product.id"
                />
              </el-select>
              <el-select v-model="selectedProvince" placeholder="选择省份" size="small" clearable @change="onProvinceChange" style="width: 110px; margin-left: 10px;">
                <el-option
                  v-for="province in availableProvinces"
                  :key="province"
                  :label="province"
                  :value="province"
                />
              </el-select>
              <el-select v-model="predictionDays" placeholder="预测天数" size="small" @change="loadPricePrediction" style="width: 100px; margin-left: 10px;">
                <el-option label="7天" :value="7" />
                <el-option label="14天" :value="14" />
                <el-option label="30天" :value="30" />
              </el-select>
            </div>
          </div>
          <div class="card-body">
            <div ref="predictionChartRef" style="width: 100%; height: 320px;"></div>
          </div>
          <div class="card-footer">
            <span>预测天数: {{ predictionDays }}天</span>
            <span>{{ predictionStatus }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部：价格走势 + 产品对比 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：价格走势 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="card-header">
            <h3>价格走势</h3>
            <div class="header-actions">
              <el-select v-model="selectedDays" placeholder="时间范围" size="small" @change="onDaysChange" style="width: 100px;">
                <el-option label="7天" :value="7" />
                <el-option label="15天" :value="15" />
                <el-option label="30天" :value="30" />
              </el-select>
            </div>
          </div>
          <div class="card-body">
            <div ref="lineChartRef" style="width: 100%; height: 280px;"></div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：地区价格对比 -->
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="card-header">
            <h3>地区价格对比</h3>
            <span class="product-label">当前产品: {{ selectedProductName }}</span>
          </div>
          <div class="card-body">
            <div ref="regionChartRef" style="width: 100%; height: 280px;"></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'
import {
  getProducts,
  getCollectionSummary,
  getPriceTrend,
  getProvinceHeatmap,
  getRegionComparison
} from '@/api/dataCollection'
import { getPricePrediction, getPredictableProducts } from '@/api/prediction'

const loading = ref(false)
const products = ref([])
const selectedProductId = ref(null)
const selectedProvince = ref(null)  // 选中的省份
const availableProvinces = ref([])  // 可用的省份列表
const selectedDays = ref(30)  // 默认查询30天数据
const predictionDays = ref(7)

const summary = reactive({
  total_records: 0,
  total_products: 0,
  province_count: 0
})

const priceStats = reactive({
  avg_price: null,
  max_price: null,
  min_price: null
})

const priceTrendData = ref([])
const regionComparisonData = ref([])

// 计算属性：获取当前选中产品的名称
const selectedProductName = computed(() => {
  if (!selectedProductId.value) return '-'
  const product = products.value.find(p => p.id === selectedProductId.value)
  return product ? product.name : '-'
})
const predictionData = ref({
  prediction: { dates: [], prices: [] }
})

let mapChart = null
let lineChart = null
let regionChart = null
let predictionChart = null

const mapChartRef = ref(null)
const lineChartRef = ref(null)
const regionChartRef = ref(null)
const predictionChartRef = ref(null)

const predictionStatus = ref('请选择产品')

const updatePredictionStatus = (res) => {
  if (!res || !res.success) {
    predictionStatus.value = res?.error || '加载失败'
  } else {
    const prices = res.prediction?.prices || []
    if (prices.length === 0) {
      predictionStatus.value = '暂无预测数据'
    } else {
      const lastPred = prices[prices.length - 1]
      predictionStatus.value = `最新预测: ${lastPred} 元/公斤`
    }
  }
}

// 初始化地图
const mapRegistered = ref(false)
const initMapChart = () => {
  if (!mapChartRef.value) return
  mapChart = echarts.init(mapChartRef.value)
  import('@/assets/china.json').then((module) => {
    // 处理动态导入的结果，可能是 default 或直接是数据
    const chinaData = module.default || module
    if (!echarts.getMap('china')) {
      echarts.registerMap('china', chinaData)
      mapRegistered.value = true
    } else {
      mapRegistered.value = true
    }
    updateMapChart()
  }).catch(err => {
    console.error('加载中国地图失败:', err)
    mapRegistered.value = false
    // 即使地图加载失败，也尝试更新图表
    updateMapChart()
  })
}

const updateMapChart = () => {
  if (!mapChart) return

  const mapData = priceStats._mapData || []

  // 如果地图未注册，显示空白提示
  if (!mapRegistered.value) {
    mapChart.setOption({
      title: { text: '地图加载中...', left: 'center', top: 'center', textStyle: { color: '#999' } }
    })
    return
  }

  if (mapData.length === 0) {
    mapChart.setOption({
      title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 16 } }
    })
    return
  }

  const maxValue = Math.max(...mapData.map(d => d.value || 0), 1)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.data) {
          return `${params.name}<br/>平均价格: ${params.data.value} 元/公斤`
        }
        return params.name
      }
    },
    visualMap: {
      min: 0,
      max: maxValue * 1.2,
      left: 'left',
      top: 'bottom',
      text: ['高', '低'],
      calculable: true,
      inRange: { color: ['#50a3ba', '#eac736', '#d94e5d'] }
    },
    series: [{
      name: '平均价格',
      type: 'map',
      map: 'china',
      roam: true,
      emphasis: {
        label: { show: true, color: '#fff' },
        itemStyle: { areaColor: '#66b3ff' }
      },
      data: mapData
    }]
  }
  mapChart.setOption(option, true)
}

// 初始化折线图
const initLineChart = () => {
  if (!lineChartRef.value) return
  lineChart = echarts.init(lineChartRef.value)
  updateLineChart()
}

const updateLineChart = () => {
  if (!lineChart) return

  const trendData = priceTrendData.value

  const option = {
    tooltip: { trigger: 'axis', formatter: '{b}<br/>{a}: {c} 元/公斤' },
    xAxis: {
      type: 'category',
      data: trendData.map(d => d.date?.slice(5) || ''),
      axisLabel: { rotate: 45, fontSize: 10 }
    },
    yAxis: { type: 'value', name: '价格(元/公斤)' },
    series: [{
      name: '历史价格',
      type: 'line',
      data: trendData.map(d => d.price),
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#409EFF', width: 2 },
      itemStyle: { color: '#409EFF' }
    }],
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true }
  }
  lineChart.setOption(option)
}

// 初始化地区对比图
const initRegionChart = () => {
  if (!regionChartRef.value) return
  regionChart = echarts.init(regionChartRef.value)
  updateRegionChart()
}

const updateRegionChart = () => {
  if (!regionChart) return

  const data = regionComparisonData.value

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const item = data[params[0].dataIndex]
        return `${params[0].name}<br/>
          平均价格: ${params[0].value} 元/公斤<br/>
          数据量: ${item?.record_count || 0} 条`
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.market_name || ''),
      axisLabel: { rotate: 30, fontSize: 10 }
    },
    yAxis: { type: 'value', name: '价格(元/公斤)' },
    series: [{
      name: '平均价格',
      type: 'bar',
      data: data.map(d => d.avg_price || 0),
      itemStyle: {
        color: (params) => {
          const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#00BCD4', '#9C27B0', '#FF9800']
          return colors[params.dataIndex % colors.length]
        },
        borderRadius: [5, 5, 0, 0]
      },
      barWidth: '50%'
    }],
    grid: { left: '3%', right: '4%', bottom: '25%', top: '10%', containLabel: true }
  }
  regionChart.setOption(option)
}

// 初始化预测图
const initPredictionChart = () => {
  if (!predictionChartRef.value) return
  predictionChart = echarts.init(predictionChartRef.value)
  updatePredictionChart()
}

const updatePredictionChart = () => {
  if (!predictionChart) return

  const pred = predictionData.value.prediction

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}<br/>${params[0].seriesName}: ${params[0].value} 元/公斤`
      }
    },
    xAxis: {
      type: 'category',
      data: pred.dates?.map(d => d.slice(5)) || [],
      axisLabel: { rotate: 45, fontSize: 10 }
    },
    yAxis: { type: 'value', name: '价格(元/公斤)' },
    series: [{
      name: 'LSTM预测',
      type: 'line',
      data: pred.prices || [],
      smooth: true,
      lineStyle: { color: '#F56C6C', width: 2 },
      itemStyle: { color: '#F56C6C' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
            { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
          ]
        }
      },
      symbol: 'circle',
      symbolSize: 6
    }],
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true }
  }
  predictionChart.setOption(option)
}

// 加载数据
const loadProducts = async () => {
  try {
    // 优先加载可预测的产品列表（有足够历史数据和模型）
    const predRes = await getPredictableProducts()
    if (predRes && predRes.success && predRes.products && predRes.products.length > 0) {
      products.value = predRes.products
      selectedProductId.value = products.value[0].id
      return true
    }
    // 回退：加载所有产品，但只选择有数据的产品
    const res = await getProducts()
    if (res && Array.isArray(res) && res.length > 0) {
      products.value = res
      const withData = res.filter(p => p.recent_count > 0)
      selectedProductId.value = withData.length > 0 ? withData[0].id : null
      return withData.length > 0
    }
    return false
  } catch (error) {
    console.error('加载产品列表失败:', error)
    return false
  }
}

const loadDashboardSummary = async () => {
  try {
    const res = await getCollectionSummary()
    if (res && res.summary) {
      Object.assign(summary, res.summary)
    }
  } catch (error) {
    console.error('加载摘要失败:', error)
  }
}

const loadPriceTrend = async () => {
  if (!selectedProductId.value) return
  try {
    const params = {
      product_id: selectedProductId.value,
      days: selectedDays.value
      // 不传 end_date，让 API 自动获取到最新数据
    }
    const res = await getPriceTrend(params)
    console.log('价格走势API响应:', res)
    // 处理响应数据 - API返回 dates 和 prices
    if (res && Array.isArray(res.dates) && res.dates.length > 0) {
      priceTrendData.value = res.dates.map((d, i) => ({
        date: d,
        price: res.prices?.[i] || 0
      }))
    } else if (res && Array.isArray(res.data) && res.data.length > 0) {
      priceTrendData.value = res.data
    } else {
      priceTrendData.value = []
    }
    // 无论数据是否为空都更新图表
    updateLineChart()
  } catch (error) {
    console.error('加载价格走势失败:', error)
  }
}

const loadProvinceHeatmap = async () => {
  try {
    const res = await getProvinceHeatmap({
      product_id: selectedProductId.value || undefined,
      days: 180  // 查询半年数据，确保能查到历史数据
    })
    console.log('热力图API响应:', res)
    if (res) {
      // 处理 map_data
      if (res.map_data) {
        priceStats._mapData = res.map_data
      } else if (res.province_data) {
        // 有时候返回的是 province_data 而不是 map_data
        priceStats._mapData = res.province_data
      }
      // 处理统计数据
      if (res.statistics) {
        priceStats.avg_price = res.statistics.avg_price
        priceStats.max_price = res.statistics.max_price
        priceStats.min_price = res.statistics.min_price
      } else if (res.avg_price !== undefined) {
        priceStats.avg_price = res.avg_price
        priceStats.max_price = res.max_price
        priceStats.min_price = res.min_price
      }
    }
    // 无论数据是否为空都更新图表
    updateMapChart()
  } catch (error) {
    console.error('加载热力图失败:', error)
  }
}

const loadRegionComparison = async () => {
  // 直接使用热力图选中的产品ID，保持同步
  const productId = selectedProductId.value
  if (!productId) {
    console.warn('没有可用的产品ID进行地区对比')
    regionComparisonData.value = []
    updateRegionChart()
    return
  }
  try {
    const res = await getRegionComparison({
      product_id: productId,
      days: 180  // 查询半年数据，确保能查到历史数据
    })
    console.log('地区对比API响应:', res)
    // 处理响应数据
    if (res && Array.isArray(res)) {
      regionComparisonData.value = res
    } else if (res && res.data) {
      regionComparisonData.value = res.data
    } else if (res && typeof res === 'object') {
      // 取第一个数组值
      const arrKey = Object.keys(res).find(k => Array.isArray(res[k]))
      if (arrKey) {
        regionComparisonData.value = res[arrKey]
      }
    } else {
      regionComparisonData.value = []
    }
    // 无论数据是否为空都更新图表
    updateRegionChart()
  } catch (error) {
    console.error('加载地区对比失败:', error)
  }
}

const loadPricePrediction = async () => {
  if (!selectedProductId.value) return
  try {
    const params = {
      product_id: selectedProductId.value,
      days: predictionDays.value
    }
    // 如果选择了省份，传递省份参数
    if (selectedProvince.value) {
      params.province = selectedProvince.value
    }
    const res = await getPricePrediction(params)
    updatePredictionStatus(res)
    if (res && res.success) {
      predictionData.value.prediction = res.prediction || { dates: [], prices: [] }
      // 更新可用省份列表
      if (res.available_provinces && res.available_provinces.length > 0) {
        availableProvinces.value = res.available_provinces
      }
    } else {
      predictionData.value.prediction = { dates: [], prices: [] }
    }
    updatePredictionChart()
  } catch (error) {
    predictionStatus.value = '加载失败'
    console.error('加载预测数据失败:', error)
  }
}

const onProductChange = () => {
  // 切换产品时清空省份选择，重新获取可用省份
  selectedProvince.value = null
  loadPriceTrend()
  loadProvinceHeatmap()
  loadRegionComparison()
  loadPricePrediction()
}

const onProvinceChange = () => {
  // 省份改变时重新加载预测
  loadPricePrediction()
}

const onDaysChange = () => {
  loadPriceTrend()
}

const handleResize = () => {
  if (mapChart) mapChart.resize()
  if (lineChart) lineChart.resize()
  if (regionChart) regionChart.resize()
  if (predictionChart) predictionChart.resize()
}

onMounted(async () => {
  loading.value = true
  try {
    // 1. 先初始化图表（图表必须先 init，否则无法 setOption）
    await nextTick()
    initMapChart()
    initLineChart()
    initRegionChart()
    initPredictionChart()

    // 2. 再加载数据（数据到达后直接 updateChart，图表已就绪）
    const hasProducts = await loadProducts()

    if (hasProducts && selectedProductId.value) {
      // 并行加载所有数据
      await Promise.allSettled([
        loadDashboardSummary(),
        loadPriceTrend(),
        loadProvinceHeatmap(),
        loadRegionComparison(),
        loadPricePrediction(),
      ])
    }
  } catch (error) {
    console.error('初始化失败:', error)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (mapChart) mapChart.dispose()
  if (lineChart) lineChart.dispose()
  if (regionChart) regionChart.dispose()
  if (predictionChart) predictionChart.dispose()
})
</script>

<style scoped>
.data-dashboard {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
  position: relative;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  background: linear-gradient(135deg, #409EFF, #66b3ff);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  overflow: hidden;
}

.card-header {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
}

.product-label {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 4px;
}

.card-body {
  padding: 15px;
}

.card-footer {
  padding: 10px 20px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #606266;
  display: flex;
  justify-content: space-between;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
  font-size: 18px;
  color: #409EFF;
}

.loading-overlay .el-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .data-dashboard {
    padding: 10px;
  }

  .stat-card {
    padding: 15px;
  }

  .stat-icon {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }

  .stat-value {
    font-size: 22px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
