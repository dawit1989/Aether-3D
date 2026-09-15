import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isServe = mode === 'development';
  const isPreview = mode === 'preview';
  const defineDev = isServe || isPreview;

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@hooks': path.resolve(__dirname, 'src/hooks'),
        '@utils': path.resolve(__dirname, 'src/utils'),
      },
    },
    server: {
      // Allow connections from any host in containerised environments.
      host: true,
      port: 5173,
      fs: {
        // Allow serving files from the parent Aether-3D directory so
        // users can load generated .czml files directly.
        allow: [
          __dirname,
          path.resolve(__dirname, '..'),
        ],
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            cesium: ['cesium'],
            react: ['react', 'react-dom'],
          },
        },
      },
    },
    // Cesium requires these defines to resolve assets correctly.
    define: {
      CESIUM_BASE_URL: defineDev
        ? JSON.stringify('/')
        : JSON.stringify('/'),
    },
    optimizeDeps: {
      exclude: ['cesium'],
    },
  };
});
