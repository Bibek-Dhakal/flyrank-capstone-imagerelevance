# FoxGuard (FlyRank Capstone - Image Relevance)

AI Image Understanding & Content Matching Engine.
Understand an image library, organize it automatically, and match the right image to the right article — with a strict production-grade mismatch guard.

## Phase 2: Image Understanding Pipeline
In this phase, we implemented:
- **Vision Model API integration** via LiteLLM (`gemini/gemini-3.6-flash`).
- **Structured JSON output** using strict Pydantic schema validation.
- **Batch Processing with Resilience**: `asyncio.Semaphore` combined with `tenacity` retries.
- **Cost Tracking**: All AI API calls actively log operations, usage tokens, and cost.
- **Mismatch / Confidence Guard Start**: Any low-confidence categorization (<0.70) is proactively flagged for review rather than blindly accepted.
- **Dockerization**: The entire API and Database now run strictly in isolated Docker containers for a unified developer experience.

## Phase 1: Design Document

### 1. Problem Statement
The goal is to build a trustworthy AI decision system that matches images to blog posts based on semantics, not keywords. The most critical requirement is the **mismatch guard**: the system must safely reject uncertain or mismatched images (e.g., rejecting a wolf image for a red-fox post) and explain why, rather than guessing blindly.

### 2. Explicit Non-Goal
We are **not** building a frontend UI or a comprehensive image management platform. The review interface will be handled purely via validated API endpoints. Comparing multiple embedding/vision models is out of scope; we will stick to one vision model and one embedding model.

### 3. Data Model
* **Image**: Stores image URLs, parsed structured output (subject, category, attributes, caption), and AI confidence score alongside its status (`completed`, `flagged`, etc.).
* **ImageEmbedding**: Stores the vector embedding (`pgvector`) generated from the image caption/attributes.
* **Post**: Stores blog post content and its vector embedding.
* **MatchSuggestion**: Stores the pairing between a Post and an Image, including the similarity score, mismatch guard status (Accepted/Rejected), and the explanation.
* **CostLog**: Logs AI API operations and metrics to ensure budget limitations are respected.

### 4. API Surface
* `POST /api/v1/images/ingest` - Trigger async batch job to process images through the vision model.
* `GET /api/v1/images/costs` - Review AI usage costs.
* `GET /api/v1/posts/{post_id}/images` - Retrieve ranked image suggestions for a post (passed through the mismatch guard).
* `POST /api/v1/reviews/{suggestion_id}` - Human-in-the-loop endpoint to approve or reject a suggested match.

### 5. Layer Sketch (Architecture)
```text
Images —(batch job via LiteLLM async)→ Vision Model → {tags, caption, confidence} → PostgreSQL
 | embed(caption) ————————→ image_vectors (pgvector)
Posts ————————————→ embed(post text) ————————————→ post_vectors (pgvector)

GET /posts/:id/images
 → Similarity Ranking (image_vectors × post_vector)
 → Mismatch Guard (tags + threshold + confidence)
 | Suggested image (ranked, explained)
 | "No confident match" + explanation
```

---

## Setup & Running Locally

### 1. Requirements
* Docker & Docker Compose (Requirements for Database + pgvector and the API application)

### 2. Environment Setup
```bash
# Setup environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Running the Stack
Start the database and the API server in one command:
```bash
docker compose up --build -d
```
Check API logs to ensure it booted correctly:
```bash
docker compose logs -f api
```

*Note: Database tables and pgvector extension are created automatically on API startup. Alembic environments are pre-configured to easily track schema migrations.*

### 4. Seeding Data (Coming soon)
```bash
python src/scripts/seed.py
```

### 5. Documentation Directory
* [Architecture Docs](docs/architecture/README.md)
* [Usage & Config](docs/usage/README.md)
* [Testing Setup](docs/testing/README.md)
* [Code Quality](docs/CODE_QUALITY.md)
