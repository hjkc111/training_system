import { createRouter, createWebHistory } from 'vue-router'
// 引入页面组件（保留你原有路径，无需修改）
import Login from '../views/Login.vue'
import VideoUpload from '../views/VideoUpload.vue'

const router = createRouter({
  history: createWebHistory(),  // 路由模式（保留你原有配置，不用改）
  routes: [
    // 默认跳转到登录页（保留）
    { path: '/', redirect: '/login' },
    // 登录页（保留）
    { path: '/login', component: Login },
    // 视频上传页（保留你原有路径 /video/upload，仅新增可选的登录守卫）
    { 
      path: '/video/upload', 
      component: VideoUpload,
      // 修复：容错处理 localStorage.getItem('userInfo') 为 null 的情况
      beforeEnter: (to, from, next) => {
        const userInfoStr = localStorage.getItem('userInfo')
        // 只有存在 userInfo 且解析后有 username 才允许访问
        if (userInfoStr) {
          const userInfo = JSON.parse(userInfoStr)
          if (userInfo?.username) {
            next() // 已登录，允许访问
            return
          }
        }
        next('/login') // 未登录/无用户名，强制跳回登录页
      }
    }
  ]
})

export default router