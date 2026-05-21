"""
================================================================================
 File: backend/app/dash_app/__init__.py
 Purpose:
   Plotly Dash side-app that runs as a separate process from the FastAPI
   API. Polls `/api/v1/sensors/recent` and renders a live line chart.

   This is intentionally NOT mounted inside FastAPI — Dash uses its own
   Flask server and threading model, and embedding it complicates auth.
   Running it as a sibling service keeps each app simple to operate.

 Run:
     python -m app.dash_app.server
================================================================================
"""
