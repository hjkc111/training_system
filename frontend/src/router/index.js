import { createRouter, createWebHistory } from 'vue-router'
// 引入页面组件
import Login from '../views/Login.vue'
import VideoUpload from '../views/VideoUpload.vue'
import Home from '../views/Home.vue'
import Profile from '../views/Profile.vue'
import TrainingPlan from '../views/TrainingPlan.vue'
import ResourceView from '../views/ResourceView.vue'
import About from '../views/About.vue'
// 新增训练日页面
import TrainingDayList from '../views/TrainingDayList.vue'
import TrainingDayDetail from '../views/TrainingDayDetail.vue'

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
    // 新增：训练日列表
    { path: '/training/day-list', component: TrainingDayList },
    // 新增：训练日详情
    { path: '/training/day-detail/:id', component: TrainingDayDetail }
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