import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Requests to /api/* are forwarded to the Python backend, so the UI needs no config.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.BACKEND_URL || 'http://localhost:8000',
    },
  },
})
