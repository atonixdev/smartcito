/**
 * ============================================================================
 * File: webapp/src/pages/NotFound.tsx
 * Purpose: 404 fallback route.
 * ============================================================================
 */

import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section className="not-found">
      <h2>404 — page not found</h2>
      <p>
        The page you requested doesn’t exist. Try going <Link to="/">home</Link>
        .
      </p>
    </section>
  );
}
