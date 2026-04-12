<template>
  <div class="main-layout">
    <aside class="sidebar">
      <div class="logo-container">
        <h3>数字农业平台</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        :router="true"
      >
        <el-menu-item index="/dashboard/home">
          <span>首页</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/profile">
          <span>个人中心</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/orders" v-if="userRole === 'buyer' || userRole === 'farmer'">
          <span>订单管理</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/users" v-if="userRole === 'admin'">
          <span>用户管理</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/data-screen">
          <span>数据大屏</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/profit-simulation">
          <span>利润模拟</span>
        </el-menu-item>

        <el-menu-item index="/dashboard/trade-hall">
          <span>供需大厅</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <main class="main-content">
      <header class="header">
        <div class="breadcrumb">
          <span class="role-tag">{{ roleName }}</span>
          <span class="username">{{ userInfo?.username }}</span>
        </div>
        <div class="header-actions">
          <MessageBell />
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-icon><User /></el-icon>
              {{ userInfo?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { User, ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import MessageBell from '@/components/MessageBell.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userInfo = computed(() => userStore.userInfo)
const userRole = computed(() => userStore.userRole)
const roleName = computed(() => userStore.roleName)
const activeMenu = computed(() => route.path)

onMounted(async () => {
  if (!userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
})

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/dashboard/profile')
      break
    case 'changePassword':
      router.push('/dashboard/change-password')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await userStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch {
        // 取消操作
      }
      break
  }
}
</script>

<style scoped>
.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b3a4a;
}

.logo-container h3 {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.sidebar-menu {
  border-right: none;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-tag {
  background: #409EFF;
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.username {
  color: #606266;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
</style>
