<template>
  <div class="resource-page">
    <HeaderNav />
    <div class="resource-content">
      <el-card shadow="never" class="resource-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-document"></i>
            <span>资源查阅</span>
          </div>
        </template>
        <div class="resource-desc">
          <p>🚧 资源查阅模块开发中...</p>
          <p>后续可添加：</p>
          <el-list>
            <el-list-item>1. 世界技能大赛官方文档</el-list-item>
            <el-list-item>2. 技术动作标准教程</el-list-item>
            <el-list-item>3. 往届大赛视频/案例</el-list-item>
            <el-list-item>4. 资源上传/下载功能</el-list-item>
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
.resource-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.resource-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.resource-card {
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
.resource-desc {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}
</style>