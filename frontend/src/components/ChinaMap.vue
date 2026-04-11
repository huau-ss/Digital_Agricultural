<template>
  <div ref="mapRef" :style="{ width: width, height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '500px'
  },
  autoresize: {
    type: Boolean,
    default: true
  },
  title: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['province-click'])

const mapRef = ref(null)
let chartInstance = null

const registerMap = async () => {
  if (!echarts.getMap('china')) {
    try {
      const chinaJson = await import('@/assets/china.json')
      echarts.registerMap('china', chinaJson.default)
      return true
    } catch (e) {
      console.error('加载地图失败:', e)
      return false
    }
  }
  return true
}

const getOption = () => {
  const maxValue = props.data.length > 0
    ? Math.max(...props.data.map(d => d.value || 0), 1)
    : 1

  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: { color: '#333', fontSize: 16 }
    },
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
      inRange: {
        color: ['#50a3ba', '#eac736', '#d94e5d']
      },
      textStyle: { color: '#333' }
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
      data: props.data
    }]
  }
}

const initChart = async () => {
  if (!mapRef.value) return

  const success = await registerMap()
  if (!success) return

  chartInstance = echarts.init(mapRef.value)

  chartInstance.on('click', (params) => {
    emit('province-click', params)
  })

  chartInstance.setOption(getOption())
}

const updateData = (newData) => {
  if (chartInstance) {
    chartInstance.setOption({
      series: [{ data: newData }]
    }, true)
  }
}

const resize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const dispose = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

watch(
  () => props.data,
  (newData) => {
    if (newData && chartInstance) {
      updateData(newData)
    }
  },
  { deep: true }
)

defineExpose({
  updateData,
  resize,
  dispose
})

onMounted(() => {
  nextTick(() => {
    initChart()
  })

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