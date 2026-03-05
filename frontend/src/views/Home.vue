<template>
  <div class="home-page">
    <!-- 引入顶部导航 -->
    <HeaderNav />
    <div class="home-content">
      <el-card shadow="never" class="home-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-house"></i>
            <span>世界技能大赛 - 训练管理系统</span>
          </div>
        </template>
        <div class="home-desc">
          <p>欢迎使用训练视频分析管理平台，可通过顶部导航切换功能模块：</p>
          <el-list>
            <el-list-item>📊 数据分析：上传训练视频，调用AI分析技术动作规范性</el-list-item>
            <el-list-item>📋 训练计划：制定/查看个人训练计划</el-list-item>
            <el-list-item>📚 资源查阅：查看大赛相关资料、技术文档</el-list-item>
            <el-list-item>👤 个人中心：管理个人信息、查看历史记录</el-list-item>
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
.home-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.home-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.home-card {
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
.home-desc {
  margin-top: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}
</style>