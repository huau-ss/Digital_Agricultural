<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">数字农业平台</h2>
      
      <el-tabs v-model="activeTab" class="form-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loginLoading"
                style="width: 100%"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱"
                size="large"
                prefix-icon="Message"
              />
            </el-form-item>
            
            <el-form-item label="角色" prop="role">
              <el-select
                v-model="registerForm.role"
                placeholder="请选择角色"
                size="large"
                style="width: 100%"
              >
                <el-option label="农户" value="farmer" />
                <el-option label="采购商" value="buyer" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="手机号" prop="phone">
              <el-input
                v-model="registerForm.phone"
                placeholder="请输入手机号（选填）"
                size="large"
                prefix-icon="Phone"
              />
            </el-form-item>
            
            <el-form-item label="地址" prop="address">
              <el-input
                v-model="registerForm.address"
                placeholder="请输入地址（选填）"
                size="large"
                prefix-icon="Location"
              />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="确认密码" prop="password_confirm">
              <el-input
                v-model="registerForm.password_confirm"
                type="password"
                placeholder="请再次输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="registerLoading"
                style="width: 100%"
                @click="handleRegister"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// =============================================
// 路由与状态管理初始化
// =============================================
// useRouter: 获取路由实例，用于登录/注册成功后页面跳转
// useUserStore: 获取用户状态管理，包含登录、注册、获取用户信息等方法
const router = useRouter()
const userStore = useUserStore()

// =============================================
// Tab 页签状态
// =============================================
// activeTab: 控制登录/注册 Tab 页的切换，默认为"登录"页
const activeTab = ref('login')

// =============================================
// 表单引用与加载状态
// =============================================
// loginFormRef / registerFormRef: 表单 DOM 引用，用于触发表单验证
// loginLoading / registerLoading: 按钮加载状态，防止重复提交
const loginFormRef = ref()
const registerFormRef = ref()
const loginLoading = ref(false)
const registerLoading = ref(false)

// =============================================
// 登录表单数据
// =============================================
// loginForm: 登录表单的双向绑定数据
// username: 用户名，必填
// password: 密码，必填
const loginForm = reactive({
  username: '',
  password: ''
})

// =============================================
// 注册表单数据
// =============================================
// registerForm: 注册表单的双向绑定数据
// username: 用户名，必填，长度3-20字符
// email: 邮箱，选填，但需符合邮箱格式
// role: 角色，必填，可选"农户"或"采购商"
// phone: 手机号，选填
// address: 地址，选填
// password: 密码，必填，至少8个字符
// password_confirm: 确认密码，必填，需与密码一致
const registerForm = reactive({
  username: '',
  email: '',
  role: 'farmer',  // 默认选择"农户"角色
  phone: '',
  address: '',
  password: '',
  password_confirm: ''
})

// =============================================
// 自定义验证器：密码确认
// =============================================
// validatePasswordConfirm: 验证两次输入的密码是否一致
// rule: 验证规则对象（Element Plus 表单验证框架要求）
// value: 当前输入值
// callback: 回调函数，验证通过时调用 callback()，失败时调用 callback(new Error('错误信息'))
const validatePasswordConfirm = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// =============================================
// 登录表单验证规则
// =============================================
// required: true 表示该字段必填
// trigger: 'blur' 表示失去焦点时触发验证
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// =============================================
// 注册表单验证规则
// =============================================
// type: 'email' 内置邮箱格式验证
// min/max: 字符串长度限制
// validator: 自定义验证器，这里用于验证确认密码
// trigger: 'change' 表示值变化时触发（适用于 select 下拉框）
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8个字符', trigger: 'blur' }
  ],
  password_confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePasswordConfirm, trigger: 'blur' }
  ]
}

// =============================================
// 登录处理函数
// =============================================
// handleLogin: 处理用户登录
// 1. 先触发表单验证，确保必填项已填写
// 2. 调用 userStore.login 发送登录请求
// 3. 登录成功后获取用户信息并跳转到目标页面
const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loginLoading.value = true
      try {
        // 调用后端登录接口，返回用户信息和 Token
        await userStore.login(loginForm)
        // 确保获取最新的用户信息
        if (!userStore.userInfo) {
          await userStore.fetchUserInfo()
        }
        ElMessage.success('登录成功')

        // 检查是否有 redirect 参数（从需要权限的页面跳转过来）
        const redirect = router.currentRoute.value.query.redirect
        if (redirect) {
          // 如果有 redirect，跳转到目标页面
          router.push(redirect)
        } else {
          // 否则跳转到首页
          router.push('/dashboard/home')
        }
      } catch (error) {
        console.error('登录失败:', error)
        // 错误消息由 userStore.login 内部处理（ElMessage.error）
      } finally {
        // 不管成功失败，都要关闭加载状态
        loginLoading.value = false
      }
    }
  })
}

// =============================================
// 注册处理函数
// =============================================
// handleRegister: 处理用户注册
// 1. 先触发表单验证，确保所有字段符合规则
// 2. 调用 userStore.register 发送注册请求
// 3. 注册成功后跳转到首页（注册后需等待管理员审核才能登录）
const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      registerLoading.value = true
      try {
        await userStore.register(registerForm)
        // 确保获取最新的用户信息
        if (!userStore.userInfo) {
          await userStore.fetchUserInfo()
        }
        ElMessage.success('注册成功')

        // 注册成功后跳转到首页
        router.push('/dashboard/home')
      } catch (error) {
        console.error('注册失败:', error)
        // 错误消息由 userStore.register 内部处理
      } finally {
        // 关闭加载状态
        registerLoading.value = false
      }
    }
  })
}

// =============================================
// 根据角色获取仪表盘路径
// =============================================
// getDashboardByRole: 根据用户角色返回对应的仪表盘路径
// roleMap: 角色到路径的映射表
// farmer -> /dashboard/farmer: 农户工作台
// buyer -> /dashboard/buyer: 采购商工作台
// admin -> /dashboard/admin: 管理员工作台
// 默认返回农户工作台路径
const getDashboardByRole = (role) => {
  const roleMap = {
    farmer: '/dashboard/farmer',
    buyer: '/dashboard/buyer',
    admin: '/dashboard/admin'
  }
  return roleMap[role] || '/dashboard/farmer'
}
</script>
