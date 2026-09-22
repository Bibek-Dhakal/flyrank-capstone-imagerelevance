# FoxGuard (FlyRank Capstone - Image Relevance)

AI Image Understanding & Content Matching Engine.
Understand an image library, organize it automatically, and match the right image to the right article — with a strict production-grade mismatch guard.

## Phase 1: Design Document

### 1. Problem Statement
The goal is to build a trustworthy AI decision system that matches images to blog posts based on semantics, not keywords. The most critical requirement is the **mismatch guard**: the system must safely reject uncertain or mismatched images (e.g., rejecting a wolf image for a red-fox post) and explain why, rather than guessing blindly.

### 2. Explicit Non-Goal
We are **not** building a frontend UI or a comprehensive image management platform. The review interface will be handled purely via validated API endpoints. Comparing multiple embedding/vision models is out of scope; we will stick to one vision model and one embedding model.

### 3. Data Model
* **ImageMetadata**: Stores image URLs, parsed structured output (subject, category, attributes, caption), and AI confidence score.
* **ImageEmbedding**: Stores the vector embedding (`pgvector`) generated from the image caption/attributes.
* **Post**: Stores blog post content and its vector embedding.
* **MatchSuggestion**: Stores the pairing between a Post and an Image, including the similarity score, mismatch guard status (Accepted/Rejected), and the explanation.

### 4. API Surface
* `POST /api/v1/images/ingest` - Trigger async batch job to process images through the vision model.
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
* Python 3.10+
* Docker & Docker Compose (for PostgreSQL + pgvector)

### 2. Installation
```bash
# Install dependencies
pip install -e ".[dev]"

# Setup environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY or preferred AI provider key
```

### 3. Running the Stack
Start the database and the API server:
```bash
docker compose up -d
uvicorn src.main:app --reload
```

### 4. Seeding Data (Coming in Phase 2)
```bash
python src/scripts/seed.py
```

### 5. Documentation Directory
* [Architecture Docs](docs/architecture/README.md)
* [Usage & Config](docs/usage/README.md)
* [Testing Setup](docs/testing/README.md)
* [Code Quality](docs/CODE_QUALITY.md)
