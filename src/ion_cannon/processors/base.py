from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ion_cannon.collectors.base import ContentItem

class ValidationResult(BaseModel):
    """Model for content validation results."""
    
    is_relevant: bool = Field(..., description="Whether the content is relevant")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    primary_topic: str = Field(..., description="Main topic identified")
    reason: str = Field(..., description="Explanation for the decision")
    key_aspects: List[str] = Field(default_factory=list, description="Key aspects identified")

class Summary(BaseModel):
    """Model for content summaries."""
    
    title: str = Field(..., description="Content title")
    summary: str = Field(..., description="Brief summary")
    nofluff_take: str = Field(..., description="Key insights")
    ciso_takeaway: str = Field(..., description="CISO-level takeaways")
    security_engineer_thoughts: str = Field(..., description="Technical insights")

class BaseProcessor(ABC):
    """Abstract base class for content processors."""
    
    @abstractmethod
    async def process(self, content: ContentItem) -> Any:
        """
        Process a content item.
        
        Args:
            content: Content item to process
            
        Returns:
            Processing result
        """
        pass
