import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from src.api.v1 import images, posts, reviews
from src.config import settings
from src.db.database import engine
from src.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure pgvector and tables exist on startup for a smooth local DX experience.
    # In full production setups, manual Alembic migration runs are strictly enforced.
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    # Ensure the public / images directory exists
    os.makedirs("public/images", exist_ok=True)
    yield


app = FastAPI(
    title="FoxGuard API",
    description="AI Image Understanding & Content Matching Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the public directory to serve local images
app.mount("/public", StaticFiles(directory="public"), name="public")

app.include_router(images.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {"status": "ok", "service": "imagerelevance"}
