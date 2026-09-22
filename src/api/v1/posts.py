import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_db
from src.db.models import CostLog, Post
from src.schemas.post import MatchSuggestionResponse, PostCreateRequest, PostResponse
from src.services.embeddings import generate_embedding
from src.services.matching import get_best_image_for_post

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/", response_model=PostResponse)
async def create_post(request: PostCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a post and immediately generates its embedding."""
    new_post = Post(title=request.title, content=request.content)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    # Generate Embeddings immediately on create for simplicity
    semantic_text = f"Title: {new_post.title}. Content: {new_post.content}"
    vector, cost, usage = await generate_embedding(semantic_text)

    if not vector:
        # Rollback the post if embedding failed so we don't end up with corrupted data
        await db.delete(new_post)
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate post embedding via AI provider. Check API keys and region limits.",
        )

    new_post.embedding = vector

    if cost > 0 or usage:
        cost_log = CostLog(
            operation="embedding",
            model=settings.embedding_model,
            cost=cost,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("total_tokens", 0),
        )
        db.add(cost_log)

    await db.commit()

    return PostResponse(id=new_post.id, title=new_post.title, content=new_post.content)


@router.get("/{post_id}/images", response_model=MatchSuggestionResponse)
async def get_image_matches(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Runs the ranking engine and Mismatch Guard to find the best image for a post."""
    try:
        response = await get_best_image_for_post(str(post_id), db)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal matching error: {str(e)}")
