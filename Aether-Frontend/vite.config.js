import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Cesium needs to resolve 'cesium' from node_modules. On Vite this works
  // out of the box, but if you encounter asset-loading issues you can add:
  // resolve: { alias: { 'cesium': 'cesium/Cesium.js' } }
  optimizeDeps: {
    exclude: ['cesium'],
  },
});
