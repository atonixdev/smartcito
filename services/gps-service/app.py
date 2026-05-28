from fastapi import FastAPI

app = FastAPI(title="Orca GPS Service")


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
