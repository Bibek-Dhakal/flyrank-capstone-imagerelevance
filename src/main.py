from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.api.v1 import images
from src.db.database import engine
from src.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure pgvector and tables exist on startup for a smooth local DX experience.
    # In full production setups, manual Alembic migration runs are strictly enforced.
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="FoxGuard API",
    description="AI Image Understanding & Content Matching Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(images.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {"status": "ok", "service": "imagerelevance"}
