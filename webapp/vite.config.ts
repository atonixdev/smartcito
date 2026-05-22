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
import type { IncomingMessage, ServerResponse } from "node:http";

export default defineConfig({
  envPrefix: ["VITE_"],
  base: process.env.GITHUB_PAGES === "true" ? "/smartcito/" : "/",
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

const backendEnabled = process.env.VITE_ENABLE_BACKEND === "true";

const demoDashboardLogsPayload = {
  generated_at: new Date().toISOString(),
  logs: [
    {
      id: "log-demo-001",
      timestamp: new Date().toISOString(),
      type: "operations",
      severity: "info",
      device_id: "PI-NBO-01",
      country: "KE",
      region: "NBO",
      area_code: "020",
      ip: "10.10.20.12",
      gps: { latitude: -1.2921, longitude: 36.8219 },
      message: "Offline dashboard log feed active",
      incident_id: null,
    },
  ],
  threats: [],
};

function writeJson(res: ServerResponse, payload: unknown) {
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(payload));
}

function offlineDashboardLogsPlugin() {
  return {
    name: "smartcito-offline-dashboard-logs",
    configureServer(server: { middlewares: { use: (handler: (req: IncomingMessage, res: ServerResponse, next: () => void) => void) => void } }) {
      server.middlewares.use((req, res, next) => {
        const pathname = req.url?.split("?")[0];
        if (!backendEnabled && pathname === "/api/location/dashboard/logs") {
          writeJson(res, {
            ...demoDashboardLogsPayload,
            generated_at: new Date().toISOString(),
          });
          return;
        }

        next();
      });
    },
  };
}

export default defineConfig({
  envPrefix: ["VITE_"],
  base: process.env.GITHUB_PAGES === "true" ? "/smartcito/" : "/",
  plugins: [react(), offlineDashboardLogsPlugin()],
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
