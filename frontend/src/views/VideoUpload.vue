<template>
  <div class="upload-container">
    <!-- 顶部导航栏 -->
    <div class="header-nav">
      <div class="nav-content">
        <div class="logo">
          <i class="el-icon-video-camera"></i>
          <span>世界技能大赛 - 训练视频分析系统</span>
        </div>
        <div class="user-info" v-if="userInfo.username">
          <el-tag type="info" effect="dark">
            <i class="el-icon-user"></i> {{ userInfo.username }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <el-page-header content="视频上传与分析" class="page-header"></el-page-header>
      
      <!-- 上传区域 -->
      <el-card shadow="none" class="upload-card">
        <div class="upload-card-inner">
          <el-upload
            ref="uploadRef"
            action="/api/video/upload"
            :chunk-size="5 * 1024 * 1024"
            :chunk-number="(n) => n - 1"
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
              <h3>拖放视频文件到此处</h3>
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
            :indeterminate="uploadProgress > 0"
            class="progress-bar"
            stroke-width="8"
            status="success"
          ></el-progress>
          
          <!-- 分析按钮 -->
          <div class="action-group">
            <el-button 
              v-if="uploadedFilename && userInfo.username" 
              type="primary" 
              @click="analyzeVideo"
              :loading="analyzing"
              class="analyze-btn"
              size="large"
            >
              <i class="el-icon-s-data" v-if="!analyzing"></i>
              {{ analyzing ? '分析中...' : '调用Qwen3.5-Plus分析视频' }}
            </el-button>
            
            <el-alert 
              v-if="!userInfo.username" 
              title="请先完成登录，再进行视频分析" 
              type="warning" 
              show-icon 
              class="login-alert"
              :closable="false"
            ></el-alert>
          </div>
        </div>
      </el-card>

      <!-- 分析结果 -->
      <el-card shadow="none" class="result-card" v-if="analysisResult">
        <template #header>
          <div class="card-header">
            <i class="el-icon-chart"></i>
            <span>Qwen3.5-Plus 视频分析结果</span>
          </div>
        </template>
        
        <!-- 评分卡片 -->
        <div class="score-card">
          <div class="score-circle">
            {{ analysisResult.analysis_result?.action_norm_score || 0 }}
            <span class="score-unit">分</span>
          </div>
          <div class="score-desc">技术动作规范性评分</div>
        </div>
        
        <!-- 视频基本信息 -->
        <el-descriptions title="视频基本信息" border class="desc-card">
          <el-descriptions-item label="文件名" width="200px">{{ analysisResult.video_filename || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="视频时长">{{ analysisResult.video_duration || 0 }} 秒</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ analysisResult.analysis_time || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="关键动作数量">{{ analysisResult.analysis_result?.video_stats?.action_count || 0 }}</el-descriptions-item>
        </el-descriptions>

        <!-- 分析总结 -->
        <el-divider content-position="left" class="divider">
          <i class="el-icon-document"></i> 分析总结
        </el-divider>
        <el-card class="summary-card" shadow="none">
          {{ analysisResult.analysis_result?.analysis_summary || '暂无分析总结' }}
        </el-card>

        <!-- 改进建议 -->
        <el-divider content-position="left" class="divider">
          <i class="el-icon-lightbulb"></i> 改进建议
        </el-divider>
        <el-list 
          v-if="analysisResult.analysis_result?.improvement_suggestions && analysisResult.analysis_result.improvement_suggestions.length" 
          border 
          class="suggest-list"
        >
          <el-list-item v-for="(item, idx) in analysisResult.analysis_result.improvement_suggestions" :key="`s-${idx}-${item.substring(0,8)}`">
            <el-tag type="warning" size="small" class="suggest-tag">{{ idx+1 }}</el-tag> 
            <span class="suggest-text">{{ item }}</span>
          </el-list-item>
        </el-list>
        <el-empty v-else description="暂无改进建议" class="empty-tip"></el-empty>
      </el-card>

      <!-- 历史记录 -->
      <el-card shadow="none" class="history-card" v-if="historyList.length>0">
        <template #header>
          <div class="card-header">
            <i class="el-icon-time"></i>
            <span>历史分析记录</span>
            <el-button type="text" @click="loadHistory" class="refresh-btn">
              <i class="el-icon-refresh"></i> 刷新
            </el-button>
          </div>
        </template>
        <el-table 
          :data="historyList" 
          border 
          @row-click="showHistoryRecord"
          class="history-table"
          stripe
          highlight-current-row
        >
          <el-table-column prop="video_filename" label="视频文件名" min-width="300"></el-table-column>
          <el-table-column prop="analysis_time" label="分析时间" width="200"></el-table-column>
          <el-table-column label="评分" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.analysis_result?.action_norm_score >= 80 ? 'success' : scope.row.analysis_result?.action_norm_score >= 60 ? 'warning' : 'danger'">
                {{ scope.row.analysis_result?.action_norm_score || 0 }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="primary" size="small" icon="el-icon-view" @click="showHistoryRecord(scope.row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <el-empty 
        v-if="userInfo.username && historyList.length===0" 
        description="暂无历史分析记录，请先上传并分析视频" 
        class="empty-tip"
      ></el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 基础配置：适配 FastAPI 的传参要求
axios.defaults.baseURL = '/'
// 全局设置 Content-Type（FastAPI 解析 JSON 需此头）
axios.defaults.headers.common['Content-Type'] = 'application/json;charset=utf-8'
// 允许跨域携带凭证（若后端有跨域，需此配置）
axios.defaults.withCredentials = true

// 容错获取用户信息（防 JSON 解析错误）
let userInfoInit = { username: '' }
try {
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    userInfoInit = JSON.parse(userInfoStr)
    // 确保 username 是字符串（FastAPI 不接受 undefined/null）
    userInfoInit.username = userInfoInit.username || ''
  }
} catch (e) {
  ElMessage.warning('用户信息异常，已重置！')
}
const userInfo = ref(userInfoInit)

// 响应式变量
const uploadProgress = ref(0)
const uploadRef = ref(null)
const uploadedFilename = ref('')
const analyzing = ref(false)
const analysisResult = ref(null)
const historyList = ref([])

// 上传前校验（确保参数非空）
const beforeUpload = (file) => {
  // 1. 校验登录（username 非空）
  if (!userInfo.value.username) {
    ElMessage.warning('请先登录后再上传视频！')
    return false
  }
  // 2. 校验格式
  const allowedTypes = ['video/mp4', 'video/mov', 'video/avi']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持上传mp4/mov/avi格式的视频！')
    return false
  }
  // 3. 校验大小
  const maxSize = 100 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件大小超过100MB限制，当前：${(file.size/1024/1024).toFixed(2)}MB`)
    return false
  }
  uploadProgress.value = 0
  return true
}

// 上传进度
const handleUploadProgress = (e) => {
  uploadProgress.value = Math.round(e.percent)
}

// 上传成功（确保 filename 非空）
const handleUploadSuccess = (res) => {
  uploadProgress.value = 100
  // 兼容后端可能的字段名（filename/file_name）
  uploadedFilename.value = res.file_info?.filename || res.file_info?.file_name || ''
  
  // 校验 filename（避免传空给后端）
  if (!uploadedFilename.value) {
    ElMessage.warning('未获取到文件名，请重新上传！')
    return
  }
  
  ElMessage.success('视频上传成功！')
  if (uploadRef.value) uploadRef.value.clearFiles()
  setTimeout(() => { uploadProgress.value = 0 }, 2000)
}

// 上传失败（精准捕获后端错误）
const handleUploadError = (err) => {
  uploadProgress.value = 0
  let msg = '视频上传失败，请重试！'
  // 优先显示 FastAPI 返回的 detail 错误
  if (err.response?.data?.detail) msg = err.response.data.detail
  else if (err.message) msg = err.message
  ElMessage.error(msg)
}

// 分析视频（适配 FastAPI 传参：参数非空 + JSON 格式）
const analyzeVideo = async () => {
  // 前置校验（杜绝空参数传给后端）
  if (!uploadedFilename.value) {
    ElMessage.warning('请先上传视频！')
    return
  }
  if (!userInfo.value.username) {
    ElMessage.warning('请先登录！')
    return
  }

  analyzing.value = true
  try {
    // 传参格式：严格 JSON，参数名和后端保持一致
    const res = await axios.post('/api/video/analyze', {
      filename: uploadedFilename.value,
      username: userInfo.value.username
    })

    if (res.data.code === 200) {
      analysisResult.value = res.data.analysis_record
      ElMessage.success('视频分析完成！')
      loadHistory()
    } else {
      ElMessage.error(res.data.message || '分析失败！')
    }
  } catch (err) {
    let msg = '分析失败！'
    // 显示 FastAPI 的 422 具体错误
    if (err.response?.data?.detail) {
      // 解析 FastAPI 的详细错误（数组格式）
      if (Array.isArray(err.response.data.detail)) {
        msg = err.response.data.detail.map(item => item.msg).join('；')
      } else {
        msg = err.response.data.detail
      }
    } else if (err.message) {
      msg = err.message
    }
    ElMessage.error(msg)
  } finally {
    analyzing.value = false
  }
}

// 加载历史记录（适配 FastAPI 传参）
const loadHistory = async () => {
  if (!userInfo.value.username) return
  
  try {
    const res = await axios.post('/api/video/analysis/history', {
      username: userInfo.value.username
    })
    historyList.value = res.data.history || []
  } catch (err) {
    let msg = '加载历史记录失败！'
    if (err.response?.data?.detail) {
      if (Array.isArray(err.response.data.detail)) {
        msg = err.response.data.detail.map(item => item.msg).join('；')
      } else {
        msg = err.response.data.detail
      }
    } else if (err.message) {
      msg = err.message
    }
    ElMessage.error(msg)
  }
}

// 查看历史详情
const showHistoryRecord = (record) => {
  analysisResult.value = record
}

// 挂载加载历史
onMounted(() => {
  if (userInfo.value.username) loadHistory()
})
</script>

<style scoped>
/* 全局样式 */
.upload-container {
  min-height: 100vh;
  background: #f5f7fa;
}

/* 顶部导航 */
.header-nav {
  background: #1e40af;
  color: white;
  padding: 0 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}
.logo i {
  font-size: 24px;
}
.user-info {
  font-size: 14px;
}

/* 主内容区 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.page-header {
  margin-bottom: 20px;
}

/* 上传卡片 */
.upload-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  padding: 40px;
  margin-bottom: 30px;
}
.upload-card-inner {
  max-width: 800px;
  margin: 0 auto;
}
.uploader {
  border-radius: 8px;
  overflow: hidden;
}
:deep(.el-upload-dragger) {
  width: 100%;
  padding: 60px 0;
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  transition: all 0.3s ease;
}
:deep(.el-upload-dragger:hover) {
  border-color: #3b82f6;
  background: #eff6ff;
}
.upload-icon {
  font-size: 48px;
  color: #3b82f6;
  margin-bottom: 16px;
}
.upload-text {
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
  cursor: pointer;
}
.upload-tip {
  margin-top: 16px;
  font-size: 14px;
  color: #94a3b8;
}

/* 进度条 */
.progress-bar {
  margin: 24px 0;
}
:deep(.el-progress-bar__outer) {
  border-radius: 4px;
  background: #e2e8f0;
}
:deep(.el-progress-bar__inner) {
  background: #3b82f6;
}

/* 操作按钮组 */
.action-group {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
.analyze-btn {
  padding: 12px 32px;
  font-size: 16px;
  border-radius: 8px;
  background: #3b82f6;
  border: none;
  transition: all 0.3s ease;
}
:deep(.analyze-btn:hover) {
  background: #2563eb;
  transform: translateY(-2px);
}
.login-alert {
  width: 100%;
  margin: 0;
}

/* 结果卡片 */
.result-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  padding: 30px;
  margin-bottom: 30px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.card-header i {
  color: #3b82f6;
}

/* 评分卡片 */
.score-card {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
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
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
  position: relative;
}
.score-unit {
  font-size: 18px;
  position: absolute;
  bottom: 25px;
  right: 25px;
}
.score-desc {
  font-size: 16px;
  color: #475569;
  font-weight: 500;
}

/* 描述卡片 */
.desc-card {
  margin-bottom: 24px;
}
:deep(.el-descriptions__header) {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 16px;
}
:deep(.el-descriptions-item__label) {
  font-weight: 500;
  color: #475569;
}

/* 分割线 */
.divider {
  margin: 24px 0;
}
:deep(.el-divider__text) {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}
.divider i {
  color: #3b82f6;
  margin-right: 8px;
}

/* 总结卡片 */
.summary-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 20px;
  line-height: 1.8;
  color: #1e293b;
  font-size: 15px;
}

/* 建议列表 */
.suggest-list {
  margin-top: 8px;
}
.suggest-tag {
  margin-right: 12px;
}
.suggest-text {
  line-height: 1.6;
  color: #475569;
}
:deep(.el-list-item) {
  padding: 16px 12px;
  border-bottom: 1px solid #f1f5f9;
}
:deep(.el-list-item:last-child) {
  border-bottom: none;
}

/* 历史记录 */
.history-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  padding: 30px;
  margin-bottom: 30px;
}
.refresh-btn {
  color: #3b82f6;
}
.history-table {
  margin-top: 16px;
  border-radius: 8px;
  overflow: hidden;
}
:deep(.el-table) {
  --el-table-header-text-color: #475569;
  --el-table-row-hover-bg-color: #eff6ff;
}
:deep(.el-table th) {
  background: #f8fafc;
  font-weight: 600;
}

/* 空状态 */
.empty-tip {
  padding: 40px 0;
  text-align: center;
  color: #94a3b8;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .upload-card {
    padding: 20px;
  }
  .result-card, .history-card {
    padding: 20px;
  }
  .score-circle {
    width: 80px;
    height: 80px;
    line-height: 80px;
    font-size: 32px;
  }
  .score-unit {
    bottom: 15px;
    right: 15px;
    font-size: 14px;
  }
}
</style>