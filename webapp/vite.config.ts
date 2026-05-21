/**
 * ============================================================================
 * File: frontend/vite.config.ts
 * Purpose:
 *   Vite build configuration. We:
 *     - Enable the React Fast Refresh plugin.
 *     - Expose `@` as an alias for `src/` (matches tsconfig paths).
 *     - Proxy `/api` to the FastAPI backend in dev so the frontend never
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
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
