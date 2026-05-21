"""
================================================================================
 File: backend/app/dash_app/server.py
 Purpose:
   Live sensor dashboard built with Plotly Dash. Intended for analysts and
   data engineers who want a quick, code-defined view of the data flowing
   through SmartCito.

 How it works:
   - Every 5 seconds, callbacks fetch the latest readings from the API.
   - Readings are grouped by sensor and rendered as a time-series chart.
   - Auth: in production, place this behind an SSO proxy (oauth2-proxy) —
     Dash itself does not enforce auth.

 Run:
     python -m app.dash_app.server
 Browse:
     http://localhost:8050
================================================================================
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

API_BASE = os.getenv("SMARTCITO_API_BASE", "http://localhost:8000/api/v1")
REFRESH_MS = int(os.getenv("DASH_REFRESH_MS", "5000"))


def _fetch_readings(limit: int = 200) -> pd.DataFrame:
    """Pull recent readings from the API and return them as a DataFrame.

    On error we log and return an empty frame so the UI degrades gracefully
    instead of crashing.
    """
    try:
        res = httpx.get(f"{API_BASE}/sensors/recent", params={"limit": limit}, timeout=5)
        res.raise_for_status()
        data: list[dict[str, Any]] = res.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Dash fetch failed: %s", exc)
        return pd.DataFrame(columns=["sensor_id", "kind", "value", "observed_at"])

    df = pd.DataFrame(data)
    if not df.empty:
        df["observed_at"] = pd.to_datetime(df["observed_at"])
    return df


def build_app() -> Dash:
    """Factory for the Dash application."""
    app = Dash(__name__, title="SmartCito · Analytics")

    app.layout = html.Div(
        style={"fontFamily": "system-ui", "padding": "1.5rem", "background": "#0f172a",
               "color": "#e2e8f0", "minHeight": "100vh"},
        children=[
            html.H2("SmartCito Live Analytics"),
            html.P("Streaming view of recent sensor readings. Refreshes every "
                   f"{REFRESH_MS // 1000}s."),
            dcc.Interval(id="tick", interval=REFRESH_MS, n_intervals=0),
            dcc.Graph(id="ts-chart"),
            html.Div(id="summary", style={"marginTop": "1rem"}),
        ],
    )

    @app.callback(
        Output("ts-chart", "figure"),
        Output("summary", "children"),
        Input("tick", "n_intervals"),
    )
    def _refresh(_n: int) -> tuple[Any, Any]:
        df = _fetch_readings()
        if df.empty:
            return px.line(title="No data yet"), "Waiting for readings…"

        fig = px.line(
            df.sort_values("observed_at"),
            x="observed_at",
            y="value",
            color="sensor_id",
            line_group="sensor_id",
            title="Sensor values over time",
            template="plotly_dark",
        )
        summary = f"{len(df)} readings across {df['sensor_id'].nunique()} sensors."
        return fig, summary

    return app


def main() -> None:
    configure_logging("INFO")
    app = build_app()
    app.run_server(host="0.0.0.0", port=8050, debug=False)  # noqa: S104


if __name__ == "__main__":
    main()
