<template>
  <div class="training-detail-container">
    <HeaderNav />
    <div class="main-content">
      <!-- 训练日头部信息 -->
      <div class="page-header">
        <el-page-header @back="goBack" :content="trainingDayInfo.training_day_name || '光电项目训练详情'"></el-page-header>
        <div class="header-info">
          <el-tag :type="trainingDayInfo.is_finished ? 'success' : 'warning'" size="large">
            {{ trainingDayInfo.is_finished ? '已完成' : '进行中' }}
          </el-tag>
          <el-tag type="info" size="large" v-if="trainingDayInfo.overall_score">
            整体评分：{{ trainingDayInfo.overall_score }}分
          </el-tag>
        </div>
      </div>

      <!-- 加载提示 -->
      <el-empty v-if="loading" description="加载光电项目训练日信息中..."></el-empty>

      <!-- 项目列表 -->
      <el-card v-if="!loading" class="project-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>光电训练项目列表</span>
            <span>完成进度：{{ finishedCount }} / {{ projectList.length }}</span>
          </div>
        </template>

        <!-- 项目步骤 -->
        <div class="project-list">
          <div 
            v-for="(project, idx) in projectList" 
            :key="project.project_id"
            class="project-item"
            :class="{ 'project-active': idx === currentProjectIndex, 'project-finished': project.is_analyzed }"
          >
            <!-- 项目头部 -->
            <div class="project-item-header" @click="currentProjectIndex = idx">
              <div class="project-title">
                <el-tag 
                  :type="project.is_analyzed ? 'success' : idx === currentProjectIndex ? 'primary' : 'info'"
                  size="small"
                  class="project-order"
                >
                  {{ idx+1 }}
                </el-tag>
                <span class="project-name">{{ project.project_name }}</span>
                <span class="project-status">
                  {{ project.is_analyzed ? '已完成分析' : '待上传视频分析' }}
                </span>
              </div>
              <i class="el-icon-arrow-down project-arrow" :class="{ 'rotate': idx === currentProjectIndex }"></i>
            </div>

            <!-- 项目内容：当前激活且未完成的项目，显示上传区域 -->
            <div class="project-content" v-show="idx === currentProjectIndex && !project.is_analyzed">
              <el-alert 
                title="当前正在进行【{{ project.project_name }}】项目训练" 
                type="info" 
                :closable="false"
                style="margin-bottom: 20px;"
              >
                <template #default>
                  {{ project.project_desc }}
                </template>
              </el-alert>

              <!-- 视频上传区域（和原有逻辑完全兼容） -->
              <el-upload
                ref="uploadRef"
                action="/api/photoelectric/video/upload"
                :chunk-size="5 * 1024 * 1024"
                accept="video/mp4,video/mov,video/avi"
                :show-file-list="true"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :on-progress="handleUploadProgress"
                :before-upload="beforeUpload"
                :data="{ username: userInfo.username }"
                drag
                :multiple="false"
                class="uploader"
              >
                <div class="upload-icon">
                  <i class="el-icon-upload"></i>
                </div>
                <div class="upload-text">
                  <h3>拖放【{{ project.project_name }}】的训练视频到此处</h3>
                  <p>或 <span class="upload-btn-text">点击上传</span></p>
                </div>
                <div class="upload-tip">
                  <i class="el-icon-info"></i> 仅支持mp4/mov/avi格式，单个文件不超过100MB
                </div>
              </el-upload>

              <!-- 进度条 -->
              <el-progress 
                v-if="uploadProgress > 0 && uploadProgress < 100" 
                :percentage="uploadProgress" 
                class="progress-bar"
                stroke-width="8"
                status="success"
              ></el-progress>

              <!-- 分析按钮 -->
              <div class="action-group">
                <el-button 
                  v-if="uploadedFilename" 
                  type="primary" 
                  @click="analyzeCurrentProject"
                  :loading="analyzing"
                  size="large"
                >
                  {{ analyzing ? '分析中...' : '开始分析当前光电项目' }}
                </el-button>
              </div>
            </div>

            <!-- 已完成的项目分析结果 -->
            <div class="project-result" v-show="idx === currentProjectIndex && project.is_analyzed">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="项目得分">{{ project?.analysis_result?.project_score || 0 }}分</el-descriptions-item>
                <el-descriptions-item label="视频时长">{{ project?.video_duration || 0 }}秒</el-descriptions-item>
                <el-descriptions-item label="完成步骤数">{{ project?.analysis_result?.step_completed_count || 0 }}</el-descriptions-item>
                <el-descriptions-item label="错误步骤数">{{ project?.analysis_result?.step_error_count || 0 }}</el-descriptions-item>
              </el-descriptions>

              <el-divider content-position="left">操作规范性分析</el-divider>
              <p>{{ project?.analysis_result?.action_norm_analysis || '暂无分析数据' }}</p>

              <el-divider content-position="left">扣分项</el-divider>
              <div class="deduction-list">
                <div 
                  v-for="(deduction, idx) in project?.analysis_result?.deduction_items || []" 
                  :key="idx"
                  class="deduction-item"
                >
                  <el-tag type="danger" size="small">-{{ deduction?.deduction_score || 0 }}分</el-tag>
                  <span style="margin-left: 10px;">{{ deduction?.reason || '无' }}</span>
                </div>
              </div>

              <el-divider content-position="left">改进建议</el-divider>
              <div class="suggest-list">
                <div 
                  v-for="(suggest, idx) in project?.analysis_result?.improvement_suggestions || []" 
                  :key="idx"
                  class="suggest-item"
                >
                  {{ idx+1 }}. {{ suggest }}
                </div>
              </div>

              <!-- 自动跳到下一个项目的按钮 -->
              <div class="next-project-btn" v-if="idx < projectList.length - 1 && !projectList[idx+1]?.is_analyzed">
                <el-button type="primary" @click="currentProjectIndex = idx+1">
                  进行下一个光电项目
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 全部完成后，整体汇总报告 -->
      <el-card v-if="trainingDayInfo.is_finished && trainingDayInfo.overall_analysis" class="summary-card" shadow="never">
        <template #header>
          <div class="card-header">
            <i class="el-icon-data-line"></i>
            <span>光电项目训练日整体汇总报告</span>
          </div>
        </template>

        <div class="score-card">
          <div class="score-circle">
            {{ trainingDayInfo?.overall_analysis?.overall_score || 0 }}
            <span class="score-unit">分</span>
          </div>
          <div class="score-desc">本次光电项目训练整体评分</div>
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="never" class="stat-card">
              <template #header><span>高频扣分项</span></template>
              <div class="deduction-list">
                <div 
                  v-for="(item, idx) in trainingDayInfo?.overall_analysis?.high_freq_deductions || []" 
                  :key="idx"
                  class="deduction-item"
                >
                  {{ idx+1 }}. {{ item }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" class="stat-card">
              <template #header><span>核心短板</span></template>
              <div class="suggest-list">
                <div 
                  v-for="(item, idx) in trainingDayInfo?.overall_analysis?.core_shortcomings || []" 
                  :key="idx"
                  class="suggest-item"
                >
                  {{ idx+1 }}. {{ item }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-divider content-position="left">整体用时分析</el-divider>
        <el-card shadow="never" class="summary-card-inner">
          {{ trainingDayInfo?.overall_analysis?.time_overall_analysis || '暂无分析数据' }}
        </el-card>

        <el-divider content-position="left">优势分析</el-divider>
        <el-card shadow="never" class="summary-card-inner">
          {{ trainingDayInfo?.overall_analysis?.advantage_analysis || '暂无分析数据' }}
        </el-card>

        <el-divider content-position="left">整体改进建议</el-divider>
        <div class="suggest-list">
          <div 
            v-for="(suggest, idx) in trainingDayInfo?.overall_analysis?.overall_improvement_suggestions || []" 
            :key="idx"
            class="suggest-item"
          >
            {{ idx+1 }}. {{ suggest }}
          </div>
        </div>
      </el-card>

      <!-- 全部项目完成后，生成汇总按钮 -->
      <div class="summary-action" v-if="allProjectFinished && !trainingDayInfo.overall_analysis">
        <el-button type="primary" size="large" @click="generateSummary" :loading="summaryLoading">
          生成光电项目整体训练汇总报告
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import HeaderNav from '@/components/HeaderNav.vue'

const router = useRouter()
const route = useRoute()
const trainingDayId = route.params.id

// 响应式变量
const loading = ref(true)
const trainingDayInfo = ref({})
const projectList = ref([])
const currentProjectIndex = ref(0)
const userInfo = ref({ username: '' })
const uploadRef = ref(null)
const uploadProgress = ref(0)
const uploadedFilename = ref('')
const analyzing = ref(false)
const summaryLoading = ref(false)

// 计算属性
const finishedCount = computed(() => {
  return projectList.value.filter(p => p.is_analyzed).length
})
const allProjectFinished = computed(() => {
  return projectList.value.length > 0 && projectList.value.every(p => p.is_analyzed)
})

// 初始化用户信息
const initUserInfo = () => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (userInfoStr) {
      userInfo.value = JSON.parse(userInfoStr)
    } else {
      ElMessage.warning('请先登录')
      router.push('/login')
    }
  } catch (e) {
    ElMessage.warning('用户信息异常，请重新登录')
    router.push('/login')
  }
}

// 获取光电项目训练日详情
const getTrainingDayDetail = async () => {
  if (!trainingDayId || !userInfo.value.username) return
  loading.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/day/detail', {
      training_day_id: trainingDayId,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      trainingDayInfo.value = res.data.detail
      projectList.value = res.data.detail.project_list || []
      // 自动定位到第一个未完成的项目
      const unFinishIndex = projectList.value.findIndex(p => !p.is_analyzed)
      currentProjectIndex.value = unFinishIndex >= 0 ? unFinishIndex : 0
    }
  } catch (err) {
    ElMessage.error('获取光电项目训练日详情失败')
  } finally {
    loading.value = false
  }
}

// 上传相关逻辑（和原有单视频上传完全兼容）
const beforeUpload = (file) => {
  if (!userInfo.value.username) {
    ElMessage.warning('请先登录后再上传视频！')
    return false
  }
  const allowedTypes = ['video/mp4', 'video/mov', 'video/avi']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持上传mp4/mov/avi格式的视频！')
    return false
  }
  const maxSize = 100 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件大小超过100MB限制，当前：${(file.size/1024/1024).toFixed(2)}MB`)
    return false
  }
  uploadProgress.value = 0
  return true
}
const handleUploadProgress = (e) => {
  uploadProgress.value = Math.round(e.percent)
}
const handleUploadSuccess = (res) => {
  uploadProgress.value = 100
  uploadedFilename.value = res.file_info?.filename || ''
  if (!uploadedFilename.value) {
    ElMessage.warning('未获取到文件名，请重新上传！')
    return
  }
  ElMessage.success('光电项目视频上传成功！')
  if (uploadRef.value) uploadRef.value.clearFiles()
  setTimeout(() => { uploadProgress.value = 0 }, 2000)
}
const handleUploadError = (err) => {
  uploadProgress.value = 0
  let msg = '光电项目视频上传失败，请重试！'
  if (err.response?.data?.detail) msg = err.response.data.detail
  ElMessage.error(msg)
}

// 分析当前光电项目
const analyzeCurrentProject = async () => {
  if (!uploadedFilename.value) {
    ElMessage.warning('请先上传视频！')
    return
  }
  const currentProject = projectList.value[currentProjectIndex.value]
  analyzing.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/project/analyze', {
      training_day_id: trainingDayId,
      project_id: currentProject.project_id,
      filename: uploadedFilename.value,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      ElMessage.success('光电项目分析完成！')
      uploadedFilename.value = ''
      // 刷新详情
      getTrainingDayDetail()
    }
  } catch (err) {
    let msg = '光电项目分析失败！'
    if (err.response?.data?.detail) msg = err.response.data.detail
    ElMessage.error(msg)
  } finally {
    analyzing.value = false
  }
}

// 生成光电项目整体汇总
const generateSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/day/summary', {
      training_day_id: trainingDayId,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      ElMessage.success('光电项目整体汇总生成完成！')
      getTrainingDayDetail()
    }
  } catch (err) {
    let msg = '生成光电项目汇总失败！'
    if (err.response?.data?.detail) msg = err.response.data.detail
    ElMessage.error(msg)
  } finally {
    summaryLoading.value = false
  }
}

// 返回光电项目训练日列表页
const goBack = () => {
  router.push('/photoelectric/training/day-list')
}

onMounted(() => {
  initUserInfo()
  getTrainingDayDetail()
})
</script>

<style scoped>
.training-detail-container {
  min-height: 100vh;
  background: #f5f7fa;
}
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-info {
  display: flex;
  gap: 10px;
}
.project-card {
  border-radius: 12px;
  margin-bottom: 30px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

/* 项目列表样式 */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.project-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}
.project-item.project-active {
  border-color: #409eff;
}
.project-item.project-finished {
  border-color: #67c23a;
}
.project-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fafafa;
  cursor: pointer;
  user-select: none;
}
.project-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.project-order {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  padding: 0;
}
.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.project-status {
  font-size: 14px;
  color: #909399;
}
.project-arrow {
  font-size: 16px;
  color: #909399;
  transition: transform 0.3s ease;
}
.project-arrow.rotate {
  transform: rotate(180deg);
}
.project-content {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
}
.project-result {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: #f8fafc;
}
.next-project-btn {
  text-align: center;
  margin-top: 20px;
}

/* 列表样式（替代el-list，避免注册问题） */
.deduction-list, .suggest-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.deduction-item, .suggest-item {
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
}

/* 上传区域样式 */
.uploader {
  margin: 20px 0;
}
.upload-icon {
  font-size: 48px;
  color: #3b82f6;
  margin-bottom: 16px;
  text-align: center;
}
.upload-text {
  text-align: center;
  font-size: 16px;
  color: #475569;
}
.upload-text h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}
.upload-btn-text {
  color: #3b82f6;
  font-weight: 600;
}
.upload-tip {
  margin-top: 16px;
  font-size: 14px;
  color: #94a3b8;
  text-align: center;
}
.progress-bar {
  margin: 20px 0;
}
.action-group {
  text-align: center;
  margin: 20px 0;
}

/* 汇总报告样式 */
.summary-card {
  border-radius: 12px;
  margin-bottom: 30px;
}
.score-card {
  text-align: center;
  margin-bottom: 30px;
}
.score-circle {
  width: 120px;
  height: 120px;
  line-height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
  font-size: 48px;
  font-weight: 700;
  margin: 0 auto 16px;
}
.score-unit {
  font-size: 18px;
}
.score-desc {
  font-size: 16px;
  color: #475569;
}
.stat-card {
  margin-bottom: 20px;
}
.summary-card-inner {
  line-height: 1.8;
  color: #1e293b;
}
.summary-action {
  text-align: center;
  margin: 30px 0;
}
</style>