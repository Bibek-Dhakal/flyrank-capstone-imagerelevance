import logging

from litellm import aembedding, completion_cost

from src.config import settings

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> tuple[list[float] | None, float, dict]:
    """
    Generates a vector embedding for the given text using the configured embedding model.
    Falls back to alternate Gemini embedding models if the primary one is unavailable.
    """
    models_to_try = [
        settings.embedding_model,
        "gemini/gemini-embedding-2",
        "gemini/gemini-embedding-001",
        "gemini/text-embedding-004",
    ]

    # Remove duplicates while preserving order
    seen = set()
    models_to_try = [x for x in models_to_try if not (x in seen or seen.add(x))]

    last_error = None

    for model in models_to_try:
        try:
            response = await aembedding(
                model=model,
                input=text,
            )

            cost = 0.0
            try:
                cost = completion_cost(completion_response=response)
            except Exception:
                pass

            usage = (
                response.usage.model_dump() if hasattr(response, "usage") and response.usage else {}
            )
            vector = response.data[0].embedding

            # Matryoshka Representation Learning: newer Gemini models default to 3072 dimensions,
            # but they are mathematically trained to be safely truncated to 768 without losing
            # semantic meaning. Slicing it protects our pgvector(768) database columns from crashing!
            if len(vector) > 768:
                vector = vector[:768]
            elif len(vector) < 768:
                vector = vector + [0.0] * (768 - len(vector))

            return vector, cost, usage

        except Exception as e:
            logger.warning(f"Embedding generation with {model} failed: {e}. Trying fallback...")
            last_error = e
            continue

    logger.error(f"All embedding models failed. Last error: {last_error}")
    return None, 0.0, {}
