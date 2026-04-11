<template>
  <div class="profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-button type="primary" @click="handleEdit">{{ isEditing ? '取消编辑' : '编辑资料' }}</el-button>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        :disabled="!isEditing"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入地址" />
        </el-form-item>
        
        <el-form-item label="角色" v-if="userInfo.role">
          <el-input :model-value="userInfo.role_display" disabled />
        </el-form-item>
        
        <el-form-item v-if="isEditing">
          <el-button type="primary" :loading="loading" @click="handleSubmit">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { authAPI } from '@/api/auth'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)
const isEditing = ref(false)
const loading = ref(false)
const formRef = ref()

const form = reactive({
  email: '',
  phone: '',
  address: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

onMounted(() => {
  if (userInfo.value) {
    Object.assign(form, {
      email: userInfo.value.email || '',
      phone: userInfo.value.phone || '',
      address: userInfo.value.address || ''
    })
  }
})

const handleEdit = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) {
    Object.assign(form, {
      email: userInfo.value.email || '',
      phone: userInfo.value.phone || '',
      address: userInfo.value.address || ''
    })
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authAPI.updateProfile(form)
        await userStore.fetchUserInfo()
        ElMessage.success('修改成功')
        isEditing.value = false
      } catch (error) {
        console.error('修改失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-container {
  max-width: 600px;
}
</style>
