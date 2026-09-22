import asyncio
import logging
import uuid

from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.db.database import AsyncSessionLocal
from src.db.models import CostLog, Image
from src.services.vision import analyze_image

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _do_process_single_image(image_id: uuid.UUID):
    """
    Process a single image, utilizing retries on transient errors.
    Idempotent by nature — checks if already completed or flagged.
    """
    async with AsyncSessionLocal() as session:
        image = await session.get(Image, image_id)
        if not image or image.status in ["completed", "flagged"]:
            return

        image.status = "processing"
        await session.commit()

    try:
        metadata, cost, usage = await analyze_image(image.url)

        async with AsyncSessionLocal() as session:
            db_image = await session.get(Image, image_id)
            if cost > 0 or usage:
                cost_log = CostLog(
                    operation="vision",
                    model=settings.vision_model,
                    cost=cost,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )
                session.add(cost_log)

            if not metadata:
                # Trigger a retry from tenacity
                raise Exception("Vision call failed or returned invalid schema")

            # Mismatch guard: Low confidence check
            if metadata.confidence < 0.7:
                db_image.status = "flagged"
                db_image.error_message = "Low confidence classification"
            else:
                db_image.status = "completed"
                db_image.error_message = None

            db_image.subject = metadata.subject
            db_image.category = metadata.category
            db_image.attributes = metadata.attributes
            db_image.caption = metadata.caption
            db_image.confidence = metadata.confidence

            await session.commit()

    except Exception as e:
        logger.error(f"Error processing image {image_id}: {e}")
        raise e


async def batch_process_images(image_ids: list[uuid.UUID]):
    """
    Runs resilient background processing with a concurrency ceiling.
    """
    semaphore = asyncio.Semaphore(5)

    async def sem_task(image_id):
        async with semaphore:
            try:
                await _do_process_single_image(image_id)
            except Exception as e:
                async with AsyncSessionLocal() as session:
                    img = await session.get(Image, image_id)
                    if img:
                        img.status = "failed"
                        img.error_message = f"Failed after retries: {str(e)}"
                        await session.commit()

    await asyncio.gather(*(sem_task(img_id) for img_id in image_ids))
