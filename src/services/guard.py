import logging

from litellm import acompletion, completion_cost
from pydantic import ValidationError

from src.config import settings
from src.db.models import Image, Post
from src.schemas.guard import MismatchGuardOutput

logger = logging.getLogger(__name__)


async def execute_mismatch_guard(
    post: Post, image: Image
) -> tuple[MismatchGuardOutput, float, dict]:
    """
    The Safety Layer.
    Combines tag validation and post semantics to reject incorrect matches (e.g. Wolf on Fox post).
    """
    prompt = f"""
    You are a strict Mismatch Guard. Your job is to prevent bad image recommendations for blog posts.

    POST DATA:
    Title: {post.title}
    Content: {post.content}

    CANDIDATE IMAGE TAGS:
    Subject: {image.subject}
    Category: {image.category}
    Attributes: {image.attributes}
    Caption: {image.caption}

    Determine if this image strictly matches the post's core subject. Do not guess.
    If the post is about a 'red fox', a 'wolf' or generic 'dog' image MUST be REJECTED.

    Output strictly in this JSON format:
    {{
        "is_match": true or false,
        "reason": "Clear explanation of why it matches or why it was rejected (e.g., 'Animal category mismatch: expected fox, detected wolf')."
    }}
    """

    messages = [{"role": "user", "content": prompt}]

    try:
        response = await acompletion(
            model=settings.vision_model,  # Reuse standard fast LLM for text-to-text here
            messages=messages,
            response_format={"type": "json_object"},
        )

        cost = 0.0
        try:
            cost = completion_cost(completion_response=response)
        except Exception:
            pass

        usage = response.usage.model_dump() if hasattr(response, "usage") and response.usage else {}
        content = response.choices[0].message.content

        if not content:
            return (
                MismatchGuardOutput(
                    is_match=False, reason="Guard evaluation failed to return content"
                ),
                cost,
                usage,
            )

        content = content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            content = content.replace("```", "", 1)
            if content.endswith("```"):
                content = content[:-3]

        guard_result = MismatchGuardOutput.model_validate_json(content.strip())
        return guard_result, cost, usage

    except ValidationError as e:
        logger.error(f"Guard schema validation failed: {e}")
        return MismatchGuardOutput(is_match=False, reason="Guard system validation error"), 0.0, {}
    except Exception as e:
        logger.error(f"Guard evaluation failed: {e}")
        return MismatchGuardOutput(is_match=False, reason="Guard system error"), 0.0, {}
