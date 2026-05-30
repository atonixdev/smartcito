/**
 * ============================================================================
 * File: webapp/src/App.tsx
 * Purpose:
 *   Top-level component. Owns the route table and the persistent shell
 *   (header, navigation). Keep this file small — routes pull in their own
 *   page components from `src/pages`.
 * ============================================================================
 */

import { Link, Navigate, Route, Routes } from "react-router-dom";

import OrcaLogo from "./components/OrcaLogo";
import Home from "./pages/Home";
import Architecture from "./pages/Architecture";
import Community from "./pages/Community";
import Docs from "./pages/Docs";
import Downloads from "./pages/Downloads";
import Firmware from "./pages/Firmware";
import NotFound from "./pages/NotFound";
import Roadmap from "./pages/Roadmap";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-lockup">
          <OrcaLogo className="brand-mark" title="Official ORCA symbol" />
          <div className="brand-copy">
            <h1 className="app-title">Orca</h1>
            <span className="app-title-sub">
              Local-first robotics and security
            </span>
          </div>
        </div>
        <nav className="app-nav">
          <Link to="/home">Home</Link>
          <Link to="/downloads">Downloads</Link>
          <Link to="/docs">Docs</Link>
          <Link to="/architecture">Architecture</Link>
          <Link to="/firmware">Firmware</Link>
          <Link to="/community">Developer Guides</Link>
          <Link to="/roadmap">Roadmap</Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<Home />} />
          <Route path="/downloads" element={<Downloads />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/firmware" element={<Firmware />} />
          <Route path="/community" element={<Community />} />
          <Route path="/roadmap" element={<Roadmap />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <small>
          Orca · Local-first device operations · Apache 2.0 ·{" "}
          <a
            href="https://github.com/AtonixCorp/Orca"
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
