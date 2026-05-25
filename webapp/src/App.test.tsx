/**
 * ============================================================================
 * File: webapp/src/App.test.tsx
 * Purpose: Smoke test ensuring the app renders without crashing.
 * ============================================================================
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

vi.mock("./pages/DroneDashboard", () => ({
  default: () => <div>Drone Dashboard Route</div>,
}));

vi.mock("./pages/RobotDashboard", () => ({
  default: () => <div>Robot Dashboard Route</div>,
}));

vi.mock("./pages/Dashboard", () => ({
  default: () => <div>City Map Dashboard Route</div>,
}));

describe("App", () => {
  it("opens the dashboard by default", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByText(/Drone Dashboard Route/i),
    ).toBeInTheDocument();
  });

  it("routes the robot dashboard", async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/dashboard/robot"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText(/Robot Dashboard Route/i)).toBeInTheDocument();
  });
});
