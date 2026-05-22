from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SmartCito GPS Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gps-service"}


@app.get("/standards")
async def standards() -> dict[str, object]:
    return {
        "service": "gps-service",
        "supported": ["nmea0183", "nmea2000", "json"],
        "purpose": "gps normalization and ingestion",
    }

@app.get("/api/gps/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok", "service": "gps-service"}
