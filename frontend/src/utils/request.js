import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let isRefreshing = false
let refreshSubscribers = []

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback)
}

const onTokenRefreshed = (access) => {
  refreshSubscribers.forEach(callback => callback(access))
  refreshSubscribers = []
}

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          const refreshToken = localStorage.getItem('refresh_token')
          if (refreshToken && !error.config._retry) {
            if (!isRefreshing) {
              isRefreshing = true
              error.config._retry = true
              try {
                const res = await axios.post('/api/auth/token/refresh/', {
                  refresh: refreshToken
                })
                const { access } = res.data
                localStorage.setItem('access_token', access)
                onTokenRefreshed(access)
                isRefreshing = false
                return api(error.config)
              } catch (refreshError) {
                isRefreshing = false
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                refreshSubscribers = []
                router.push('/login')
                ElMessage.error('登录已过期，请重新登录')
                return Promise.reject(refreshError)
              }
            } else {
              return new Promise((resolve) => {
                subscribeTokenRefresh((access) => {
                  error.config.headers.Authorization = `Bearer ${access}`
                  resolve(api(error.config))
                })
              })
            }
          } else {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            router.push('/login')
            ElMessage.error('请先登录')
          }
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          break  // 静默处理 404，让页面自行处理
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(data?.message || data?.detail || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default api
