import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cesiumBuildPath = 'node_modules/cesium/Build/Cesium';

// https://vitejs.dev/config/
export default defineConfig(() => {
  return {
    plugins: [
      react(),
      viteStaticCopy({
        targets: [
          { src: `${cesiumBuildPath}/Workers/**/*`, dest: 'Workers' },
          { src: `${cesiumBuildPath}/Assets/**/*`, dest: 'Assets' },
          { src: `${cesiumBuildPath}/Widgets/**/*`, dest: 'Widgets' },
          { src: `${cesiumBuildPath}/ThirdParty/**/*`, dest: 'ThirdParty' },
        ],
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@hooks': path.resolve(__dirname, 'src/hooks'),
        '@utils': path.resolve(__dirname, 'src/utils'),
      },
    },
    server: {
      host: true,
      port: 5173,
      fs: {
        allow: [
          __dirname,
          path.resolve(__dirname, '..'),
        ],
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      chunkSizeWarningLimit: 5000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/cesium')) return 'cesium';
            if (id.includes('node_modules/react-dom') || id.includes('node_modules/react/')) return 'react';
          },
        },
      },
    },
    define: {
      CESIUM_BASE_URL: JSON.stringify('/'),
    },
  };
});
