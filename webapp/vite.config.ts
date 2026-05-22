/**
 * ============================================================================
 * File: webapp/vite.config.ts
 * Purpose:
 *   Vite build configuration for React, aliases, dev proxying, offline
 *   dashboard-log fallback, and Vitest.
 * ============================================================================
 */

import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import type { IncomingMessage, ServerResponse } from "node:http";

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

const demoDevicesPayload = {
  status: "success",
  timestamp: new Date().toISOString(),
  request_id: "vite-offline-devices",
  data: {
    devices: [
      {
        id: "cam-001",
        type: "camera",
        status: "online",
        location: { lat: -26.2041, lng: 28.0473 },
        trust_score: 96,
      },
      {
        id: "gps-001",
        type: "gps",
        status: "online",
        location: { lat: -26.205, lng: 28.048 },
        trust_score: 92,
      },
    ],
  },
  meta: { version: "v1", source: "smartcito-vite-offline" },
};

const demoEventsPayload = {
  status: "success",
  timestamp: new Date().toISOString(),
  request_id: "vite-offline-events",
  data: { events: [] },
  meta: { version: "v1", source: "smartcito-vite-offline" },
};

function writeJson(res: ServerResponse, payload: unknown) {
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(payload));
}

function offlineDashboardLogsPlugin(): Plugin {
  return {
    name: "smartcito-offline-dashboard-logs",
    configureServer(server) {
      server.middlewares.use((req: IncomingMessage, res: ServerResponse, next) => {
        const pathname = req.url?.split("?")[0];

        if (!backendEnabled && pathname === "/api/location/dashboard/logs") {
          writeJson(res, {
            ...demoDashboardLogsPayload,
            generated_at: new Date().toISOString(),
          });
          return;
        }

        if (!backendEnabled && pathname === "/api/v1/devices") {
          writeJson(res, {
            ...demoDevicesPayload,
            timestamp: new Date().toISOString(),
          });
          return;
        }

        if (!backendEnabled && pathname === "/api/v1/events") {
          writeJson(res, {
            ...demoEventsPayload,
            timestamp: new Date().toISOString(),
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
