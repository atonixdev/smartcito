import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Dashboard from "./Dashboard";

vi.mock("@/components/LocationIntelligencePanel", () => ({
  default: () => <section><h3>Sovereign Location Intelligence</h3></section>,
}));

vi.mock("@/components/OperationsVisualizationPanel", () => ({
  default: () => <section><h3>Map Visualization</h3></section>,
}));

vi.mock("@/components/UnifiedLogsThreatPanel", () => ({
  default: () => <section><h3>Unified Logs & AI Threat Analysis</h3></section>,
}));

vi.mock("@/api/sensors", () => ({
  useRecentSensors: () => ({
    data: [],
    isLoading: false,
    isError: false,
    error: null,
  }),
}));

describe("Dashboard", () => {
  it("renders the unified operations dashboard", async () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>,
    );

    expect(
      screen.getByRole("heading", { name: /SmartCito Operations Visualization/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Sovereign Location Intelligence/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Map Visualization/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Operations Logs/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Unified Logs & AI Threat Analysis/i }),
    ).toBeInTheDocument();
  });
});