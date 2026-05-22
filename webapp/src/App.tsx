/**
 * ============================================================================
 * File: webapp/src/App.tsx
 * Purpose:
 *   Top-level component. Owns the route table and the persistent shell
 *   (header, navigation). Keep this file small — routes pull in their own
 *   page components from `src/pages`.
 * ============================================================================
 */

import { Link, Route, Routes, useLocation } from "react-router-dom";

import Home from "./pages/Home";
import Architecture from "./pages/Architecture";
import Community from "./pages/Community";
import Dashboard from "./pages/Dashboard";
import Mission from "./pages/Mission";
import NotFound from "./pages/NotFound";
import Roadmap from "./pages/Roadmap";

export default function App() {
  const location = useLocation();
  const isDashboardRoute = location.pathname.startsWith("/dashboard");

  return (
    <div className={`app-shell ${isDashboardRoute ? "dashboard-shell-route" : ""}`}>
      {!isDashboardRoute && (
        <header className="app-header">
          <Link className="app-title" to="/">
            SmartCito
          </Link>
          <nav className="app-nav" aria-label="Primary navigation">
            <Link to="/home">Home</Link>
            <Link to="/mission">Mission</Link>
            <Link to="/architecture">Architecture</Link>
            <Link to="/community">Community</Link>
            <Link to="/roadmap">Roadmap</Link>
            <Link to="/dashboard">Dashboard</Link>
          </nav>
          <div className="app-profile" aria-label="Current profile">
            Operator
          </div>
        </header>
      )}

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
