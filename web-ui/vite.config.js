import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://proxy-api:8080',
        changeOrigin: true
      },
      '/proxy': {
        target: process.env.VITE_API_PROXY || 'http://proxy-api:8080',
        changeOrigin: true
      },
      '/health': {
        target: process.env.VITE_API_PROXY || 'http://proxy-api:8080',
        changeOrigin: true
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`
      }
    }
  }
})
