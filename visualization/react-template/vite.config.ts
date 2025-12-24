import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // 使用相对路径，方便部署
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'charts-vendor': ['lightweight-charts'],
        },
      },
    },
  },
  server: {
    port: 5173,
    open: false, // 由 test_strategy.py 控制浏览器打开，避免重复打开
  },
})
