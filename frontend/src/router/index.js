import { createRouter, createWebHistory } from 'vue-router'
// 引入页面组件
import Login from '../views/Login.vue'
import VideoUpload from '../views/VideoUpload.vue'
import Home from '../views/Home.vue'
import Profile from '../views/Profile.vue'
import TrainingPlan from '../views/TrainingPlan.vue'
import ResourceView from '../views/ResourceView.vue'
import About from '../views/About.vue'
// 新增训练日页面（网络布线）
import TrainingDayList from '../views/TrainingDayList.vue'
import TrainingDayDetail from '../views/TrainingDayDetail.vue'
// 导入光电项目组件（关键修改1：新增这两个导入）
import PhotoelectricDayList from '../views/PhotoelectricDayList.vue'
import PhotoelectricDayDetail from '../views/PhotoelectricDayDetail.vue'
// 光电项目空页面（保留，若不需要可删除）
import Photoelectric from '@/views/Photoelectric.vue' 

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 默认跳转到首页
    { path: '/', redirect: '/home' },
    // 登录页
    { path: '/login', component: Login },
    // 首页
    { path: '/home', component: Home },
    // 个人中心
    { path: '/profile', component: Profile },
    // 原单视频分析（数据分析页）
    { path: '/data-analysis', component: VideoUpload },
    // 训练计划
    { path: '/training-plan', component: TrainingPlan },
    // 资源查阅
    { path: '/resource-view', component: ResourceView },
    // 关于我们
    { path: '/about', component: About },
    // 新增：网络布线训练日列表
    { path: '/network/training/day/list', component: TrainingDayList },
    // 新增：网络布线训练日详情
    { path: '/network/training/day/detail/:id', component: TrainingDayDetail },
    // 关键修改2：新增光电项目训练日列表路由
    { path: '/photoelectric/training/day/list', component: PhotoelectricDayList },
    // 关键修改3：新增光电项目训练日详情路由（带动态id参数）
    { path: '/photoelectric/training/day/detail/:id', component: PhotoelectricDayDetail },
    // 光电项目空页面（保留，若不需要可删除）
    { path: '/photoelectric/training',name: 'Photoelectric',component: Photoelectric }
  ]
})

// 全局路由守卫：验证登录状态
router.beforeEach((to, from, next) => {
  const whiteList = ['/login']
  if (whiteList.includes(to.path)) {
    next()
    return
  }

  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    try {
      const userInfo = JSON.parse(userInfoStr)
      if (userInfo?.username) {
        next()
        return
      }
    } catch (e) {
      localStorage.removeItem('userInfo')
    }
  }

  next('/login')
})

export default router