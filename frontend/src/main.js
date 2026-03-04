// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 1. 完整导入Element Plus（新手推荐，避免按需导入漏组件）
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 2. 导入所有图标（确保el-icon-upload等图标正常）
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 3. 全局注册Element Plus（关键！）
app.use(ElementPlus)
// 4. 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)
app.mount('#app')