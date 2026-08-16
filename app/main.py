from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="Academic AI API",
    description="Backend API for the Academic AI platform",
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Academic AI Backend is running"
    }