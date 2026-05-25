/**
 * ============================================================================
 * File: webapp/src/App.tsx
 * Purpose:
 *   Top-level component. Owns the route table and the persistent shell
 *   (header, navigation). Keep this file small — routes pull in their own
 *   page components from `src/pages`.
 * ============================================================================
 */

import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import Home from "./pages/Home";
import Architecture from "./pages/Architecture";
import Community from "./pages/Community";
import Dashboard from "./pages/Dashboard";
import Mission from "./pages/Mission";
import NotFound from "./pages/NotFound";
import Roadmap from "./pages/Roadmap";
import Visualization from "./pages/Visualization";

export default function App() {
  const location = useLocation();
  const isCommandCenterRoute = location.pathname === "/dashboard";

  return (
    <div className={isCommandCenterRoute ? "app-shell app-shell-dashboard" : "app-shell"}>
      {!isCommandCenterRoute ? (
        <header className="app-header">
          <h1 className="app-title">SmartCito</h1>
          <nav className="app-nav">
            <Link to="/home">Home</Link>
            <Link to="/mission">Mission</Link>
            <Link to="/architecture">Architecture</Link>
            <Link to="/community">Community</Link>
            <Link to="/roadmap">Roadmap</Link>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/visualization">Visualization</Link>
          </nav>
        </header>
      ) : null}

      <main className={isCommandCenterRoute ? "app-main app-main-dashboard" : "app-main"}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/home" element={<Home />} />
          <Route path="/mission" element={<Mission />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/community" element={<Community />} />
          <Route path="/roadmap" element={<Roadmap />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/visualization" element={<Visualization />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      {!isCommandCenterRoute ? (
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
      ) : null}
    </div>
  );
}
