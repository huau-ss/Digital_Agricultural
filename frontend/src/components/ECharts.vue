<template>
  <div ref="chartRef" :style="{ width: width, height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // ECharts 配置选项
  option: {
    type: Object,
    required: true
  },
  // 宽度
  width: {
    type: String,
    default: '100%'
  },
  // 高度
  height: {
    type: String,
    default: '400px'
  },
  // 是否自动Resize
  autoresize: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['chart-click', 'chart-ready'])

const chartRef = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  // 绑定点击事件
  chartInstance.on('click', (params) => {
    emit('chart-click', params)
  })

  // 设置配置
  if (props.option) {
    chartInstance.setOption(props.option)
  }

  emit('chart-ready', chartInstance)
}

// 更新图表配置
const setOption = (option) => {
  if (chartInstance) {
    chartInstance.setOption(option, true)
  }
}

// 获取图表实例
const getInstance = () => {
  return chartInstance
}

// 销毁图表
const dispose = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// Resize 图表
const resize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听 option 变化
watch(
  () => props.option,
  (newOption) => {
    if (newOption && chartInstance) {
      chartInstance.setOption(newOption, true)
    }
  },
  { deep: true }
)

// 暴露方法给父组件
defineExpose({
  setOption,
  getInstance,
  dispose,
  resize
})

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
  })

  // 添加窗口Resize监听
  if (props.autoresize) {
    window.addEventListener('resize', resize)
  }
})

onUnmounted(() => {
  if (props.autoresize) {
    window.removeEventListener('resize', resize)
  }
  dispose()
})
</script>

<style scoped>
div {
  position: relative;
}
</style>
