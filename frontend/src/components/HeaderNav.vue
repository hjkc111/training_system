<template>
  <div class="header-nav">
    <div class="nav-content">
      <div class="logo">
        <i class="el-icon-video-camera"></i>
        <span>世界技能大赛 - 训练管理系统</span>
      </div>
      <div class="nav-menu">
        <el-menu
          :default-active="activeIndex"
          mode="horizontal"
          background-color="#1e40af"
          text-color="#fff"
          active-text-color="#ffd04b"
          class="nav-menu-inner"
        >
          <el-menu-item index="1" @click="toPage('/home')">
            <i class="el-icon-house"></i>
            <span>首页</span>
          </el-menu-item>

          <!-- 核心修复：Element Plus 2.x 用 el-sub-menu（带短横线） -->
          <el-sub-menu index="7" popper-class="training-submenu">
            <template #title>
              <i class="el-icon-date"></i>
              <span>训练管理</span>
            </template>
            <el-menu-item index="7-1" @click="toPage('/training/day-list')">
              <span>网络布线项目</span>
            </el-menu-item>
            <el-menu-item index="7-2" @click="toPage('/training/photoelectric')">
              <span>光电项目</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="2" @click="toPage('/profile')">
            <i class="el-icon-user"></i>
            <span>个人中心</span>
          </el-menu-item>
          <el-menu-item index="3" @click="toPage('/data-analysis')">
            <i class="el-icon-s-data"></i>
            <span>数据分析</span>
          </el-menu-item>
          <el-menu-item index="4" @click="toPage('/training-plan')">
            <i class="el-icon-s-check"></i>
            <span>训练计划</span>
          </el-menu-item>
          <el-menu-item index="5" @click="toPage('/resource-view')">
            <i class="el-icon-document"></i>
            <span>资源查阅</span>
          </el-menu-item>
          <el-menu-item index="6" @click="toPage('/about')">
            <i class="el-icon-info"></i>
            <span>关于我们</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="user-info" v-if="userInfo.username">
        <el-tag type="info" effect="dark">
          <i class="el-icon-user"></i> {{ userInfo.username }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

// 初始化变量
const router = useRouter()
const route = useRoute()
const userInfo = ref({ username: '' })
const activeIndex = ref('1')

// 路由-菜单索引映射
const pathToIndexMap = {
  '/home': '1',
  '/training/day-list': '7',
  '/training/day-detail': '7',
  '/training/photoelectric': '7', // 光电项目路由映射
  '/profile': '2',
  '/data-analysis': '3',
  '/training-plan': '4',
  '/resource-view': '5',
  '/about': '6'
}

// 初始化逻辑
onMounted(() => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (userInfoStr) {
      userInfo.value = JSON.parse(userInfoStr)
    }
  } catch (error) {
    ElMessage.warning('用户信息异常，请重新登录')
  }
  updateActiveIndex(route.path)
})

// 监听路由变化
watch(
  () => route.path,
  (newPath) => {
    updateActiveIndex(newPath)
  },
  { immediate: true }
)

// 更新激活索引
function updateActiveIndex(path) {
  activeIndex.value = pathToIndexMap[path] || '1'
}

// 路由跳转
function toPage(path) {
  router.push(path)
}
</script>

<style scoped>
.header-nav {
  background: #1e40af;
  color: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  padding: 10px 0;
}
.logo i {
  font-size: 24px;
}
.nav-menu {
  flex: 1;
  margin: 0 20px;
}
:deep(.nav-menu-inner) {
  border: none;
  height: 60px;
  line-height: 60px;
  justify-content: center;
}
:deep(.el-menu-item) {
  font-size: 14px;
  padding: 0 20px !important;
}
.user-info {
  font-size: 14px;
  padding: 10px 0;
}

/* 适配Element Plus 2.x 水平菜单子菜单样式 */
:deep(.training-submenu) {
  background-color: #1e40af !important;
  border: none !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
:deep(.training-submenu .el-menu-item) {
  height: 45px !important;
  line-height: 45px !important;
  padding-left: 30px !important;
  color: #fff !important;
}
:deep(.training-submenu .el-menu-item:hover) {
  background-color: #19369e !important;
}
:deep(.el-sub-menu__title) {
  height: 60px !important;
  line-height: 60px !important;
  padding: 0 20px !important;
  color: #fff !important;
}
</style>