from pydantic import BaseModel, Field, HttpUrl


class ImageIngestRequest(BaseModel):
    url: HttpUrl


class ImageMetadataOutput(BaseModel):
    subject: str = Field(description="The main subject of the image, e.g., 'red fox'")
    category: str = Field(description="The general category, e.g., 'animal'")
    attributes: list[str] = Field(
        description="List of visual attributes, e.g., ['orange fur', 'wild']"
    )
    caption: str = Field(description="A descriptive caption of the image")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
