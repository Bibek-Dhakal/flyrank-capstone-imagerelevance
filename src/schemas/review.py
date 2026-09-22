import uuid
from datetime import datetime

from pydantic import BaseModel


class ReviewActionRequest(BaseModel):
    action: str  # 'approve' or 'reject'
    feedback: str | None = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    image_id: uuid.UUID | None
    similarity_score: float | None
    ai_status: str
    ai_reason: str | None
    human_status: str | None
    created_at: datetime
