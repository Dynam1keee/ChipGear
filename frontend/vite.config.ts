import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Django runs on this address during development (python manage.py runserver)
const DJANGO = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    // The browser talks only to Vite (localhost:5173). Vite forwards /api and
    // /media to Django, so there are no CORS problems, the same as on the server with Nginx.
    proxy: {
      '/api': { target: DJANGO, changeOrigin: true },
      '/media': { target: DJANGO, changeOrigin: true },
    },
  },
})
