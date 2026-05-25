import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import Visualization from "./Visualization";

describe("Visualization", () => {
  it("renders embedded observability surfaces behind shared routes", () => {
    render(
      <MemoryRouter>
        <Visualization />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: /Dash, metrics, and logs from one routed surface/i }),
    ).toBeInTheDocument();
    expect(screen.getByTitle("Plotly Dash embed")).toHaveAttribute("src", "/dash/");
    expect(screen.getByTitle("Grafana embed")).toHaveAttribute(
      "src",
      "/grafana/d/smartcito-overview/smartcito-overview?kiosk",
    );
    expect(screen.getByTitle("Kibana embed")).toHaveAttribute(
      "src",
      "/kibana/app/home#/?embed=true",
    );
    expect(screen.getAllByRole("link", { name: /Open full surface/i })).toHaveLength(3);
  });
});