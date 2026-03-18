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

        <el-tabs v-model="activeTab" class="resource-tabs" style="margin-top: 20px;">
          <!-- 1. 官方文档 -->
          <el-tab-pane label="官方文档" name="official_docs">
            <div v-loading="loadingMap.official_docs" class="loading-wrapper">
              <el-empty v-if="officialDocsList.length === 0 && !loadingMap.official_docs" description="暂无官方文档资源"></el-empty>
              <div class="doc-list">
                <el-card v-for="(doc, idx) in officialDocsList" :key="doc.id" class="doc-card">
                  <div class="doc-header">
                    <i class="el-icon-file-text doc-icon"></i>
                    <span class="doc-title">{{ doc.title }}</span>
                  </div>
                  <div class="doc-info">
                    <p class="doc-desc">{{ doc.desc }}</p>
                    <p class="doc-meta">
                      文件大小：{{ doc.size_mb }}MB | 格式：{{ doc.file_ext?.replace('.', '') || '未知' }}
                    </p>
                  </div>
                  <div class="doc-actions">
                    <el-button type="primary" size="small" @click="previewResource(doc)">
                      <i class="el-icon-view"></i> 预览
                    </el-button>
                    <el-button size="small" @click="downloadResource(doc.file_url)">
                      <i class="el-icon-download"></i> 下载
                    </el-button>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>

          <!-- 2. 标准教程 -->
          <el-tab-pane label="标准教程" name="standard_tutorials">
            <div v-loading="loadingMap.standard_tutorials" class="loading-wrapper">
              <el-empty v-if="tutorialsList.length === 0 && !loadingMap.standard_tutorials" description="暂无技术动作标准教程"></el-empty>
              <el-row :gutter="20" class="tutorial-grid">
                <el-col :span="isMobile ? 24 : 8" v-for="(tutorial, idx) in tutorialsList" :key="tutorial.id">
                  <el-card shadow="hover" class="tutorial-card">
                    <template #header>
                      <span class="tutorial-title">{{ tutorial.title }}</span>
                    </template>
                    <div class="tutorial-img">
                      <img :src="tutorial.cover_url" alt="教程封面" class="cover-img">
                    </div>
                    <div class="tutorial-desc">{{ tutorial.desc }}</div>
                    <div class="tutorial-meta">
                      文件大小：{{ tutorial.size_mb }}MB | 格式：{{ tutorial.file_ext?.replace('.', '') || '未知' }}
                    </div>
                    <div class="tutorial-actions">
                      <el-button type="primary" size="small" @click="previewResource(tutorial)">
                        {{ tutorial.file_ext && tutorial.file_ext.includes('mp4') ? '预览视频' : '查看文档' }}
                      </el-button>
                      <el-button size="small" @click="downloadResource(tutorial.file_url)">
                        下载
                      </el-button>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

          <!-- 3. 往届案例 -->
          <el-tab-pane label="往届案例" name="past_cases">
            <div v-loading="loadingMap.past_cases" class="loading-wrapper">
              <el-empty v-if="casesList.length === 0 && !loadingMap.past_cases" description="暂无往届大赛视频/案例"></el-empty>
              <el-row :gutter="20" class="cases-grid">
                <el-col :span="isMobile ? 24 : 12" v-for="(caseItem, idx) in casesList" :key="caseItem.id">
                  <el-card shadow="hover" class="case-card">
                    <template #header>
                      <span class="case-title">{{ caseItem.title }}</span>
                    </template>
                    <div class="case-video">
                      <video v-if="caseItem.file_ext && caseItem.file_ext.includes('mp4')" :src="getPreviewUrl(caseItem.file_url)" controls class="video-player">
                        您的浏览器不支持视频播放
                      </video>
                      <img v-else :src="caseItem.cover_url" alt="案例封面" class="case-cover-img" @click="previewResource(caseItem)">
                    </div>
                    <div class="case-info">
                      <span class="case-year">{{ caseItem.year }}届 · {{ caseItem.category }}</span>
                      <span class="case-desc">{{ caseItem.desc }}</span>
                      <span class="case-meta">
                        文件大小：{{ caseItem.size_mb }}MB | 格式：{{ caseItem.file_ext?.replace('.', '') || '未知' }}
                      </span>
                    </div>
                    <div class="case-actions">
                      <el-button size="small" @click="previewResource(caseItem)">
                        放大预览
                      </el-button>
                      <el-button size="small" @click="downloadResource(caseItem.file_url)">
                        下载案例
                      </el-button>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 预览弹窗：极简版，无复杂依赖 -->
    <el-dialog v-model="previewDialogVisible" :title="currentResource.title || '资源预览'" width="90%" append-to-body :fullscreen="isFullScreen" @close="handleDialogClose">
      <div class="preview-content">
        <!-- 1. 图片预览 -->
        <img v-if="previewType === 'image'" :src="previewUrl" alt="资源预览" class="preview-img">
        <!-- 2. 视频预览：恢复正常src，保留ref -->
        <video v-if="previewType === 'video'" ref="previewVideo" :src="previewUrl" controls class="preview-video"></video>
        <!-- 3. PDF预览：改用iframe（浏览器原生预览，最稳定） -->
        <iframe v-if="previewType === 'pdf'" :src="previewUrl" class="preview-pdf-iframe" frameborder="0"></iframe>
        <!-- 4. 其他文档 -->
        <div v-if="previewType === 'other'" class="preview-doc-placeholder">
          <i class="el-icon-file-text"></i>
          <p>暂不支持该格式（{{ currentResource.file_ext }}）直接预览，可下载后查看</p>
          <el-button type="primary" @click="downloadResource(currentResource.file_url)" icon="el-icon-download" style="margin-top: 10px;">
            下载文档
          </el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadResource(currentResource.file_url)">
          <i class="el-icon-download"></i> 下载
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import HeaderNav from '@/components/HeaderNav.vue'

// ========== 基础配置 ==========
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
axios.defaults.withCredentials = false

// 激活的标签页
const activeTab = ref('official_docs')
// 加载状态
const loadingMap = ref({ official_docs: false, standard_tutorials: false, past_cases: false })
// 预览相关
const previewDialogVisible = ref(false)
const currentResource = ref({})
const previewType = ref('')
const previewUrl = ref('') // 预览地址（统一管理）
const isFullScreen = ref(false)
const previewVideo = ref(null) // 视频ref

// 资源列表
const officialDocsList = ref([])
const tutorialsList = ref([])
const casesList = ref([])

// 移动端判断
const isMobile = computed(() => window.innerWidth <= 768)

// ========== 核心逻辑 ==========
onMounted(() => {
  loadResourceByType(activeTab.value)
})

// 监听标签页切换
watch(activeTab, (newTab) => {
  const listMap = { official_docs: officialDocsList, standard_tutorials: tutorialsList, past_cases: casesList }
  const targetList = listMap[newTab]
  if (targetList.value.length === 0 && !loadingMap.value[newTab]) {
    loadResourceByType(newTab)
  }
})

// 加载资源
const loadResourceByType = async (resourceType) => {
  loadingMap.value[resourceType] = true
  try {
    const res = await axios.get('/api/static/list', { params: { resource_type: resourceType } })
    if (res.data.code === 200) {
      const resourceList = res.data.resource_list
      switch (resourceType) {
        case 'official_docs': officialDocsList.value = resourceList; break
        case 'standard_tutorials': tutorialsList.value = resourceList; break
        case 'past_cases': casesList.value = resourceList; break
      }
      ElMessage.success(`✅ ${getResourceTypeName(resourceType)}加载成功`)
    } else {
      ElMessage.error(`❌ 加载失败：${res.data.msg}`)
    }
  } catch (err) {
    ElMessage.error(`❌ 加载失败：${err.message || '请检查后端服务'}`)
    console.error('资源加载错误：', err)
  } finally {
    loadingMap.value[resourceType] = false
  }
}

// 生成预览URL（核心：保证地址正确）
const getPreviewUrl = (fileUrl) => {
  if (!fileUrl) return ''
  // 补全域名：如果是相对路径，拼接后端地址
  if (fileUrl.startsWith('http')) {
    return fileUrl
  } else {
    // 处理开头的/：避免重复
    const base = axios.defaults.baseURL.endsWith('/') ? axios.defaults.baseURL : `${axios.defaults.baseURL}/`
    const url = fileUrl.startsWith('/') ? fileUrl.slice(1) : fileUrl
    return base + url
  }
}

// 预览资源（极简版，无复杂逻辑）
const previewResource = (resource) => {
  currentResource.value = resource
  const { file_ext, file_url } = resource
  previewUrl.value = getPreviewUrl(file_url)

  // 判断预览类型
  if (['.jpg', '.png', '.webp', '.gif', '.bmp'].includes(file_ext)) {
    previewType.value = 'image'
  } else if (['.mp4', '.mov', '.avi', '.mkv'].includes(file_ext)) {
    previewType.value = 'video'
    // 重置视频状态（避免缓存）
    if (previewVideo.value) {
      previewVideo.value.pause()
      previewVideo.value.currentTime = 0
    }
  } else if (file_ext === '.pdf') {
    previewType.value = 'pdf'
  } else {
    previewType.value = 'other'
  }

  previewDialogVisible.value = true
}

// 下载资源
const downloadResource = (fileUrl) => {
  if (!fileUrl) {
    ElMessage.warning('暂无有效下载链接')
    return
  }
  try {
    const fullUrl = getPreviewUrl(fileUrl)
    const link = document.createElement('a')
    link.href = fullUrl
    link.download = currentResource.value.title || '资源文件'
    link.click()
  } catch (err) {
    ElMessage.error('下载失败：' + err.message)
  }
}

// 弹窗关闭：停止视频播放（核心修复）
const handleDialogClose = () => {
  // 1. 停止视频播放
  if (previewVideo.value) {
    previewVideo.value.pause()
    previewVideo.value.currentTime = 0
  }
  // 2. 重置状态
  currentResource.value = {}
  previewType.value = ''
  previewUrl.value = ''
  isFullScreen.value = false
}

// 辅助函数
const getResourceTypeName = (resourceType) => {
  const typeMap = { official_docs: '官方文档', standard_tutorials: '标准教程', past_cases: '往届案例' }
  return typeMap[resourceType] || '资源'
}
</script>

<style scoped>
/* 基础样式 */
.resource-page { min-height: 100vh; background: #f5f7fa; }
.resource-content { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
.resource-card { background: white; border-radius: 12px; padding: 30px; }
.card-header { font-size: 18px; font-weight: 600; color: #1e293b; display: flex; align-items: center; gap: 8px; }
.card-header i { color: #3b82f6; }

/* 加载样式 */
.loading-wrapper { min-height: 200px; padding: 20px 0; }
.resource-tabs { --el-tabs-active-color: #3b82f6; margin-bottom: 20px; }

/* 文档列表 */
.doc-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 10px; }
.doc-card { height: 100%; display: flex; flex-direction: column; padding: 15px; }
.doc-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.doc-icon { font-size: 24px; color: #3b82f6; }
.doc-title { font-size: 16px; font-weight: 500; color: #1e293b; }
.doc-info { flex: 1; margin-bottom: 15px; }
.doc-desc { font-size: 14px; color: #64748b; line-height: 1.5; margin: 0 0 5px 0; }
.doc-meta { font-size: 12px; color: #94a3b8; margin: 0; }
.doc-actions { display: flex; gap: 8px; }

/* 教程卡片 */
.tutorial-grid { margin-top: 10px; }
.tutorial-card { height: 100%; display: flex; flex-direction: column; }
.tutorial-title { font-size: 16px; font-weight: 500; }
.tutorial-img { margin: 10px 0; text-align: center; flex: 1; }
.cover-img { width: 100%; height: 180px; object-fit: cover; border-radius: 8px; }
.tutorial-desc { font-size: 14px; color: #64748b; margin: 10px 0; line-height: 1.5; }
.tutorial-meta { font-size: 12px; color: #94a3b8; margin-bottom: 10px; }
.tutorial-actions { display: flex; justify-content: space-between; margin-top: auto; padding-top: 10px; }

/* 案例卡片 */
.cases-grid { margin-top: 10px; }
.case-card { height: 100%; display: flex; flex-direction: column; }
.case-title { font-size: 16px; font-weight: 500; }
.case-video { margin: 10px 0; }
.video-player { width: 100%; height: 240px; border-radius: 8px; }
.case-cover-img { width: 100%; height: 240px; object-fit: cover; border-radius: 8px; cursor: zoom-in; }
.case-info { margin: 10px 0; font-size: 14px; color: #64748b; }
.case-year { display: block; margin-bottom: 5px; color: #3b82f6; font-weight: 500; }
.case-meta { display: block; margin-top: 5px; font-size: 12px; color: #94a3b8; }
.case-actions { display: flex; gap: 8px; margin-top: 10px; }

/* 预览弹窗样式（极简版） */
.preview-content { padding: 10px; }
.preview-img { max-width: 100%; max-height: 700px; border-radius: 8px; }
.preview-video { width: 100%; height: 700px; border-radius: 8px; }
/* PDF iframe样式：浏览器原生预览 */
.preview-pdf-iframe { width: 100%; height: 700px; border-radius: 8px; }
.preview-doc-placeholder { padding: 40px 0; color: #64748b; font-size: 16px; text-align: center; }
.preview-doc-placeholder i { font-size: 48px; margin-bottom: 15px; color: #94a3b8; }

/* 响应式适配 */
@media (max-width: 768px) {
  .resource-card { padding: 20px; }
  .preview-video, .preview-pdf-iframe { height: 400px; }
  .preview-img { max-height: 400px; }
  .video-player, .case-cover-img { height: 180px; }
  .doc-list { grid-template-columns: 1fr; }
}
</style>