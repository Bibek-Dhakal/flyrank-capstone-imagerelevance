from fastapi import FastAPI

app = FastAPI(
    title="FoxGuard API",
    description="AI Image Understanding & Content Matching Engine",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {"status": "ok", "service": "imagerelevance"}


# TODO: Add /api/v1 routers for images, posts, and reviews (Phase 2 & 3)
