/**
 * ============================================================================
 * File: webapp/src/components/AppHeader.tsx
 * Purpose:
 *   Enterprise SmartCito header with SVG brand lockup, centered navigation,
 *   dashboard profile shortcut, global theme toggle, and scroll collapse.
 * ============================================================================
 */

import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

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

export default function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(getInitialTheme);

  useEffect(() => setMenuOpen(false), [location.pathname]);

  useEffect(() => {
    let lastScrollY = window.scrollY;

    function onScroll() {
      const nextScrollY = window.scrollY;
      setCollapsed(nextScrollY > lastScrollY && nextScrollY > 24);
      lastScrollY = nextScrollY;
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  return (
    <header className={`app-header ${collapsed ? "is-collapsed" : ""} ${menuOpen ? "is-menu-open" : ""}`}>
      <Link className="app-brand" to="/" aria-label="SmartCito home">
        <span className="app-logo" aria-hidden="true">
          <svg className="app-icon-svg" viewBox="0 0 32 32" role="img">
            <rect className="app-icon-frame" x="2.5" y="2.5" width="27" height="27" rx="6" />
            <path className="app-icon-grid" d="M11 6v20M21 6v20M6 11h20M6 21h20" />
            <path className="app-icon-links" d="M16 6v6M16 20v6M6 16h6M20 16h6" />
            <circle className="app-icon-node" cx="16" cy="16" r="4" />
          </svg>
        </span>
        <span className="app-wordmark">
          <span className="app-wordmark-smart">Smart</span>
          <span className="app-wordmark-cito">Cito</span>
        </span>
      </Link>

      <button
        className="app-menu-toggle"
        type="button"
        aria-label="Toggle navigation menu"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((open) => !open)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>

      <nav className="app-nav" aria-label="Primary navigation">
        {navigationItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `app-nav-link${isActive ? " active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="app-actions" aria-label="Header actions">
        <button className="app-icon-button" type="button" aria-label="Search">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m21 21-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" />
          </svg>
        </button>
        <button
          className="app-icon-button"
          type="button"
          aria-label="Open dashboard"
          onClick={() => navigate("/dashboard")}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 21a8 8 0 0 0-16 0M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z" />
          </svg>
        </button>
        <button
          className="app-icon-button"
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3v2M12 19v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M3 12h2M19 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
