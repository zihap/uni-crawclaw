import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [uni()],
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

    // 👇👇 核心：禁用 CSS 最小化！彻底不生成 *
    build: {
        minify: false, // 关闭压缩
        cssMinify: false, // 关闭 CSS 压缩
    },

    server: {
        port: 3000,
        open: true,
        cors: true
    }
})