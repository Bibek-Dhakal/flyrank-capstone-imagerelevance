import uuid

from pydantic import BaseModel, Field


class PostCreateRequest(BaseModel):
    title: str = Field(description="Title of the blog post")
    content: str = Field(description="Main text content of the blog post")


class PostResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str


class MatchSuggestionResponse(BaseModel):
    post_id: uuid.UUID
    image_id: uuid.UUID | None
    status: str = Field(description="ACCEPTED or REJECTED")
    reason: str = Field(description="Explanation of why it was matched or refused")
    similarity_score: float | None
    image_url: str | None
    image_tags: dict | None
