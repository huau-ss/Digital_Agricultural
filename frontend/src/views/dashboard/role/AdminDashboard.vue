<template>
  <div class="role-dashboard">
    <h2>系统管理员工作台</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#409EFF"><User /></el-icon>
            <h3>用户管理</h3>
            <p>管理系统用户和权限</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#67C23A"><Setting /></el-icon>
            <h3>系统设置</h3>
            <p>配置系统参数</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#F56C6C"><DataLine /></el-icon>
            <h3>数据统计</h3>
            <p>查看平台运营数据</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { User, Setting, DataLine } from '@element-plus/icons-vue'
</script>

<style scoped>
.role-dashboard h2 {
  margin-bottom: 20px;
  color: #303133;
}

.dashboard-item {
  text-align: center;
  padding: 20px;
}

.dashboard-item h3 {
  margin: 16px 0 8px;
  color: #303133;
}

.dashboard-item p {
  color: #909399;
  font-size: 14px;
}
</style>
