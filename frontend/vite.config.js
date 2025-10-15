import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Configure Vite to proxy API calls to the Flask backend during development.
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000'
    }
  }
});
