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
          <el-tag type="info" size="large">
            完成进度：{{ finishedCount }} / {{ projectList.length }}
          </el-tag>
        </div>
      </div>

      <!-- 加载提示 -->
      <el-empty v-if="loading" description="加载光电项目训练日信息中..."></el-empty>

      <!-- 项目标签页（核心：顶部导航切换） -->
      <el-card v-if="!loading" class="project-card" shadow="never">
        <template #header>
          <div class="card-header">
            <i class="el-icon-menu"></i>
            <span>光电训练项目（点击标签切换）</span>
          </div>
        </template>

        <el-tabs v-model="currentProjectIndex" type="card" class="project-tabs">
          <el-tab-pane
            v-for="(project, idx) in projectList"
            :key="project.project_id"
            :label="`${idx+1}. ${project.project_name}${project.is_analyzed ? ' 【已完成】' : ''}`"
            :class="{'project-finished-tab': project.is_analyzed}"
          >
            <div class="project-content-wrapper">
              <!-- 项目描述 -->
              <el-alert 
                :title="`当前正在进行【${project.project_name}】项目训练`" 
                type="info" 
                :closable="false"
                style="margin-bottom: 20px;"
              >
                <template #default>
                  {{ project.project_desc }}
                </template>
              </el-alert>

              <!-- 未完成：根据评分类型渲染不同上传组件 -->
              <div v-if="!project.is_analyzed">
                <!-- 类型1：视频分析（原有逻辑） -->
                <div v-if="project.evaluation_type === 'video_analysis'">
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

                  <el-progress 
                    v-if="uploadProgress > 0 && uploadProgress < 100" 
                    :percentage="uploadProgress" 
                    class="progress-bar"
                    stroke-width="8"
                    status="success"
                  ></el-progress>

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

                <!-- 类型2：文档上传 -->
                <div v-else-if="project.evaluation_type === 'doc_upload'">
                  <el-upload
                    ref="docUploadRef"
                    action="/api/photoelectric/doc/upload"
                    accept=".txt,.pdf,.docx"
                    :show-file-list="true"
                    :on-success="handleDocUploadSuccess"
                    :on-error="handleDocUploadError"
                    :before-upload="beforeDocUpload"
                    :data="{ username: userInfo.username, project_id: project.project_id }"
                    drag
                    :multiple="false"
                    class="uploader"
                  >
                    <div class="upload-icon">
                      <i class="el-icon-document"></i>
                    </div>
                    <div class="upload-text">
                      <h3>拖放【{{ project.project_name }}】的分析文档到此处</h3>
                      <p>或 <span class="upload-btn-text">点击上传</span></p>
                    </div>
                    <div class="upload-tip">
                      <i class="el-icon-info"></i> 仅支持txt/pdf/docx格式，单个文件不超过20MB
                    </div>
                  </el-upload>

                  <div class="action-group">
                    <el-button 
                      v-if="uploadedDocFilename" 
                      type="primary" 
                      @click="analyzeCurrentDocProject"
                      :loading="analyzing"
                      size="large"
                    >
                      {{ analyzing ? '分析中...' : '提交文档并分析' }}
                    </el-button>
                  </div>
                </div>

                <!-- 类型3：图片对比 -->
                <div v-else-if="project.evaluation_type === 'image_compare'">
                  <div class="image-compare-wrapper">
                    <div class="image-upload-group">
                      <h4>上传您的操作图片</h4>
                      <el-upload
                        ref="userImageUploadRef"
                        action="/api/photoelectric/image/upload"
                        accept="image/jpg,image/png,image/jpeg"
                        :show-file-list="true"
                        :on-success="handleUserImageUploadSuccess"
                        :on-error="handleImageUploadError"
                        :before-upload="beforeImageUpload"
                        :data="{ username: userInfo.username, project_id: project.project_id, type: 'user' }"
                        drag
                        :multiple="false"
                        class="image-uploader"
                      >
                        <div class="upload-icon">
                          <i class="el-icon-picture"></i>
                        </div>
                        <div class="upload-text">
                          <p>拖放操作图片到此处</p>
                          <p>或 <span class="upload-btn-text">点击上传</span></p>
                        </div>
                      </el-upload>
                    </div>

                    <div class="image-upload-group">
                      <h4>标准操作参考图</h4>
                      <div class="standard-image">
                        <img :src="project.standard_image_url || 'http://localhost:8000/static/assets/standard_clean.jpg'" 
                             alt="标准操作图" style="max-width: 300px; border: 1px solid #e4e7ed;" />
                        <p>（系统内置标准参考图）</p>
                      </div>
                    </div>
                  </div>

                  <div class="action-group">
                    <el-button 
                      v-if="uploadedUserImageFilename" 
                      type="primary" 
                      @click="analyzeCurrentImageProject"
                      :loading="analyzing"
                      size="large"
                    >
                      {{ analyzing ? '对比分析中...' : '开始对比分析' }}
                    </el-button>
                  </div>
                </div>

                <!-- 类型4：步骤截图 -->
                <div v-else-if="project.evaluation_type === 'step_screenshot'">
                  <el-upload
                    ref="stepScreenshotUploadRef"
                    action="/api/photoelectric/step/screenshot/upload"
                    accept="image/jpg,image/png,image/jpeg"
                    :show-file-list="true"
                    :on-success="handleStepScreenshotUploadSuccess"
                    :on-error="handleStepScreenshotUploadError"
                    :before-upload="beforeStepScreenshotUpload"
                    :data="{ username: userInfo.username, project_id: project.project_id }"
                    drag
                    :multiple="true"
                    class="uploader"
                  >
                    <div class="upload-icon">
                      <i class="el-icon-picture"></i>
                    </div>
                    <div class="upload-text">
                      <h3>拖放【{{ project.project_name }}】的关键步骤截图到此处</h3>
                      <p>或 <span class="upload-btn-text">点击上传</span>（可多选）</p>
                    </div>
                    <div class="upload-tip">
                      <i class="el-icon-info"></i> 仅支持jpg/png格式，单个文件不超过5MB，最多上传10张
                    </div>
                  </el-upload>

                  <div class="action-group">
                    <el-button 
                      v-if="uploadedStepScreenshotFilenames.length > 0" 
                      type="primary" 
                      @click="analyzeCurrentStepScreenshotProject"
                      :loading="analyzing"
                      size="large"
                    >
                      {{ analyzing ? '分析中...' : '提交步骤截图并分析' }}
                    </el-button>
                  </div>
                </div>

                <!-- 未知类型 -->
                <div v-else>
                  <el-alert title="未知评分方式" type="error" :closable="false">
                    该项目的评分方式未配置，请联系管理员
                  </el-alert>
                </div>
              </div>

              <!-- 已完成：展示分析结果（移除自动跳转按钮） -->
              <div v-else class="project-result">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="项目得分">{{ project?.analysis_result?.project_score || 0 }}分</el-descriptions-item>
                  <el-descriptions-item label="视频时长" v-if="project.evaluation_type === 'video_analysis'">{{ project?.video_duration || 0 }}秒</el-descriptions-item>
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
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 汇总报告部分（和原有逻辑完全一致） -->
      <el-card v-if="trainingDayInfo.is_finished && trainingDayInfo.overall_analysis" class="summary-card" shadow="never">
        <!-- 原有汇总代码不变 -->
      </el-card>

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

// 新增：不同评分类型的上传变量
const docUploadRef = ref(null)
const uploadedDocFilename = ref('')
const userImageUploadRef = ref(null)
const uploadedUserImageFilename = ref('')
const stepScreenshotUploadRef = ref(null)
const uploadedStepScreenshotFilenames = ref([])



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
      // const unFinishIndex = projectList.value.findIndex(p => !p.is_analyzed)
      // currentProjectIndex.value = unFinishIndex >= 0 ? unFinishIndex : 0
      //默认显示第一个项目，不会自动跳转
      currentProjectIndex.value = 0
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
  router.push('/photoelectric/training/day/list')
}

onMounted(() => {
  initUserInfo()
  getTrainingDayDetail()
})
// ------------------- 新增：文档上传/分析 -------------------
const beforeDocUpload = (file) => {
  const allowedTypes = ['.txt', '.pdf', '.docx']
  const fileExt = file.name.slice(file.name.lastIndexOf('.'))
  if (!allowedTypes.includes(fileExt)) {
    ElMessage.error('仅支持txt/pdf/docx格式文档！')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文档大小不能超过20MB！')
    return false
  }
  return true
}
const handleDocUploadSuccess = (res) => {
  uploadedDocFilename.value = res.file_info?.filename || ''
  ElMessage.success('文档上传成功！')
  docUploadRef.value.clearFiles()
}
const handleDocUploadError = (err) => {
  ElMessage.error('文档上传失败，请重试！')
}
const analyzeCurrentDocProject = async () => {
  const currentProject = projectList.value[currentProjectIndex.value]
  analyzing.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/project/analyze/doc', {
      training_day_id: trainingDayId,
      project_id: currentProject.project_id,
      filename: uploadedDocFilename.value,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      ElMessage.success('文档分析完成！')
      uploadedDocFilename.value = ''
      getTrainingDayDetail()
    }
  } catch (err) {
    ElMessage.error('文档分析失败：' + (err.response?.data?.detail || ''))
  } finally {
    analyzing.value = false
  }
}

// ------------------- 新增：图片对比上传/分析 -------------------
const beforeImageUpload = (file) => {
  const allowedTypes = ['image/jpg', 'image/png', 'image/jpeg']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持jpg/png格式图片！')
    return false
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB！')
    return false
  }
  return true
}
const handleUserImageUploadSuccess = (res) => {
  uploadedUserImageFilename.value = res.file_info?.filename || ''
  ElMessage.success('操作图片上传成功！')
    // 方式1：判空 + 正确调用（推荐）
  if (userImageUploadRef.value && typeof userImageUploadRef.value.clearFiles === 'function') {
    userImageUploadRef.value.clearFiles()
  }
  // 方式2：Element Plus 新版兼容写法（如果方式1仍报错，用这个）
  // if (userImageUploadRef.value) {
  //   userImageUploadRef.value.uploadFiles = []; // 直接清空文件列表
  // }
}
const handleImageUploadError = (err) => {
  ElMessage.error('图片上传失败，请重试！')
}
const analyzeCurrentImageProject = async () => {
  const currentProject = projectList.value[currentProjectIndex.value]
  analyzing.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/project/analyze/image', {
      training_day_id: trainingDayId,
      project_id: currentProject.project_id,
      user_image_filename: uploadedUserImageFilename.value,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      ElMessage.success('图片对比分析完成！')
      uploadedUserImageFilename.value = ''
      getTrainingDayDetail()
    }
  } catch (err) {
    ElMessage.error('图片对比分析失败：' + (err.response?.data?.detail || ''))
  } finally {
    analyzing.value = false
  }
}

// ------------------- 新增：步骤截图上传/分析 -------------------
const beforeStepScreenshotUpload = (file) => {
  const allowedTypes = ['image/jpg', 'image/png', 'image/jpeg']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持jpg/png格式截图！')
    return false
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('单张截图大小不能超过5MB！')
    return false
  }
  if (uploadedStepScreenshotFilenames.value.length >= 10) {
    ElMessage.error('最多上传10张步骤截图！')
    return false
  }
  return true
}
const handleStepScreenshotUploadSuccess = (res) => {
  uploadedStepScreenshotFilenames.value.push(res.file_info?.filename || '')
  ElMessage.success('步骤截图上传成功！')
}
const handleStepScreenshotUploadError = (err) => {
  ElMessage.error('步骤截图上传失败，请重试！')
}
const analyzeCurrentStepScreenshotProject = async () => {
  const currentProject = projectList.value[currentProjectIndex.value]
  analyzing.value = true
  try {
    const res = await axios.post('/api/photoelectric/training/project/analyze/step', {
      training_day_id: trainingDayId,
      project_id: currentProject.project_id,
      filenames: uploadedStepScreenshotFilenames.value,
      username: userInfo.value.username
    })
    if (res.data.code === 200) {
      ElMessage.success('步骤截图分析完成！')
      uploadedStepScreenshotFilenames.value = []
      getTrainingDayDetail()
    }
  } catch (err) {
    ElMessage.error('步骤截图分析失败：' + (err.response?.data?.detail || ''))
  } finally {
    analyzing.value = false
  }
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
/* 原有样式不变，新增以下样式 */
.project-tabs {
  margin-top: 10px;
}
.project-content-wrapper {
  padding: 20px 0;
}
.image-compare-wrapper {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
}
.image-upload-group {
  flex: 1;
}
.standard-image {
  flex: 1;
  text-align: center;
  padding-top: 20px;
}
.image-uploader {
  margin: 10px 0;
}
/* ✅ 新增：已完成项目标签样式 */
.project-tabs :deep(.el-tabs__item.project-finished-tab) {
  color: #67c23a !important; /* 绿色文字 */
  font-weight: 600;
}
.project-tabs :deep(.el-tabs__item.project-finished-tab.is-active) {
  color: #409eff !important; /* 选中时保持原蓝色 */
}

/* 如果需要给已完成标签加背景色，可添加下面样式 */
.project-tabs :deep(.el-tabs__item.project-finished-tab) {
  background-color: #f0f9ff;
  border-color: #67c23a;
}
</style>