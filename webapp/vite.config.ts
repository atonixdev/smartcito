/**
 * ============================================================================
 * File: webapp/vite.config.ts
 * Purpose:
 *   Vite build configuration. We:
 *     - Enable the React Fast Refresh plugin.
 *     - Expose `@` as an alias for `src/` (matches tsconfig paths).
 *     - Proxy `/api` to the FastAPI citosmart in dev so the webapp never
 *       sees CORS during local development.
 *     - Configure Vitest with jsdom for component tests.
 * ============================================================================
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api/location": {
        target: "http://localhost:4010",
        changeOrigin: true,
      },
      "/api/v1": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/api/gps": {
        target: "http://localhost:8020",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/gps/, ""),
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
