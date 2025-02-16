import logging
from typing import List
import asyncpraw
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from ion_cannon.collectors.base import ContentItem
from ion_cannon.config.settings import settings

logger = logging.getLogger("ion_cannon")


async def fetch_url_content(session: aiohttp.ClientSession, url: str) -> str:
    """
    Fetch content from a URL using aiohttp
    """
    logger.info(f"Attempting to fetch content from URL: {url}")
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                logger.debug(f"Successfully fetched URL: {url}")
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text = soup.get_text(separator=" ", strip=True)

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = " ".join(chunk for chunk in chunks if chunk)

                content_length = len(text)
                logger.info(f"Extracted {content_length} characters from {url}")

                final_text = (
                    text[: settings.MAX_CONTENT_LENGTH]
                    if hasattr(settings, "MAX_CONTENT_LENGTH")
                    else text
                )
                if (
                    hasattr(settings, "MAX_CONTENT_LENGTH")
                    and content_length > settings.MAX_CONTENT_LENGTH
                ):
                    logger.debug(
                        f"Content truncated from {content_length} to {settings.MAX_CONTENT_LENGTH} characters"
                    )

                return final_text
            else:
                logger.warning(
                    f"Failed to fetch URL {url}, status code: {response.status}"
                )
                return ""
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return ""


async def get_post_content(post, session: aiohttp.ClientSession) -> str:
    """
    Get content from a Reddit post, including both selftext and linked content
    """
    logger.info(f"Processing content for post: {post.title}")
    content_parts = []

    # Get post's selftext if it exists
    if hasattr(post, "selftext") and post.selftext:
        logger.debug(f"Found selftext content of length: {len(post.selftext)}")
        content_parts.append(post.selftext)
    else:
        logger.debug("No selftext content found in post")

    # If the post has a URL that's not a Reddit link, fetch its content
    if hasattr(post, "url") and post.url:
        url = post.url
        logger.debug(f"Post URL found: {url}")
        if not url.startswith("https://reddit.com") and not url.startswith(
            "https://www.reddit.com"
        ):
            logger.info(f"Fetching external content from: {url}")
            url_content = await fetch_url_content(session, url)
            if url_content:
                logger.debug(
                    f"Successfully fetched external content of length: {len(url_content)}"
                )
                content_parts.append(url_content)
            else:
                logger.warning(f"No content retrieved from external URL: {url}")
    else:
        logger.debug("No URL found in post")

    final_content = "\n\n".join(content_parts)
    logger.info(f"Total collected content length: {len(final_content)}")
    return final_content


async def collect_reddit() -> List[ContentItem]:
    logger.info("Starting Reddit content collection")
    reddit = asyncpraw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )

    items = []
    keywords = [keyword.lower() for keyword in settings.KEYWORDS]
    logger.info(f"Searching for keywords: {keywords}")
    logger.info(f"Searching in subreddits: {settings.REDDIT_CHANNELS}")

    async with aiohttp.ClientSession() as session:
        for subreddit_name in settings.REDDIT_CHANNELS:
            try:
                logger.info(f"Processing subreddit: {subreddit_name}")
                subreddit = await reddit.subreddit(subreddit_name)
                posts_processed = 0

                async for post in subreddit.new(limit=settings.REDDIT_POST_LIMIT):
                    posts_processed += 1
                    logger.debug(f"Checking post {posts_processed}: {post.title}")

                    if any(keyword in post.title.lower() for keyword in keywords):
                        logger.info(f"Found matching post: {post.title}")
                        # Fetch the content
                        content = await get_post_content(post, session)
                        date_str = post.created_utc

                        if date_str:
                            try:
                                # Try to parse and format the date consistently
                                parsed_date = datetime.fromtimestamp(
                                    date_str, tz=timezone.utc
                                )
                                date_str = parsed_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                            except (ValueError, AttributeError):
                                logger.debug(f"Could not parse date: {date_str}")

                        if content:
                            logger.info(
                                f"Successfully collected content for post: {post.title}"
                            )
                        else:
                            logger.warning(
                                f"No content collected for matching post: {post.title}"
                            )

                        items.append(
                            ContentItem(
                                source=f"reddit/{subreddit_name}",
                                title=post.title,
                                url=f"https://reddit.com{post.permalink}",
                                date=date_str,
                                content=content,
                            )
                        )
                        logger.debug(
                            f"Added item to collection. Current total: {len(items)}"
                        )

                logger.info(
                    f"Finished processing {posts_processed} posts from r/{subreddit_name}"
                )

            except Exception as e:
                logger.error(f"Error searching subreddit {subreddit_name}: {str(e)}")
                continue

    await reddit.close()
    logger.info(f"Collected {len(items)} items from Reddit")
    return items
