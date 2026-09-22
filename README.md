# FoxGuard (FlyRank Capstone - Image Relevance)

AI Image Understanding & Content Matching Engine.
Understand an image library, organize it automatically, and match the right image to the right article — with a strict production-grade mismatch guard.

**🔥 Top-1 Precision Score: 100.00%** (Tested on 10 labeled post-to-image semantic pairings)

## Phase 4: Production Layer (Final)
- **Review API**: Human-in-the-loop endpoints allowing moderators to inspect AI matching reasoning, and approve/reject suggestions.
- **Eval Script**: A fully automated evaluation script testing Top-1 Precision against the Mismatch Guard.
- **Seed Script**: Bootstraps the application with your local wildlife imagery, fully monitoring the asynchronous background jobs.

## Phase 3: Matching Engine & Mismatch Guard
- **Embedding Generation**: Connecting image metadata and post content to `gemini/gemini-embedding-2`.
- **Vector Database**: Utilized PostgreSQL `pgvector` for `<=>` cosine distance similarity scoring. Uses Matryoshka Representation slicing to gracefully constrain new 3072-dimension models into standard 768-dimension columns.
- **The Mismatch Guard**: An active safety layer that intercepts vector-matched candidates. It parses tags and post semantics via a secondary LLM validation step to reliably reject mismatched categories (e.g. rejecting a wolf image for a red-fox post).

## Phase 2: Image Understanding Pipeline
- **Vision Model API integration** via LiteLLM (`gemini/gemini-3.6-flash`). We utilize explicit Base64 image downloading to guarantee reliability against web-scraper blocking.
- **Structured JSON output** using strict Pydantic schema validation.
- **Batch Processing with Resilience**: `asyncio.Semaphore` combined with `tenacity` retries.
- **Cost Tracking**: All AI API calls actively log operations, usage tokens, and cost.
- **Mismatch / Confidence Guard Start**: Any low-confidence categorization (<0.70) is proactively flagged for review rather than blindly accepted.
- **Dockerization**: The entire API and Database now run strictly in isolated Docker containers for a unified developer experience.

## Setup & Running Locally

### 1. Requirements
* Docker & Docker Compose

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

### 4. Seeding & Evaluation
To populate the database with images (The script will automatically wait for the background AI jobs to finish):
```bash
docker compose exec api python src/scripts/seed.py
```
To run the automated Precision Evaluation suite:
```bash
docker compose exec api python src/scripts/eval.py
```
