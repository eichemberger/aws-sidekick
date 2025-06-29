import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue({
      // Enable reactive transform for better performance
      reactivityTransform: true
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // Performance optimizations
    target: 'esnext',
    minify: 'esbuild',
    cssMinify: true,
    // Enable chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          vue: ['vue', 'vue-router'],
          ui: ['@headlessui/vue'],
          markdown: ['markdown-it', 'highlight.js'],
          utils: ['date-fns']
        }
      }
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 1000
  },
  // Optimize deps
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'markdown-it',
      'highlight.js',
      'date-fns'
    ],
    exclude: ['@vueuse/core']
  }
}) 