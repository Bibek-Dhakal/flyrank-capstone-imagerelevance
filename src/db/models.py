import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "images"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    subject: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String, index=True)
    attributes: Mapped[list | None] = mapped_column(JSON)
    caption: Mapped[str | None] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ImageEmbedding(Base):
    __tablename__ = "image_embeddings"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), unique=True
    )
    embedding = mapped_column(Vector(768))  # Gemini standard dimension
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    embedding = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MatchSuggestion(Base):
    __tablename__ = "match_suggestions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    image_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"))
    similarity_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        String, default="pending", index=True
    )  # pending, approved, rejected
    reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CostLog(Base):
    __tablename__ = "cost_logs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    operation: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    cost: Mapped[float] = mapped_column(Float)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
