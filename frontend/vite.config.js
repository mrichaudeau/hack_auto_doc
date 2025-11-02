import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      fastRefresh: true, // Enable Fast Refresh for instant component updates
    })
  ],
  server: {
    host: '0.0.0.0',  // Allow external connections (required for Docker)
    port: 3000,
    strictPort: true,  // Fail if port already in use
    watch: {
      usePolling: false,  // Use native file watching (faster than polling)
      // Enable polling if HMR doesn't work on your system:
      // usePolling: true,
      // interval: 1000,
    },
    hmr: {
      protocol: 'ws',     // WebSocket protocol for HMR
      host: 'localhost',  // Host for HMR client connection
      port: 3000,         // Port for HMR
      clientPort: 3000,   // Port client should connect to
      overlay: true,      // Show error overlay in browser
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // Backend service URL (Docker network)
        changeOrigin: true,              // Rewrite Host header
        secure: false,                   // Allow self-signed certificates
        rewrite: (path) => path,         // Keep /api prefix
        configure: (proxy, options) => {
          // Log proxy requests for debugging
          proxy.on('error', (err, req, res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Proxying:', req.method, req.url);
          });
        },
      },
    },
  },
  build: {
    sourcemap: true,  // Enable source maps for debugging
    outDir: 'dist',
  },
  resolve: {
    alias: {
      '@': '/src',  // Allow import from '@/components/...'
    },
  },
})
