import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0', // Explicit host for WSL compatibility
    strictPort: true, // Fail if port is already in use
    open: false, // Don't auto-open browser in WSL
    proxy: {
      '/oauth': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  preview: {
    port: 5173,
    host: '0.0.0.0'
  }
})