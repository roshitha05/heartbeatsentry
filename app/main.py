from fastapi import FastAPI

from app.database import Base, engine
from app.routers import endpoints

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HeartbeatSentry",
    description="API endpoint health and uptime monitoring service.",
    version="1.0.0",
)

app.include_router(endpoints.router)


@app.get("/")
def root():
    return {
        "service": "HeartbeatSentry",
        "message": "API monitoring service is running.",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}