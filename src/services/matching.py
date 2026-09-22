import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config import settings
from src.db.models import CostLog, Image, ImageEmbedding, MatchSuggestion, Post
from src.schemas.post import MatchSuggestionResponse
from src.services.guard import execute_mismatch_guard

logger = logging.getLogger(__name__)

# Max acceptable distance (Cosine distance: 0 is identical, 2 is opposite. 0.65 is a safe semantic threshold)
DISTANCE_THRESHOLD = 0.65


async def get_best_image_for_post(post_id: str, db: AsyncSession) -> MatchSuggestionResponse:
    """
    Ranks images based on vector similarity and runs the top candidate through the mismatch guard.
    """
    post = await db.get(Post, post_id)
    if not post:
        raise ValueError("Post not found")

    if not post.embedding:
        return MatchSuggestionResponse(
            post_id=post.id,
            image_id=None,
            status="REJECTED",
            reason="Post embedding not ready",
            similarity_score=None,
            image_url=None,
            image_tags=None,
        )

    # 1. Similarity Ranking
    # Calculate cosine distance using pgvector `<=>` operator
    distance_expr = ImageEmbedding.embedding.cosine_distance(post.embedding).label("distance")
    stmt = (
        select(Image, distance_expr)
        .join(ImageEmbedding, Image.id == ImageEmbedding.image_id)
        .where(Image.status == "completed")
        .order_by(distance_expr)
        .limit(3)
    )

    result = await db.execute(stmt)
    candidates = result.all()

    if not candidates:
        return MatchSuggestionResponse(
            post_id=post.id,
            image_id=None,
            status="REJECTED",
            reason="No confident match: No images available in the library.",
            similarity_score=None,
            image_url=None,
            image_tags=None,
        )

    # Evaluate the top candidate
    top_image, distance = candidates[0]
    similarity_score = (
        1 - distance
    )  # Convert distance to similarity score for easier UI rendering (1 = exact)

    # 2. Similarity Threshold Check
    if distance > DISTANCE_THRESHOLD:
        return MatchSuggestionResponse(
            post_id=post.id,
            image_id=None,
            status="REJECTED",
            reason=f"No confident match: Best similarity score ({similarity_score:.2f}) is below threshold.",
            similarity_score=similarity_score,
            image_url=None,
            image_tags=None,
        )

    # 3. Confidence Score Check (Vision output must be reliable)
    if top_image.confidence and top_image.confidence < 0.7:
        return MatchSuggestionResponse(
            post_id=post.id,
            image_id=top_image.id,
            status="REJECTED",
            reason="Rejected: Candidate image has low AI vision confidence.",
            similarity_score=similarity_score,
            image_url=top_image.url,
            image_tags={"subject": top_image.subject, "category": top_image.category},
        )

    # 4. The Mismatch Guard Check
    guard_result, cost, usage = await execute_mismatch_guard(post, top_image)

    # Log guard costs
    if cost > 0 or usage:
        cost_log = CostLog(
            operation="guard",
            model=settings.vision_model,
            cost=cost,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        db.add(cost_log)

    status = "ACCEPTED" if guard_result.is_match else "REJECTED"

    # 5. Persist the Suggestion for review API history
    suggestion = MatchSuggestion(
        post_id=post.id,
        image_id=top_image.id,
        similarity_score=similarity_score,
        status=status.lower(),
        reason=guard_result.reason,
    )
    db.add(suggestion)
    await db.commit()

    return MatchSuggestionResponse(
        post_id=post.id,
        image_id=top_image.id,
        status=status,
        reason=guard_result.reason,
        similarity_score=similarity_score,
        image_url=top_image.url,
        image_tags={
            "subject": top_image.subject,
            "category": top_image.category,
            "attributes": top_image.attributes,
        },
    )
