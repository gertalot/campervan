import { defineConfig } from 'vitest/config';

declare const process: { readonly env: Record<string, string | undefined> };

// Settings come only from the invoking process; never load dotenv files.
export default defineConfig({
  envDir: false,
  server: {
    host: process.env.CAMPERVAN_UI_HOST ?? '127.0.0.1',
    port: Number(process.env.CAMPERVAN_UI_PORT ?? '5173'),
    strictPort: true,
    proxy: {
      '/api': { target: process.env.CAMPERVAN_API_TARGET ?? 'http://127.0.0.1:8000' },
      '/viewer-assets': { target: process.env.CAMPERVAN_API_TARGET ?? 'http://127.0.0.1:8000' },
    },
  },
  build: {
    outDir: '../src/campervan/web',
    emptyOutDir: true,
    assetsDir: 'assets',
  },
  test: { environment: 'node' },
});
