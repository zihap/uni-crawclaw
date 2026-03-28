import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    uni()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@services': path.resolve(__dirname, './src/services'),
      '@data': path.resolve(__dirname, './src/data'),
      '@static': path.resolve(__dirname, './src/static'),
      '@styles': path.resolve(__dirname, './src/styles')
    }
  },
  build: {
    // 构建配置
    target: 'es6',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  server: {
    // 开发服务器配置
    port: 3000,
    open: true,
    cors: true
  }
})
