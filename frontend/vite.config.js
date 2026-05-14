import { fileURLToPath, URL } from 'node:url'
import fs from 'fs'
import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// config.json is used by local developers and SHOULD NOT be pushed to GitHub.
// In CI/Docker builds it is absent; VITE_BACKEND_URL and VITE_BACKEND_PORT env vars are used instead.
let backendUrl, backendPort
try {
  const config = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, 'src/config.json'), 'utf-8'),
  )
  backendUrl = config.backendUrl
  backendPort = config.backendPort
} catch (_) {
  backendUrl = process.env.VITE_BACKEND_URL || ''
  backendPort = process.env.VITE_BACKEND_PORT || ''
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  define: {
    'import.meta.env.VITE_BACKEND_URL': JSON.stringify(backendUrl),
    'import.meta.env.VITE_BACKEND_PORT': JSON.stringify(backendPort),
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['fulcrum.unr.dev'],
    ...(backendUrl && backendPort
      ? {
          proxy: {
            '/api': {
              target: `${backendUrl}:${backendPort}`,
              changeOrigin: true,
              secure: false,
            },
          },
        }
      : {}),
  },
})
