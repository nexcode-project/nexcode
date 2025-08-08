import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5433,
    host: '0.0.0.0'
  },
  preview: {
    port: 5433,
    host: '0.0.0.0'
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://localhost:8000')
  }
})
