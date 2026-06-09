<template>
  <div class="role-dashboard">
    <h2>农户工作台</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#409EFF"><DataLine /></el-icon>
            <h3>价格分析</h3>
            <p>查看农产品价格走势数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <div class="dashboard-item">
            <el-icon :size="40" color="#E6A23C"><Sell /></el-icon>
            <h3>供需大厅</h3>
            <p>发布和管理产销信息</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { DataLine, Sell } from '@element-plus/icons-vue'
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
