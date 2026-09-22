import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.database import get_db
from src.db.models import MatchSuggestion
from src.schemas.review import ReviewActionRequest, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/", response_model=list[ReviewResponse])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    """List all AI match suggestions to review."""
    stmt = select(MatchSuggestion).order_by(MatchSuggestion.created_at.desc())
    result = await db.execute(stmt)
    suggestions = result.scalars().all()

    return [
        ReviewResponse(
            id=s.id,
            post_id=s.post_id,
            image_id=s.image_id,
            similarity_score=s.similarity_score,
            ai_status=s.status,
            ai_reason=s.reason,
            human_status=getattr(s, "human_status", None),  # Future expansion
            created_at=s.created_at,
        )
        for s in suggestions
    ]


@router.post("/{suggestion_id}", response_model=ReviewResponse)
async def submit_review(
    suggestion_id: uuid.UUID, request: ReviewActionRequest, db: AsyncSession = Depends(get_db)
):
    """Approve or reject a match suggestion."""
    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    suggestion = await db.get(MatchSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # In a full app, this would update a 'human_status' column.
    # For this capstone, we will update the primary status with human override.
    suggestion.status = f"human_{request.action}d"
    await db.commit()
    await db.refresh(suggestion)

    return ReviewResponse(
        id=suggestion.id,
        post_id=suggestion.post_id,
        image_id=suggestion.image_id,
        similarity_score=suggestion.similarity_score,
        ai_status=suggestion.status,
        ai_reason=suggestion.reason,
        human_status=suggestion.status,
        created_at=suggestion.created_at,
    )
