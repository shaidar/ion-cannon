# src/ion_cannon/processors/summarizer.py
import json
import logging
from typing import Dict, Optional

from ion_cannon.collectors.base import ContentItem
from ion_cannon.core.llm_factory import LLMFactory
from ion_cannon.processors.base import BaseProcessor, Summary

logger = logging.getLogger(__name__)

class ContentSummarizer(BaseProcessor):
    """Generates structured summaries of content using LLM."""
    
    def __init__(self, use_dedicated_llm: bool = False, verbose: bool = False):
        self.use_dedicated_llm = use_dedicated_llm
        self.verbose = verbose
        self._setup_llm()

    def _setup_llm(self):
        """Initialize summarization LLM."""
        try:
            if self.use_dedicated_llm:
                self.llm = LLMFactory.create_summarization_llm(required=False)
            else:
                self.llm = LLMFactory.create_llm(require_llm=False)
                
            if self.llm:
                logger.info("Initialized summarization LLM")
            else:
                logger.warning("No summarizer available, summarization will be skipped")
                
        except Exception as e:
            logger.error(f"Failed to initialize summarizer: {str(e)}")
            self.llm = None

    def _get_summary_prompt(self, title: Optional[str], content: str) -> str:
        """Generate the summarization prompt."""
        return f"""Analyze this AI security content and provide a structured summary.

        Title: {title or 'Untitled'}
        Content: {content[:2500]}

        Return a JSON object with:
        {{
            "title": "Use existing or generate if missing",
            "summary": "2-3 sentences focusing on key points",
            "insight_take": "Key insights that are possibly contrarian/thought-provoking",
        }}"""

    async def process(self, item: ContentItem) -> Dict:
        """Process a content item to generate a structured summary."""
        if not self.llm:
            logger.warning("No summarizer available, returning basic summary")
            return {
                "title": item.title or "Untitled",
                "summary": "Summarization skipped - no LLM available",
                "insight_take": "No insights available",
                "summarization_status": "skipped"
            }

        try:
            response = await self.llm.acomplete(
                self._get_summary_prompt(item.title, item.content)
            )
            result = json.loads(response.text.strip())
            
            if self.verbose:
                logger.debug(f"Generated summary for: {item.url}")
                
            result["summarization_status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"Summarization failed for {item.url}: {str(e)}")
            return {
                "title": item.title or "Error Processing Title",
                "summary": "Error generating summary",
                "insight_take": "Error generating insights",
                "error": str(e),
                "summarization_status": "error"
            }