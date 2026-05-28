from fastapi import FastAPI

app = FastAPI(title="Orca Camera Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "camera-service"}


@app.get("/capabilities")
async def capabilities() -> dict[str, object]:
    return {
        "service": "camera-service",
        "protocols": ["onvif", "rtsp", "http2"],
        "purpose": "video ingestion and device stream validation",
    }
