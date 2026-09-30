import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig(({ mode }) => {
  // The cloud server (dashboard nginx, infra/compose/cloud) routes /api, /api/v1/ws and /api/v1/chat itself.
  // No VITE_ prefix: read by the dev server only, never bundled.
  const cloud = loadEnv(mode, process.cwd(), '').CLOUD_URL

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true, // bind 0.0.0.0 so other machines on the LAN can reach the dev server
      proxy: {
        '/api': { target: cloud, changeOrigin: true, ws: true },
      },
    },
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, './src'),
      },
    },
  }
})
