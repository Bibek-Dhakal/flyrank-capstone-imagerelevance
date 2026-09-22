# Usage & Operations Documentation

This directory details operational workflows, environment configurations, and command references.

## Environment Variables

Refer to `.env.example` in the project root.

| Variable          | Description                                                                             |
|-------------------|-----------------------------------------------------------------------------------------|
| `DATABASE_URL`    | PostgreSQL connection string (must use `postgresql+asyncpg://` for async DB operations) |
| `GEMINI_API_KEY`  | Free-tier key from Google AI Studio                                                     |
| `OLLAMA_API_BASE` | URL for local Ollama instance (fallback)                                                |
