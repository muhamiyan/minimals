import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import Icons from 'unplugin-icons/vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BACKEND_ORIGIN = process.env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000'

export default defineConfig(({ command }) => ({
  plugins: [
    frappeui({
      frappeProxy: false,
      lucideIcons: true,
      buildOutput: path.resolve(__dirname, '../app/static/frontend'),
    }),
    vue(),
    Icons({ autoInstall: true }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: BACKEND_ORIGIN, changeOrigin: false, secure: false },
      '/uploads': { target: BACKEND_ORIGIN, changeOrigin: false },
    },
  },
  base: command === 'build' ? '/static/frontend/' : '/',
  build: {
    outDir: '../app/static/frontend',
    emptyOutDir: true,
    assetsDir: 'assets',
    sourcemap: false,
    target: 'es2015',
    chunkSizeWarningLimit: 500,
    esbuild: {
      drop: [],
    },
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons'],
    exclude: ['frappe-ui'],
  },
}))
