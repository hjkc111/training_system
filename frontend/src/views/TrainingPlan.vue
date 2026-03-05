<template>
  <div class="plan-page">
    <HeaderNav />
    <div class="plan-content">
      <el-card shadow="never" class="plan-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-s-data"></i>
            <span>训练计划</span>
          </div>
        </template>
        <div class="plan-desc">
          <p>🚧 训练计划模块开发中...</p>
          <p>后续可添加：</p>
          <el-list>
            <el-list-item>1. 新增训练计划（标题、内容、截止时间）</el-list-item>
            <el-list-item>2. 查看我的训练计划列表</el-list-item>
            <el-list-item>3. 标记计划完成状态</el-list-item>
            <el-list-item>4. 教练给选手分配训练计划</el-list-item>
          </el-list>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import HeaderNav from '@/components/HeaderNav.vue'
</script>

<style scoped>
.plan-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.plan-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.plan-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
}
.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-header i {
  color: #3b82f6;
}
.plan-desc {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}
</style>