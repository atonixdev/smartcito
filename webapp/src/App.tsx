/**
 * ============================================================================
 * File: webapp/src/App.tsx
 * Purpose:
 *   Top-level component. Owns the route table and the persistent shell
 *   (header, navigation). Keep this file small — routes pull in their own
 *   page components from `src/pages`.
 * ============================================================================
 */

import { Route, Routes, useLocation } from "react-router-dom";

import AppHeader from "./components/AppHeader";
import Home from "./pages/Home";
import Architecture from "./pages/Architecture";
import Community from "./pages/Community";
import Dashboard from "./pages/Dashboard";
import Mission from "./pages/Mission";
import NotFound from "./pages/NotFound";
import Roadmap from "./pages/Roadmap";

const navigationItems = [
  { label: "HOME", to: "/" },
  { label: "MISSION", to: "/mission" },
  { label: "ARCHITECTURE", to: "/architecture" },
  { label: "COMMUNITY", to: "/community" },
  { label: "ROADMAP", to: "/roadmap" },
];

type ThemeMode = "dark" | "light";

const THEME_STORAGE_KEY = "smartcito.theme";

function getInitialTheme(): ThemeMode {
  if (typeof window === "undefined") return "dark";

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  return storedTheme === "light" || storedTheme === "dark" ? storedTheme : "dark";
}

export default function App() {
  const location = useLocation();
  const isDashboardRoute = location.pathname.startsWith("/dashboard");

  return (
    <div className={`app-shell ${isDashboardRoute ? "dashboard-shell-route" : ""}`}>
      {!isDashboardRoute && <AppHeader />}

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/home" element={<Home />} />
          <Route path="/mission" element={<Mission />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/community" element={<Community />} />
          <Route path="/roadmap" element={<Roadmap />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      {!isDashboardRoute && (
        <footer className="app-footer">
          <small>
            SmartCito · Urban Data Backbone · Apache 2.0 ·{" "}
            <a
              href="https://github.com/atonixdev/smartcito"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </small>
        </footer>
      )}
    </div>
  );
}
