import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// The backend (apps/api) listens on 8200; MJPEG streams and SSE go through the same /api proxy.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8200', changeOrigin: true } },
  },
  resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
})
