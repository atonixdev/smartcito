/**
 * ============================================================================
 * File: webapp/vite.config.ts
 * Purpose:
 *   Vite build configuration. We:
 *     - Enable the React Fast Refresh plugin.
 *     - Expose `@` as an alias for `src/` (matches tsconfig paths).
 *     - Proxy `/api` to the FastAPI orcaapi in dev so the webapp never
 *       sees CORS during local development.
 *     - Configure Vitest with jsdom for component tests.
 * ============================================================================
 */

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";
import path from "node:path";

const githubRepository = process.env.GITHUB_REPOSITORY ?? "";
const githubRepoName = githubRepository.split("/")[1] ?? "";
const githubPagesBase =
  githubRepoName && !githubRepoName.toLowerCase().endsWith(".github.io")
    ? `/${githubRepoName}/`
    : "/";

export default defineConfig({
  base: process.env.GITHUB_PAGES === "true" ? githubPagesBase : "/",
  plugins: [react(), cesium()],
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
        ws: true,
      },
      "/drone-gateway": {
        target: "http://localhost:8020",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/drone-gateway/, ""),
      },
      "/robot-gateway": {
        target: "http://localhost:8026",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/robot-gateway/, ""),
      },
      "/mission-control": {
        target: "http://localhost:8025",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/mission-control/, ""),
      },
      "/mapping-geospatial": {
        target: "http://localhost:8024",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/mapping-geospatial/, ""),
      },
      "/drone-camera": {
        target: "http://localhost:8022",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/drone-camera/, ""),
      },
      "/threat-detection": {
        target: "http://localhost:8023",
        changeOrigin: true,
        rewrite: (requestPath) => requestPath.replace(/^\/threat-detection/, ""),
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
