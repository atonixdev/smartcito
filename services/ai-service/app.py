from fastapi import FastAPI

app = FastAPI(title="Orca AI Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-service"}


@app.get("/models")
async def models() -> dict[str, object]:
    return {
        "service": "ai-service",
        "models": ["traffic-anomaly", "camera-event-enrichment"],
        "runtime": "tensorflow|pytorch",
    }
