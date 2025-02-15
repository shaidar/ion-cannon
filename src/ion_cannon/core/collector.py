import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

from ion_cannon.collectors.base import ContentItem
from ion_cannon.collectors.rss import collect_rss
from ion_cannon.collectors.reddit import collect_reddit
from ion_cannon.config.settings import settings
from ion_cannon.processors.validator import ContentValidator
from ion_cannon.processors.summarizer import ContentSummarizer

logger = logging.getLogger(__name__)
console = Console()

class ContentCollector:
    """Main content collection and processing orchestrator."""
    
    def __init__(
        self,
        use_multi_llm: bool = False,
        verbose: bool = False,
    ):
        """Initialize the content collector."""
        # Early check for configured sources
        if not settings.RSS_FEEDS and not settings.REDDIT_CHANNELS:
            logger.warning("No sources configured. Add URLs to RSS_FEEDS or REDDIT_CHANNELS in settings.")
            self.has_sources = False
            return
            
        self.has_sources = True
        self.use_multi_llm = use_multi_llm
        self.verbose = verbose
        self._setup_processors()

    def _setup_processors(self):
        """Initialize content processors."""
        if not self.has_sources:
            return
            
        self.validator = ContentValidator(
            use_multi_llm=self.use_multi_llm,
            verbose=self.verbose
        )
        self.summarizer = ContentSummarizer(
            use_dedicated_llm=self.use_multi_llm,
            verbose=self.verbose
        )
        logger.info("Initialized content processors")

    async def collect(self) -> List[ContentItem]:
        """Collect content from all sources."""
        if not self.has_sources:
            logger.warning("No sources configured.")
            return []
            
        collectors = []
        
        # Only add collectors for configured sources
        if settings.RSS_FEEDS:
            collectors.append(collect_rss())
        if settings.REDDIT_CHANNELS:
            collectors.append(collect_reddit())
            
        if not collectors:
            return []
            
        results = await asyncio.gather(*collectors, return_exceptions=True)
        all_content: List[ContentItem] = []
        
        for source, result in zip(["RSS", "Web"], results):
            if isinstance(result, Exception):
                logger.error(f"Error collecting from {source}: {str(result)}")
                continue
                
            all_content.extend(result)
            if self.verbose:
                logger.info(f"Collected {len(result)} items from {source}")
            
        return all_content

    def _matches_keywords(self, item: ContentItem) -> bool:
        """
        Check if content matches any configured keywords.
        Return True if NO keywords match (content should be filtered out).
        """
        if not settings.KEYWORDS:
            logger.warning("No keywords configured, passing all content through")
            return True

        content_lower = (item.content or "").lower()
        title_lower = (item.title or "").lower()

        # Check both title and content for keywords
        for keyword in settings.KEYWORDS:
            keyword_lower = keyword.lower()
            if keyword_lower in content_lower or keyword_lower in title_lower:
                if self.verbose:
                    logger.debug(f"Keyword '{keyword}' matched in item: {item.url}")
                return True

        if self.verbose:
            logger.debug(f"No keywords matched for item: {item.url}")
        return False
    
    def _is_older_than_10_days(self, date_str: str) -> bool:
        """
        Check if the given date string is older than 10 days from the current date.
        """
        if not date_str:
            return False  # Consider None or empty dates as not older than 10 days
        
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # Example: Mon, 16 Sep 2024 09:00:00 +0000
            "%a, %d %b %y %H:%M:%S %z",  # Example: Tue, 14 Jan 25 12:00:00 +0000
            "%a, %d %b %Y %H:%M:%S GMT", # Example: Wed, 28 Aug 2024 04:30:00 GMT
            "%a, %d %b %Y %H:%M:%S UTC", # Example: Wed, 27 Nov 2024 14:00:00 UTC
            "%Y-%m-%d %H:%M:%S %Z",      # Example: 2024-12-09 11:05:09 UTC
            "%Y-%m-%d"                   # Example: 2024-12-09
        ]
        
        for date_format in date_formats:
            try:
                item_date = datetime.strptime(date_str, date_format)
                if item_date.tzinfo is not None:
                    item_date = item_date.replace(tzinfo=None)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Date format for '{date_str}' not recognized")

        current_date = datetime.now()
        return (current_date - item_date).days > 10

    async def process_content(
        self,
        content: List[ContentItem],
    ) -> List[Dict]:
        """Process collected content through validation and summarization."""
        if not self.has_sources:
            return []
            
        if not content:
            return []

        total_items = len(content)
        logger.info(f"Starting to process {total_items} items")
        logger.info(f"Using keywords for filtering: {settings.KEYWORDS}")
        
        processed_items = []
        keyword_filtered = 0
        llm_rejected = 0
        date_filtered = 0
        
        # First, filter by keywords
        keyword_matches = []
        for item in content:
            if self._matches_keywords(item):
                keyword_matches.append(item)
            else:
                keyword_filtered += 1
                if self.verbose:
                    logger.debug(f"Filtered out by keywords: {item.title}")

        logger.info(f"After keyword filtering: {len(keyword_matches)} items remain ({keyword_filtered} filtered out)")

        # Filter out items older than 10 days
        recent_items = []
        for item in keyword_matches:
            if not self._is_older_than_10_days(item.date):
                recent_items.append(item)
            else:
                date_filtered += 1
                if self.verbose:
                    logger.debug(f"Filtered out by date: {item.title}")

        logger.info(f"After date filtering: {len(recent_items)} items remain ({date_filtered} filtered out)")
        
        # Then process remaining items with LLM
        for item in recent_items:
            try:
                # Validate with LLM
                validation_result = await self.validator.process(item)
                
                # Only summarize if content is relevant
                if validation_result["is_relevant"]:
                    summary = await self.summarizer.process(item)
                    processed_item = {
                        "url": item.url,
                        "title": item.title or summary.get("title", "Untitled"),
                        "source": item.source,
                        "date": item.date,
                        **summary
                    }
                    processed_items.append(processed_item)
                else:
                    llm_rejected += 1
                    if self.verbose:
                        logger.debug(f"Rejected by LLM: {item.url}")
                    
            except Exception as e:
                logger.error(f"Error processing item {item.url}: {str(e)}")
                continue
        
        # Log final statistics
        logger.info("Content processing summary:")
        logger.info(f"- Total items: {total_items}")
        logger.info(f"- Filtered by keywords: {keyword_filtered}")
        logger.info(f"- Filtered by date: {date_filtered}")
        logger.info(f"- Sent to LLM: {len(recent_items)}")
        logger.info(f"- Rejected by LLM: {llm_rejected}")
        logger.info(f"- Accepted items: {len(processed_items)}")
            
        return processed_items

    def save_results(
        self,
        results: List[Dict],
        output_dir: Optional[Path] = None,
    ):
        """Save processed results to output directory."""
        if not self.has_sources or not results:
            return
            
        output_dir = output_dir or settings.OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = output_dir / f"collected_content_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        # Save formatted report
        report_file = output_dir / f"report_{timestamp}.md"
        self._generate_report(results, report_file)
        
        logger.info(f"Saved {len(results)} results to {output_dir}")

    def _generate_report(self, results: List[Dict], report_file: Path):
        """Generate a formatted markdown report."""
        report_template = """# Content Collection Report

Generated: {timestamp}

## Summary
- Total items: {total_items}
- Sources: {sources}
{collection_period}

## Contents

{items}
"""
        item_template = """### {title}

**Source**: {source}  
**URL**: {url}  
**Date**: {date}

**Summary**
{summary}

**Key Insights**
{insights}

---
"""
        # Get unique sources
        sources = sorted(set(item.get("source", "unknown") for item in results))

        # Handle collection period
        valid_dates = [
            item.get("date") for item in results 
            if item.get("date") and item.get("date") != "N/A"
        ]
        
        if valid_dates:
            period = f"- Collection period: {min(valid_dates)} to {max(valid_dates)}"
        else:
            period = ""

        # Format individual items
        formatted_items = []
        for item in results:
            formatted_items.append(
                item_template.format(
                    title=item.get("title", "Untitled"),
                    source=item.get("source", "Unknown"),
                    url=item.get("url", "N/A"),
                    date=item.get("date", "N/A"),
                    summary=item.get("summary", "No summary available"),
                    insights=item.get("insight_take", "No insights available"),
                )
            )
        
        # Generate final report
        report_content = report_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_items=len(results),
            sources=", ".join(sources),
            collection_period=period,
            items="\n".join(formatted_items)
        )
        
        # Save report
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)