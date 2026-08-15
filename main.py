from fastapi import FastAPI

app = FastAPI(
    title="Academic AI API",
    description="Backend API for Academic AI",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "message": "Academic AI Backend is running"
    }