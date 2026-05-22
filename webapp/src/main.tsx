/**
 * ============================================================================
 * File: webapp/src/main.tsx
 * Purpose:
 *   React application entrypoint. Wraps the app in providers shared by
 *   every page: React Query, Router, and global styles.
 * ============================================================================
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import "./styles/global.css";

// React Query is the single source of truth for server state.
// `staleTime` of 30s reduces refetch chatter on dashboards.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: false },
  },
});

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Fatal: #root element not found in index.html");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
