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
      '@': path.resolve(__dirname, './'),
      '@components': path.resolve(__dirname, './components'),
      '@pages': path.resolve(__dirname, './pages'),
      '@stores': path.resolve(__dirname, './stores'),
      '@utils': path.resolve(__dirname, './utils'),
      '@services': path.resolve(__dirname, './services'),
      '@data': path.resolve(__dirname, './data'),
      '@static': path.resolve(__dirname, './static'),
      '@styles': path.resolve(__dirname, './styles')
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
