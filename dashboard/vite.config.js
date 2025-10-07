import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/live': 'http://api:8000',
      '/health': 'http://api:8000',
      '/search': 'http://api:8000',
      '/most_active': 'http://api:8000',
      '/categories': 'http://api:8000',
      '/channels': 'http://api:8000',
      '/export': 'http://api:8000',
    },
  },
});
