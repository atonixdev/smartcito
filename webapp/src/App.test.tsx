/**
 * ============================================================================
 * File: webapp/src/App.test.tsx
 * Purpose: Smoke test ensuring the docs-focused app renders and routes.
 * ============================================================================
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

describe("App", () => {
  it("opens the home page by default", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText(/Get Orca tools/i)).toBeInTheDocument();
  });

  it("routes the downloads page", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/downloads"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByText(/CLI, SDK, TUI, and local agent deliverables/i),
    ).toBeInTheDocument();
  });
});
