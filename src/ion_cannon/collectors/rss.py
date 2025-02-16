import logging
from typing import List
from llama_index.readers.web import RssReader
from datetime import datetime

from ion_cannon.collectors.base import ContentItem
from ion_cannon.config.settings import settings

logger = logging.getLogger("ion_cannon")


async def collect_rss() -> List[ContentItem]:
    """Collect content from RSS feeds using LlamaIndex."""
    reader = RssReader()
    items = []

    for feed_url in settings.RSS_FEEDS:
        try:
            documents = reader.load_data(urls=[feed_url])
            for doc in documents:
                # Extract metadata properly
                url = doc.metadata.get("link") or feed_url
                date_str = doc.metadata.get("date")

                if date_str:
                    try:
                        # Try to parse and format the date consistently
                        parsed_date = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                        date_str = parsed_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except (ValueError, AttributeError):
                        logger.debug(f"Could not parse date: {date_str}")

                items.append(
                    ContentItem(
                        source="rss",
                        content=doc.text,
                        url=url,
                        title=doc.metadata.get("title", ""),
                        date=date_str,
                        metadata=doc.metadata,
                    )
                )

                logger.debug(f"Collected RSS item: {url}")

            logger.info(f"Collected {len(documents)} items from {feed_url}")
        except Exception as e:
            logger.error(f"Error collecting from RSS feed {feed_url}: {str(e)}")

    return items
