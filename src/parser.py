"""Download article pages and extract plain text content."""

import asyncio

import aiohttp
import trafilatura
from loguru import logger

from src.constants import DEFAULT_TIMEOUT
from src.session_manager import session_manager


class Parser:
    """Provide article content extraction helpers."""

    def __init__(self) -> None:
        self.logger = logger

    @property
    def session(self) -> aiohttp.ClientSession:
        """Return a shared aiohttp session."""
        return session_manager.get()

    async def extract_text(self, url: str) -> str | None:
        """Fetch an article URL and return extracted text."""
        try:
            async with self.session.get(url, timeout=DEFAULT_TIMEOUT) as resp:
                html = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.logger.error(f"Failed to fetch article body from URL {url}: {exc}")
            return None

        if not html:
            self.logger.warning(f"Got empty HTML content from URL {url}")
            return None

        text = trafilatura.extract(
            html,
            with_metadata=False,
            include_comments=False,
            include_tables=False,
            favor_recall=False,
        )

        if not text:
            self.logger.warning(f"Could not extract article text from URL {url}")
            return None

        return text  # type: ignore[no-any-return]
