from fastapi import FastAPI

app = FastAPI(title="Orca Security Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "security-service"}


@app.get("/controls")
async def controls() -> dict[str, object]:
    return {
        "service": "security-service",
        "controls": ["jwt", "rbac", "aes-256", "pqc-ready", "qkd-ingest"],
    }
