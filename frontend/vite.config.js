// vite.config.js（Vite项目）
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  // 核心：配置代理转发/api请求到后端8000端口
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 后端服务地址
        changeOrigin: true, // 允许跨域
        rewrite: (path) => path.replace(/^\/api/, '/api') // 保留/api前缀
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})