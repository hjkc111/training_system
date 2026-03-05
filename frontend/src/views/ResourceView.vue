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

        <!-- 资源分类标签页 -->
        <el-tabs v-model="activeTab" class="resource-tabs" style="margin-top: 20px;">
          <!-- 1. 世界技能大赛官方文档 -->
          <el-tab-pane label="官方文档" name="official_docs">
            <div class="resource-list-container">
              <!-- 文档列表 -->
              <el-list border :data="officialDocsList" class="resource-list">
                <el-list-item v-for="(doc, idx) in officialDocsList" :key="doc.id">
                  <el-list-item-meta>
                    <template #avatar>
                      <i class="el-icon-file-text resource-icon"></i>
                    </template>
                    <template #title>
                      <span class="resource-title">{{ doc.title }}</span>
                    </template>
                    <template #description>
                      <span class="resource-desc">{{ doc.desc }}</span>
                      <br>
                      <span class="resource-meta">文件大小：{{ doc.size_mb }}MB</span>
                    </template>
                  </el-list-item-meta>
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="downloadResource(doc.file_url)"
                    icon="el-icon-download"
                  >
                    下载
                  </el-button>
                </el-list-item>
              </el-list>

              <!-- 无数据提示 -->
              <el-empty v-if="officialDocsList.length === 0 && !loadingMap.official_docs" description="暂无官方文档资源"></el-empty>
              <!-- 加载提示（非全屏，仅当前容器） -->
              <div v-if="loadingMap.official_docs" class="loading-container">
                <el-loading text="加载资源中..."></el-loading>
              </div>
            </div>
          </el-tab-pane>

          <!-- 2. 技术动作标准教程 -->
          <el-tab-pane label="标准教程" name="standard_tutorials">
            <div class="tutorial-container">
              <!-- 教程列表（图文+视频） -->
              <el-row :gutter="20" class="tutorial-grid">
                <el-col :span="isMobile ? 24 : 8" v-for="(tutorial, idx) in tutorialsList" :key="tutorial.id">
                  <el-card shadow="hover" class="tutorial-card">
                    <template #header>
                      <span class="tutorial-title">{{ tutorial.title }}</span>
                    </template>
                    <!-- 教程封面/图片 -->
                    <div class="tutorial-img">
                      <img :src="tutorial.cover_url" alt="教程封面" class="cover-img">
                    </div>
                    <div class="tutorial-desc">{{ tutorial.desc }}</div>
                    <div class="tutorial-meta">文件大小：{{ tutorial.size_mb }}MB</div>
                    <!-- 操作按钮 -->
                    <div class="tutorial-actions">
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="previewResource(tutorial)"
                        icon="el-icon-view"
                      >
                        {{ tutorial.video_url ? '预览视频' : '查看文档' }}
                      </el-button>
                      <el-button 
                        size="small" 
                        @click="downloadResource(tutorial.file_url)"
                        icon="el-icon-download"
                      >
                        下载
                      </el-button>
                    </div>
                  </el-card>
                </el-col>
              </el-row>

              <!-- 无数据提示 -->
              <el-empty v-if="tutorialsList.length === 0 && !loadingMap.standard_tutorials" description="暂无技术动作标准教程"></el-empty>
              <div v-if="loadingMap.standard_tutorials" class="loading-container">
                <el-loading text="加载资源中..."></el-loading>
              </div>
            </div>
          </el-tab-pane>

          <!-- 3. 往届大赛视频/案例 -->
          <el-tab-pane label="往届案例" name="past_cases">
            <div class="cases-container">
              <!-- 视频案例列表 -->
              <el-row :gutter="20" class="cases-grid">
                <el-col :span="isMobile ? 24 : 12" v-for="(caseItem, idx) in casesList" :key="caseItem.id">
                  <el-card shadow="hover" class="case-card">
                    <template #header>
                      <span class="case-title">{{ caseItem.title }}</span>
                    </template>
                    <!-- 视频预览（修复poster中文冒号） -->
                    <div class="case-video">
                      <video 
                        v-if="caseItem.video_url"
                        :src="caseItem.video_url" 
                        controls 
                        class="video-player"
                        :poster="caseItem.cover_url"
                      >
                        您的浏览器不支持视频播放
                      </video>
                      <img 
                        v-else
                        :src="caseItem.cover_url" 
                        alt="案例封面" 
                        class="case-cover-img"
                      >
                    </div>
                    <div class="case-info">
                      <span class="case-year">{{ caseItem.year }}届 · {{ caseItem.category }}</span>
                      <span class="case-desc">{{ caseItem.desc }}</span>
                      <span class="case-meta">文件大小：{{ caseItem.size_mb }}MB</span>
                    </div>
                    <el-button 
                      size="small" 
                      @click="downloadResource(caseItem.file_url)"
                      icon="el-icon-download"
                      style="margin-top: 10px;"
                    >
                      下载案例
                    </el-button>
                  </el-card>
                </el-col>
              </el-row>

              <!-- 无数据提示 -->
              <el-empty v-if="casesList.length === 0 && !loadingMap.past_cases" description="暂无往届大赛视频/案例"></el-empty>
              <div v-if="loadingMap.past_cases" class="loading-container">
                <el-loading text="加载资源中..."></el-loading>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 资源预览弹窗 -->
    <el-dialog 
      v-model="previewDialogVisible" 
      :title="currentResource.title || '资源预览'" 
      width="80%"
      append-to-body
      @close="handlePreviewDialogClose" <!-- 关闭弹窗清空数据 -->
    >
      <div class="preview-content">
        <!-- 图片预览 -->
        <img v-if="previewType === 'image'" :src="currentResource.cover_url" alt="资源预览" class="preview-img">
        <!-- 视频预览 -->
        <video v-if="previewType === 'video'" :src="currentResource.video_url" controls class="preview-video">
          您的浏览器不支持视频播放
        </video>
        <!-- 文档预览占位（可集成pdf.js扩展） -->
        <div v-if="previewType === 'doc'" class="preview-doc-placeholder">
          <i class="el-icon-file-text"></i>
          <p>文档预览需集成pdf.js插件，点击下方下载按钮查看完整文档</p>
          <el-button 
            type="primary" 
            @click="downloadResource(currentResource.file_url)"
            icon="el-icon-download"
            style="margin-top: 10px;"
          >
            下载文档
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onMounted as onMountedOriginal, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import HeaderNav from '@/components/HeaderNav.vue'

// ========== 基础配置 ==========
// 激活的标签页
const activeTab = ref('official_docs')
// 拆分各类型加载状态（解决全局loading冲突）
const loadingMap = ref({
  official_docs: false,
  standard_tutorials: false,
  past_cases: false
})
// 预览弹窗相关
const previewDialogVisible = ref(false)
const currentResource = ref({})
const previewType = ref('')

// 资源列表数据
const officialDocsList = ref([])
const tutorialsList = ref([])
const casesList = ref([])

// 响应式判断是否为移动端
const isMobile = computed(() => {
  return window.innerWidth <= 768
})

// ========== 逻辑方法 ==========
// 初始化：仅监听标签页，不主动加载所有资源（懒加载）
onMountedOriginal(() => {
  // 初始标签页自动加载
  loadResourceByType(activeTab.value)
})

// 监听标签页切换，按需加载资源（增加防重复请求）
watch(activeTab, (newTab) => {
  if (
    (newTab === 'official_docs' && officialDocsList.value.length === 0 && !loadingMap.value.official_docs) ||
    (newTab === 'standard_tutorials' && tutorialsList.value.length === 0 && !loadingMap.value.standard_tutorials) ||
    (newTab === 'past_cases' && casesList.value.length === 0 && !loadingMap.value.past_cases)
  ) {
    loadResourceByType(newTab)
  }
})

// 按类型加载资源（优化加载状态、错误处理）
const loadResourceByType = async (resourceType) => {
  // 标记当前类型加载中
  loadingMap.value[resourceType] = true
  try {
    // 建议配置axios baseURL，避免跨域/路径错误
    // axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const res = await axios.get(`/api/static/list?resource_type=${resourceType}`)
    if (res.data.code === 200) {
      const resourceList = res.data.resource_list
      switch (resourceType) {
        case 'official_docs':
          officialDocsList.value = resourceList
          break
        case 'standard_tutorials':
          tutorialsList.value = resourceList
          break
        case 'past_cases':
          casesList.value = resourceList
          break
      }
    } else {
      ElMessage.error(`加载${getResourceTypeName(resourceType)}失败：${res.data.msg || '接口返回异常'}`)
    }
  } catch (err) {
    ElMessage.error(`加载${getResourceTypeName(resourceType)}失败：${err.message || '网络错误'}`)
    console.error(`[${getResourceTypeName(resourceType)}加载失败]`, err)
  } finally {
    // 结束当前类型加载状态
    loadingMap.value[resourceType] = false
  }
}

// 下载资源（增强健壮性）
const downloadResource = (fileUrl) => {
  if (!fileUrl || fileUrl.trim() === '') {
    ElMessage.warning('暂无有效下载链接')
    return
  }
  // 处理相对路径/绝对路径
  const fullUrl = fileUrl.startsWith('http') ? fileUrl : `${import.meta.env.VITE_API_BASE_URL || ''}${fileUrl}`
  window.open(`/api/static/download?file_url=${encodeURIComponent(fullUrl)}`, '_blank')
}

// 预览资源（优化图片类型判断）
const previewResource = (resource) => {
  currentResource.value = resource
  if (resource.video_url) {
    previewType.value = 'video'
  } else if (resource.cover_url) {
    // 支持更多图片格式
    const imgExts = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
    const ext = resource.cover_url.toLowerCase().substring(resource.cover_url.lastIndexOf('.'))
    previewType.value = imgExts.includes(ext) ? 'image' : 'doc'
  } else {
    previewType.value = 'doc'
  }
  previewDialogVisible.value = true
}

// 关闭预览弹窗：清空数据，避免残留
const handlePreviewDialogClose = () => {
  currentResource.value = {}
  previewType.value = ''
  previewDialogVisible.value = false
}

// 辅助函数：获取资源类型名称
const getResourceTypeName = (resourceType) => {
  const typeMap = {
    'official_docs': '官方文档',
    'standard_tutorials': '标准教程',
    'past_cases': '往届案例'
  }
  return typeMap[resourceType] || '资源'
}
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

/* 标签页样式 */
.resource-tabs {
  --el-tabs-header-text-color: #475569;
  --el-tabs-active-color: #3b82f6;
  margin-bottom: 20px;
}

/* 资源列表通用样式 */
.resource-list-container {
  margin-top: 15px;
}
/* 样式穿透：修改Element Plus内置变量 */
:deep(.resource-list) {
  --el-list-item-height: 100px;
}
.resource-icon {
  font-size: 24px;
  color: #3b82f6;
}
.resource-title {
  font-size: 16px;
  font-weight: 500;
  color: #1e293b;
}
.resource-desc {
  font-size: 14px;
  color: #64748b;
  margin-top: 5px;
}
.resource-meta {
  font-size: 12px;
  color: #94a3b8;
}

/* 加载容器样式（非全屏） */
.loading-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 标准教程样式 */
.tutorial-container {
  margin-top: 15px;
}
.tutorial-grid {
  margin-top: 10px;
}
.tutorial-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.tutorial-title {
  font-size: 16px;
  font-weight: 500;
}
.tutorial-img {
  margin: 10px 0;
  text-align: center;
  flex: 1;
}
.cover-img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 8px;
}
.tutorial-desc {
  font-size: 14px;
  color: #64748b;
  margin: 10px 0;
  line-height: 1.5;
}
.tutorial-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 10px;
}
.tutorial-actions {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 10px;
}

/* 往届案例样式 */
.cases-container {
  margin-top: 15px;
}
.cases-grid {
  margin-top: 10px;
}
.case-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.case-title {
  font-size: 16px;
  font-weight: 500;
}
.case-video {
  margin: 10px 0;
}
.video-player {
  width: 100%;
  height: 240px;
  border-radius: 8px;
}
.case-cover-img {
  width: 100%;
  height: 240px;
  object-fit: cover;
  border-radius: 8px;
}
.case-info {
  margin: 10px 0;
  font-size: 14px;
  color: #64748b;
}
.case-year {
  display: block;
  margin-bottom: 5px;
  color: #3b82f6;
  font-weight: 500;
}
.case-meta {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #94a3b8;
}

/* 预览弹窗样式 */
.preview-content {
  text-align: center;
  padding: 10px;
}
.preview-img {
  max-width: 100%;
  max-height: 600px;
  border-radius: 8px;
}
.preview-video {
  width: 100%;
  height: 500px;
  border-radius: 8px;
}
.preview-doc-placeholder {
  padding: 40px 0;
  color: #64748b;
  font-size: 16px;
}
.preview-doc-placeholder i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #94a3b8;
}

/* 响应式适配（优化） */
@media (max-width: 768px) {
  .resource-card {
    padding: 20px;
  }
  .video-player, .case-cover-img {
    height: 180px;
  }
}
</style>