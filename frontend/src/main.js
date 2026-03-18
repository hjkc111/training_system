// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 确保路由已正确引入

// 1. 全局导入Element Plus和样式（必须完整）
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 2. 导入所有图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 3. 注册Element Plus（必须调用app.use）
app.use(ElementPlus)
// 4. 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 5. 挂载路由和应用
app.use(router).mount('#app')

// 验证：控制台打印，确认注册成功
console.log('Element Plus 全局注册成功')