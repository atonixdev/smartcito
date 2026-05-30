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

function GitHubIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path
        fill="currentColor"
        d="M12 2C6.48 2 2 6.59 2 12.25c0 4.53 2.87 8.37 6.84 9.72.5.1.68-.22.68-.49 0-.24-.01-1.04-.01-1.88-2.78.62-3.37-1.21-3.37-1.21-.45-1.18-1.11-1.49-1.11-1.49-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.58 2.35 1.13 2.92.86.09-.67.35-1.13.64-1.39-2.22-.26-4.56-1.14-4.56-5.08 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05A9.3 9.3 0 0 1 12 6.84c.85 0 1.71.12 2.51.35 1.91-1.33 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.95-2.35 4.81-4.59 5.07.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.8 0 .27.18.6.69.49A10.29 10.29 0 0 0 22 12.25C22 6.59 17.52 2 12 2Z"
      />
    </svg>
  );
}

function GitLabIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path
        fill="currentColor"
        d="m12 22 3.68-11.33H8.32L12 22Zm0 0L8.32 10.67H3.17L12 22Zm-8.83-11.33-.34 1.05a.92.92 0 0 0 .33 1.02L12 22 3.17 10.67Zm0 0h5.15L6.1 3.83a.46.46 0 0 0-.88 0L3.17 10.67Zm8.83 11.33 8.84-10.28a.92.92 0 0 0 .32-1.02l-.34-1.05L12 22Zm8.84-11.33L18.78 3.83a.46.46 0 0 0-.88 0l-2.22 6.84h5.16Z"
      />
    </svg>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link className="brand-lockup" to="/home">
          <OrcaLogo className="brand-mark" title="Official ORCA symbol" />
          <div className="brand-copy">
            <h1 className="app-title">Orca</h1>
          </div>
        </Link>
        <nav className="app-nav">
          <Link to="/downloads">Downloads</Link>
          <Link to="/docs">Docs</Link>
          <a href="https://github.com/AtonixCorp/Orca" target="_blank" rel="noreferrer">
            <GitHubIcon />
            <span>GitHub</span>
          </a>
          <a href="https://gitlab.com/atonixdev/smartcito" target="_blank" rel="noreferrer">
            <GitLabIcon />
            <span>GitLab</span>
          </a>
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
        <small>© 2026 ORCA. All rights reserved.</small>
        <div className="footer-links">
          <a href="https://github.com/AtonixCorp/Orca" target="_blank" rel="noreferrer">
            <GitHubIcon />
            <span>GitHub</span>
          </a>
          <a href="https://gitlab.com/atonixdev/smartcito" target="_blank" rel="noreferrer">
            <GitLabIcon />
            <span>GitLab</span>
          </a>
          <Link to="/docs">Documentation</Link>
        </div>
      </footer>
    </div>
  );
}
