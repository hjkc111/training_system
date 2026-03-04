import axios from 'axios'

// 创建axios实例，统一配置
const request = axios.create({
  baseURL: '/api',  // 对应Vite的跨域代理，实际指向后端http://127.0.0.1:8000
  timeout: 10000    // 请求超时时间
})

// 请求拦截器：携带登录令牌（新手先注释，登录功能跑通后再开）
// request.interceptors.request.use(
//   (config) => {
//     // 从本地存储获取token，添加到请求头
//     const token = localStorage.getItem('token')
//     if (token) {
//       config.headers.Authorization = `Bearer ${token}`
//     }
//     return config
//   },
//   (error) => Promise.reject(error)
// )

// 响应拦截器：统一处理返回结果
request.interceptors.response.use(
  (response) => {
    // 只返回后端的data数据，简化使用
    return response.data
  },
  (error) => {
    // 错误提示（用Element Plus的ElMessage）
    import('element-plus').then(({ ElMessage }) => {
      ElMessage.error(error.message || '请求失败')
    })
    return Promise.reject(error)
  }
)

export default request