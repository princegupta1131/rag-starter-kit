import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api/* is forwarded to the backend, so the UI needs no config of its own.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.BACKEND_URL || 'http://localhost:8000',
    },
  },
})
