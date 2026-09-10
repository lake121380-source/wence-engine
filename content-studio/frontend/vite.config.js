import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    hmr: false,
  },
  build: {
    // 框架与 UI 库单独成块：它们很少变，可被浏览器长期缓存，
    // 业务代码更新时不必让用户重下这几百 KB。
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-ui': ['naive-ui'],
        },
      },
    },
  },
})
