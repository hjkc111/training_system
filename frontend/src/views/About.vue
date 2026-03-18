<template>
  <div class="about-page">
    <HeaderNav />
    <div class="about-content">
      <el-card shadow="never" class="about-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-info"></i>
            <span>关于我们</span>
          </div>
        </template>
        <div class="about-desc">
          <h3>世界技能大赛训练视频分析系统</h3>
          <p>版本：v1.0.0</p>
          <p>简介：基于FastAPI + Vue3 + Qwen3.5-Plus开发的AI辅助训练分析平台</p>
          <p>功能：视频上传、AI动作分析、历史记录、训练管理等</p>
          <p>开发团队：XXX开发组</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import HeaderNav from '@/components/HeaderNav.vue'
</script>

<style scoped>
.about-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.about-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.about-card {
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
.about-desc {
  margin-top: 20px;
  font-size: 15px;
  line-height: 2;
  color: #475569;
}
.about-desc h3 {
  color: #1e293b;
  margin-bottom: 10px;
}
</style>