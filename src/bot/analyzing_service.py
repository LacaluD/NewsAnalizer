"""Service layer used by Telegram bot handlers."""

from __future__ import annotations

from loguru import logger
from typing_extensions import TYPE_CHECKING

from src.ai_core import AIAnalyze
from src.contracts import PipelineResult

if TYPE_CHECKING:
    from src.parser import Parser


class AnalyzingTGService:
    """Bridge parser and AI layers for Telegram command handlers."""

    def __init__(
        self,
        news_parser: Parser,
        ai_analyzer: AIAnalyze | None = None,
    ) -> None:
        """Initialize service with canonical and legacy argument support."""
        self.news_parser = news_parser
        self.ai_analyzer = ai_analyzer if ai_analyzer is not None else AIAnalyze()
        if self.ai_analyzer is None:
            raise ValueError("AI analyzer instance must be provided")
        self.logger = logger

    async def parse_news(self, url: str) -> PipelineResult:
        """Parse article text from URL and return AI analysis result."""
        self.logger.info(f"Extracting text from provided URL: {url}")
        article_data = await self.news_parser.extract_text(url)
        if article_data is None:
            self.logger.error("Failed to extract text from article")
            return PipelineResult.fail("Failed to extract text from article.")

        self.logger.info("Sending extracted text to AI for analysis")
        return await self.ai_analyzer.send_for_ai_analyze(article_data, category="")
