from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.database import get_db
from src.db.models import CostLog, Image
from src.schemas.image import ImageIngestRequest
from src.services.batch import batch_process_images

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/ingest")
async def ingest_images(
    requests: list[ImageIngestRequest],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    image_ids = []
    for req in requests:
        # Idempotency guard
        stmt = select(Image).where(Image.url == str(req.url))
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            if existing.status in ["failed", "pending"]:
                image_ids.append(existing.id)
            continue

        new_image = Image(url=str(req.url))
        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)
        image_ids.append(new_image.id)

    if image_ids:
        background_tasks.add_task(batch_process_images, image_ids)

    return {"message": f"Queued {len(image_ids)} images for processing."}


@router.get("/")
async def list_images(db: AsyncSession = Depends(get_db)):
    """Retrieve all processed, pending, flagged, and failed images."""
    stmt = select(Image).order_by(Image.created_at.desc())
    result = await db.execute(stmt)
    images = result.scalars().all()
    return images


@router.get("/costs")
async def get_costs(db: AsyncSession = Depends(get_db)):
    """Retrieve aggregated AI costs from the processing engine."""
    stmt = select(
        CostLog.operation,
        func.sum(CostLog.cost).label("total_cost"),
        func.count(CostLog.id).label("total_calls"),
    ).group_by(CostLog.operation)

    result = await db.execute(stmt)
    costs = []
    for row in result.all():
        costs.append(
            {
                "operation": row.operation,
                "total_cost": row.total_cost,
                "total_calls": row.total_calls,
            }
        )
    return costs
