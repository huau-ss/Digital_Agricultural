import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard/home'
  },
  {
    path: '/dashboard',
    component: () => import('@/views/dashboard/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'home',
        name: 'DashboardHome',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/dashboard/Profile.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'farmer',
        name: 'FarmerDashboard',
        component: () => import('@/views/dashboard/role/FarmerDashboard.vue'),
        meta: { title: '农户工作台', roles: ['farmer'] }
      },
      {
        path: 'buyer',
        name: 'BuyerDashboard',
        component: () => import('@/views/dashboard/role/BuyerDashboard.vue'),
        meta: { title: '采购商工作台', roles: ['buyer'] }
      },
      {
        path: 'admin',
        name: 'AdminDashboard',
        component: () => import('@/views/dashboard/role/AdminDashboard.vue'),
        meta: { title: '管理员工作台', roles: ['admin'] }
      },
      {
        path: 'data-screen',
        name: 'DataScreen',
        component: () => import('@/views/dashboard/DataDashboard.vue'),
        meta: { title: '数据大屏', requiresAuth: false }
      },
      {
        path: 'profit-simulation',
        name: 'ProfitSimulation',
        component: () => import('@/views/analysis/ProfitSimulation.vue'),
        meta: { title: '利润模拟' }
      },
      {
        path: 'trade-hall',
        name: 'TradeHall',
        component: () => import('@/views/trade/TradeHall.vue'),
        meta: { title: '供需大厅' }
      },
      {
        path: 'crops',
        name: 'Crops',
        component: () => import('@/views/dashboard/role/FarmerDashboard.vue'),
        meta: { title: '作物管理', roles: ['farmer'] }
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/trade/Orders.vue'),
        meta: { title: '订单管理', roles: ['buyer', 'farmer'] }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/dashboard/role/AdminDashboard.vue'),
        meta: { title: '用户管理', roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const targetRoles = to.meta.roles
  
  if (requiresAuth && !userStore.isLoggedIn) {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }
  
  if (userStore.isLoggedIn && to.path === '/login') {
    next('/dashboard/home')
    return
  }
  
  // 如果有 token 但没有 userInfo，尝试获取用户信息
  if (userStore.isLoggedIn && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      console.warn('获取用户信息失败', error)
    }
  }
  
  if (targetRoles && userStore.isLoggedIn) {
    if (!targetRoles.includes(userStore.userRole)) {
      const dashboardPath = `/dashboard/${userStore.userRole}`
      next(dashboardPath)
      return
    }
  }
  
  next()
})

export default router
