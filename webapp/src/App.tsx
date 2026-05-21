/**
 * ============================================================================
 * File: frontend/src/App.tsx
 * Purpose:
 *   Top-level component. Owns the route table and the persistent shell
 *   (header, navigation). Keep this file small — routes pull in their own
 *   page components from `src/pages`.
 * ============================================================================
 */

import { Link, Route, Routes } from "react-router-dom";

import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">SmartCito</h1>
        <nav className="app-nav">
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

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
    </div>
  );
}
