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
      '/api': {
        target: DJANGO,
        changeOrigin: true,
        // Django checks that the Origin header of a POST matches the Host. The browser sends
        // Origin: http://localhost:5173, but Django sees Host 127.0.0.1:8000, so it answers 403.
        // We make the Origin equal to Django's address (only in development).
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            if (proxyReq.getHeader('origin')) proxyReq.setHeader('origin', DJANGO)
          })
        },
      },
      '/media': { target: DJANGO, changeOrigin: true },
    },
  },
})
