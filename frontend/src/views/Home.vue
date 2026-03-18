<template>
  <div class="home-page">
    <!-- 顶部导航 -->
    <HeaderNav />

    <!-- 英雄区 -->
    <section class="hero-section">
      <div class="hero-container">
        <h1 class="hero-title">
          世界技能大赛 <span>训练管理系统</span>
        </h1>
        <p class="hero-desc">
          基于AI技术的训练视频分析管理平台，助力选手高效训练、教练精准指导，提升大赛备赛效率
        </p>
      </div>
    </section>

    <!-- 核心功能区 -->
    <section class="feature-section">
      <div class="feature-container">
        <h2 class="section-title">核心功能模块</h2>
        <p class="section-subtitle">一站式覆盖训练全流程管理需求</p>

        <div class="feature-card-list">
          <!-- 数据分析模块 - 跳转至数据分析页 -->
          <router-link to="/data-analysis" tag="div" class="feature-card">
            <div class="card-icon">
              <i class="el-icon-data-analysis"></i>
            </div>
            <h3 class="card-title">AI 数据分析</h3>
            <div class="card-desc">
              <p>✅ 上传训练视频，自动解析技术动作关键点</p>
              <p>✅ AI 智能判定动作规范性，生成量化分析报告</p>
              <p>✅ 对比标准动作库，定位偏差并给出改进建议</p>
              <p>✅ 多维度数据可视化，直观展示训练效果趋势</p>
            </div>
          </router-link>

          <!-- 训练计划模块 - 跳转至训练计划页 -->
          <router-link to="/training-plan" tag="div" class="feature-card">
            <div class="card-icon">
              <i class="el-icon-schedule"></i>
            </div>
            <h3 class="card-title">训练计划管理</h3>
            <div class="card-desc">
              <p>✅ 教练端：制定个性化训练计划，分配训练任务</p>
              <p>✅ 选手端：查看每日训练目标，提交训练完成情况</p>
              <p>✅ 计划进度实时追踪，自动提醒未完成任务</p>
              <p>✅ 历史计划归档，支持训练方案复用与优化</p>
            </div>
          </router-link>

          <!-- 资源查阅模块 - 跳转至资源查阅页 -->
          <router-link to="/resource-view" tag="div" class="feature-card">
            <div class="card-icon">
              <i class="el-icon-document-library"></i>
            </div>
            <h3 class="card-title">大赛资源查阅</h3>
            <div class="card-desc">
              <p>✅ 历届大赛真题、技术文档、评分标准查阅</p>
              <p>✅ 优秀选手训练视频、技术动作示范库</p>
              <p>✅ 分类检索资源，支持收藏与下载</p>
              <p>✅ 资源更新提醒，同步最新大赛政策与要求</p>
            </div>
          </router-link>

          <!-- 个人中心模块 - 跳转至个人中心页 -->
          <router-link to="/profile" tag="div" class="feature-card">
            <div class="card-icon">
              <i class="el-icon-user"></i>
            </div>
            <h3 class="card-title">个人中心</h3>
            <div class="card-desc">
              <p>✅ 个人信息管理，角色权限配置（选手/教练/管理员）</p>
              <p>✅ 训练历史记录、分析报告一键导出</p>
              <p>✅ 消息通知中心，接收计划、评价、资源更新提醒</p>
              <p>✅ 个人训练数据看板，展示成长曲线</p>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- 项目价值区 -->
    <section class="value-section">
      <div class="value-container">
        <h2 class="section-title">项目核心价值</h2>
        <div class="value-card-list">
          <div class="value-card">
            <i class="el-icon-time"></i>
            <h3>提升训练效率</h3>
            <p>AI 自动分析替代人工逐帧查看，节省80%分析时间</p>
          </div>
          <div class="value-card">
            <i class="el-icon-accuracy"></i>
            <h3>精准动作指导</h3>
            <p>量化数据对比，告别主观判断，指导更科学</p>
          </div>
          <div class="value-card">
            <i class="el-icon-files"></i>
            <h3>全流程数据留存</h3>
            <p>训练计划、分析报告、资源使用全记录，可追溯可复盘</p>
          </div>
          <div class="value-card">
            <i class="el-icon-team"></i>
            <h3>高效协同备赛</h3>
            <p>教练与选手信息同步，备赛节奏统一，提升团队效率</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部信息 -->
    <footer class="footer-section">
      <div class="footer-container">
        <p>© 2025 世界技能大赛训练管理系统</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import HeaderNav from '@/components/HeaderNav.vue'
// 确保vue-router已在项目中配置，router-link可直接使用
</script>

<style scoped>
/* 全局样式 */
.home-page {
  min-height: 100vh;
  background: #f5f7fa;
  font-family: "Inter", "Helvetica Neue", Arial, sans-serif;
}
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
a {
  text-decoration: none;
}

/* 英雄区样式 */
.hero-section {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  padding: 60px 20px;
  color: white;
  text-align: center;
}
.hero-container {
  max-width: 1200px;
  margin: 0 auto;
}
.hero-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 20px;
  line-height: 1.2;
}
.hero-title span {
  color: #bae6fd;
}
.hero-desc {
  font-size: 18px;
  max-width: 800px;
  margin: 0 auto 30px;
  line-height: 1.6;
  opacity: 0.9;
}

/* 功能区样式 */
.feature-section {
  padding: 80px 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  text-align: center;
  margin-bottom: 12px;
}
.section-subtitle {
  font-size: 16px;
  color: #64748b;
  text-align: center;
  margin-bottom: 40px;
}
.feature-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}
.feature-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  /* 增加鼠标指针样式，提示可点击 */
  cursor: pointer;
}
.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}
.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  background: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.card-icon i {
  font-size: 28px;
  color: #3b82f6;
}
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}
.card-desc {
  font-size: 14px;
  color: #475569;
  line-height: 1.8;
}
.card-desc p {
  margin-bottom: 8px;
}
.card-desc p:last-child {
  margin-bottom: 0;
}

/* 价值区样式 */
.value-section {
  padding: 60px 20px;
  background: #eff6ff;
  margin: 20px 0;
}
.value-container {
  max-width: 1200px;
  margin: 0 auto;
}
.value-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 30px;
}
.value-card {
  background: white;
  padding: 30px;
  border-radius: 10px;
  text-align: center;
  transition: all 0.3s ease;
}
.value-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}
.value-card i {
  font-size: 32px;
  color: #3b82f6;
  margin-bottom: 16px;
}
.value-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}
.value-card p {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
}

/* 底部样式 */
.footer-section {
  background: #1e293b;
  color: #cbd5e1;
  padding: 30px 20px;
  text-align: center;
}
.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  font-size: 14px;
}
.footer-section a {
  color: #3b82f6;
  text-decoration: underline;
}
.footer-section a:hover {
  color: #60a5fa;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  .hero-desc {
    font-size: 16px;
  }
  .section-title {
    font-size: 26px;
  }
  .feature-section {
    padding: 40px 20px;
  }
  .value-section {
    padding: 40px 20px;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 26px;
  }
  .feature-card {
    padding: 20px;
  }
  .card-icon {
    width: 50px;
    height: 50px;
  }
  .card-icon i {
    font-size: 24px;
  }
}

/* 修复router-link默认样式，确保卡片样式不受影响 */
:deep(.feature-card) {
  color: inherit;
  text-decoration: none;
}
</style>