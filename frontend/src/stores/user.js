import { defineStore } from 'pinia'
import { authAPI } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
     // 刷新页面时从 localStorage 恢复 token 和 refreshToken
    token: localStorage.getItem('access_token') || '',
    refreshToken: localStorage.getItem('refresh_token') || '',
    userInfo: null
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    userId: (state) => state.userInfo?.id,
    // 获取用户角色
    userRole: (state) => state.userInfo?.role || '',
    roleName: (state) => {
      const roleMap = {
        farmer: '农户',
        buyer: '采购商',
        admin: '系统管理员'
      }
      return roleMap[state.userInfo?.role] || ''
    }
  },
  
  actions: {
    setToken(token, refreshToken) {
      this.token = token
      this.refreshToken = refreshToken
      // 保存到 localStorage，刷新页面不丢失
      localStorage.setItem('access_token', token)
      localStorage.setItem('refresh_token', refreshToken)
    },
    
    clearToken() {
      this.token = ''
      this.refreshToken = ''
      this.userInfo = null
      // 清除 localStorage，刷新页面丢失
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
    
    async login(credentials) {
      // 调用 auth.js 的 API 方法
      const res = await authAPI.login(credentials)
      this.setToken(res.data.tokens.access, res.data.tokens.refresh)     // 保存token 和 refreshToken
      this.userInfo = res.data.user                                  // 保存用户信息
      return res
    },
    
    async register(data) {
      const res = await authAPI.register(data)
      this.setToken(res.data.tokens.access, res.data.tokens.refresh)
      this.userInfo = res.data.user
      return res
    },
    
    async logout() {
      try {
        await authAPI.logout({ refresh: this.refreshToken })
      } catch (error) {
        console.warn('后端登出请求失败，将清除本地状态')
      } finally {
        this.clearToken()
      }
    },
    
    async fetchUserInfo() {
      try {
        const res = await authAPI.getProfile()
        this.userInfo = res.data
        return res
      } catch (error) {
        this.clearToken()
        throw error
      }
    },
    
    async updateProfile(data) {
      const res = await authAPI.updateProfile(data)
      this.userInfo = res.data
      return res
    }
  }
})
