from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """Base model for collected content items."""

    source: str = Field(..., description="Source type (rss, web)")
    content: str = Field(..., description="Content text")
    url: str = Field(..., description="Content URL")
    title: str = Field(
        "", description="Content title"
    )  # Empty string default instead of None
    date: Optional[str] = Field(None, description="Publication date")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S UTC")}
