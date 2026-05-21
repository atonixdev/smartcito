"""
================================================================================
 File: backend/app/services/__init__.py
 Purpose:
   Domain services — reusable business logic kept out of HTTP handlers.
   Endpoints orchestrate; services do the actual work. This keeps the API
   thin and makes the same logic reusable from background workers, CLI
   tools, and tests.
================================================================================
"""
