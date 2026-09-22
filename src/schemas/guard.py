from pydantic import BaseModel, Field


class MismatchGuardOutput(BaseModel):
    is_match: bool = Field(
        description="True if the image strictly matches the post semantics, False if it is a mismatch"
    )
    reason: str = Field(
        description="Explanation of why it matches or why it was rejected (e.g., 'Animal category mismatch: expected fox, detected wolf')"
    )
