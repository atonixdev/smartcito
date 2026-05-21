/**
 * ============================================================================
 * File: frontend/src/App.test.tsx
 * Purpose: Smoke test ensuring the app renders without crashing.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

describe("App", () => {
  it("renders the site title", () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByText(/SmartCito/i)).toBeInTheDocument();
  });
});
