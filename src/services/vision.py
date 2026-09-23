import base64
import logging

import httpx
from litellm import acompletion, completion_cost
from pydantic import ValidationError

from src.config import settings
from src.schemas.image import ImageMetadataOutput

logger = logging.getLogger(__name__)


async def fetch_image_as_base64(url: str) -> str:
    """
    Downloads an image using httpx and converts it to a base64 data URI.
    This prevents AI models from failing due to internal scraper blocks or 404s.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        mime_type = response.headers.get("content-type", "image/jpeg")
        encoded_string = base64.b64encode(response.content).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_string}"


async def analyze_image(image_url: str) -> tuple[ImageMetadataOutput | None, float, dict]:
    """
    Analyzes an image using a vision model.
    Returns: (Parsed metadata or None if invalid, cost, usage_stats)
    """
    prompt = """
    Analyze this image and return a JSON object exactly matching this schema:
    {
      "subject": "string",
      "category": "string",
      "attributes": ["string", "string"],
      "caption": "string",
      "confidence": 0.95
    }
    Output ONLY valid JSON. The confidence score should be your certainty of the subject and category from 0.0 to 1.0.
    """

    try:
        base64_image = await fetch_image_as_base64(image_url)
    except Exception as e:
        logger.error(f"Failed to download image {image_url}: {e}")
        return None, 0.0, {}

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": base64_image}},
            ],
        }
    ]

    try:
        response = await acompletion(
            model=settings.vision_model,
            messages=messages,
            num_retries=3,  # Auto-retry on rate limits (429)
        )

        cost = 0.0
        try:
            cost = completion_cost(completion_response=response)
        except Exception:
            pass

        usage = response.usage.model_dump() if hasattr(response, "usage") and response.usage else {}
        content = response.choices[0].message.content

        if not content:
            return None, cost, usage

        content = content.strip()
        # Clean potential markdown fences commonly created by LLMs
        if content.startswith("```json"):
            content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            content = content.replace("```", "", 1)
            if content.endswith("```"):
                content = content[:-3]

        content = content.strip()

        metadata = ImageMetadataOutput.model_validate_json(content)
        return metadata, cost, usage

    except ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        return None, 0.0, {}
    except Exception as e:
        logger.error(f"Vision model call failed: {e}")
        return None, 0.0, {}
