<template>
  <div class="role-dashboard">
    <h2>采购商工作台</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#409EFF"><Shop /></el-icon>
            <h3>产品浏览</h3>
            <p>浏览农户发布的农产品</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#67C23A"><ShoppingCart /></el-icon>
            <h3>采购订单</h3>
            <p>管理您的采购订单</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#E6A23C"><DataAnalysis /></el-icon>
            <h3>市场分析</h3>
            <p>查看市场行情分析</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Shop, ShoppingCart, DataAnalysis } from '@element-plus/icons-vue'
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
