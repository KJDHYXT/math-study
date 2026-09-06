import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 对应文档 03 §4.5：开发时用 Vite proxy 把 /api 转发到后端。
// 跨设备访问时，前端可配置 VITE_API_BASE 指向后端地址（见 .env.example）。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 允许任何 Host（便于 Cloudflare Tunnel / ngrok 等公网域名访问）
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
