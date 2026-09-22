import asyncio
import logging
import uuid

from sqlalchemy.future import select
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.db.database import AsyncSessionLocal
from src.db.models import CostLog, Image, ImageEmbedding
from src.services.embeddings import generate_embedding
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
        # 1. Vision Tagging
        metadata, v_cost, v_usage = await analyze_image(image.url)

        async with AsyncSessionLocal() as session:
            db_image = await session.get(Image, image_id)
            if v_cost > 0 or v_usage:
                cost_log = CostLog(
                    operation="vision",
                    model=settings.vision_model,
                    cost=v_cost,
                    prompt_tokens=v_usage.get("prompt_tokens", 0),
                    completion_tokens=v_usage.get("completion_tokens", 0),
                )
                session.add(cost_log)

            if not metadata:
                raise Exception("Vision call failed or returned invalid schema")

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

        # 2. Embedding Generation (if vision succeeded and passed confidence check)
        if metadata and metadata.confidence >= 0.7:
            semantic_text = f"Subject: {metadata.subject}. Category: {metadata.category}. Attributes: {', '.join(metadata.attributes)}. Caption: {metadata.caption}"

            e_vector, e_cost, e_usage = await generate_embedding(semantic_text)

            if e_vector:
                async with AsyncSessionLocal() as session:
                    if e_cost > 0 or e_usage:
                        cost_log_emb = CostLog(
                            operation="embedding",
                            model=settings.embedding_model,
                            cost=e_cost,
                            prompt_tokens=e_usage.get("prompt_tokens", 0),
                            completion_tokens=e_usage.get(
                                "total_tokens", 0
                            ),  # litellm embedding format mapping
                        )
                        session.add(cost_log_emb)

                    # Ensure we don't insert duplicates if retried partially
                    stmt = select(ImageEmbedding).where(ImageEmbedding.image_id == image_id)
                    result = await session.execute(stmt)
                    existing_emb = result.scalars().first()

                    if not existing_emb:
                        new_emb = ImageEmbedding(image_id=image_id, embedding=e_vector)
                        session.add(new_emb)
                    else:
                        existing_emb.embedding = e_vector

                    await session.commit()

    except Exception as e:
        logger.error(f"Error processing image {image_id}: {e}")
        raise e


async def batch_process_images(image_ids: list[uuid.UUID]):
    """
    Runs resilient background processing with a concurrency ceiling.
    """
    # Reduced concurrency to 2 to heavily respect Gemini Free Tier limits
    semaphore = asyncio.Semaphore(2)

    async def sem_task(image_id):
        async with semaphore:
            try:
                await _do_process_single_image(image_id)
                # Sleep between successful processings to throttle request rate
                await asyncio.sleep(4)
            except Exception as e:
                async with AsyncSessionLocal() as session:
                    img = await session.get(Image, image_id)
                    if img:
                        img.status = "failed"
                        img.error_message = f"Failed after retries: {str(e)}"
                        await session.commit()

    await asyncio.gather(*(sem_task(img_id) for img_id in image_ids))
