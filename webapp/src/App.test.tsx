/**
 * ============================================================================
 * File: webapp/src/App.test.tsx
 * Purpose: Smoke test ensuring the app renders without crashing.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

describe("App", () => {
  it("opens the homepage by default", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("link", { name: /SmartCito/i })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /SmartCito/i, level: 2 }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open dashboard/i })).toBeInTheDocument();
  });
});
