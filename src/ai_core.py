"""AI processing module for fact extraction and analysis."""

import json
import re

import aiohttp
from loguru import logger

from src.constants import (
    DEFAULT_TIMEOUT,
    PUBLIC_ANALYSIS_PROMPT,
    PUBLIC_EXTRACTION_PROMPT,
    TAG_INSTRUCTIONS,
)
from src.contracts import PipelineResult
from src.logger import log_exception_short
from src.session_manager import session_manager
from src.settings import settings


class AIAnalyze:
    """Run the two-step AI pipeline for article analysis."""

    def __init__(self) -> None:
        self.logger = logger

    @property
    def session(self) -> aiohttp.ClientSession:
        """Return a shared aiohttp session."""
        return session_manager.get()

    async def _call_llm(self, prompt: str, content: str) -> PipelineResult:
        """Call the LLM API and normalize the output into PipelineResult."""
        try:
            payload = {
                "model": settings.AI_MODEL,
                "reasoning": {"enabled": True},
                "messages": [
                    {"role": "user", "content": f"{prompt}{TAG_INSTRUCTIONS}{content}"}
                ],
                "temperature": 0.2,
            }

            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.AI_TOKEN}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload),
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                resp = await resp.json()

            logger.info(f"Used model to analyze: {resp['model']}")

            if "choices" not in resp:
                raise ValueError(f"LLM error: {resp}")

            clean_text, tag = self.extract_and_validate_tag(
                resp["choices"][0]["message"]["content"]
            )
            return PipelineResult.ok(text=clean_text, tag=tag)
        except (aiohttp.ClientError, TypeError, ValueError) as exc:
            log_exception_short(exc=exc, prefix="LLM call failed", level="error")
            return PipelineResult.fail(
                "AI request failed due to network or response format error."
            )

    def extract_and_validate_tag(self, text: str) -> tuple[str, str | None]:
        """Extract a trailing hashtag and return cleaned text plus tag."""
        match = re.search(r"#([A-Za-z0-9]+)\s*$", text.strip())
        if not match:
            return text, None

        tag = f"#{match.group(1)}"
        clean_text = text[: match.start()].strip()
        return clean_text, tag

    async def extract_facts(self, article_text: str) -> PipelineResult:
        """Run step 1 and return extracted facts as normalized text."""
        llm_result = await self._call_llm(
            prompt=PUBLIC_EXTRACTION_PROMPT, content=article_text
        )
        if not llm_result.success or llm_result.text is None:
            return PipelineResult.fail(
                llm_result.error or "Fact extraction request failed."
            )

        raw = llm_result.text.strip().replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(raw)
            return PipelineResult.ok(
                text=json.dumps(parsed, ensure_ascii=False, indent=2),
                tag=llm_result.tag,
            )
        except json.JSONDecodeError:
            return PipelineResult.ok(text=raw, tag=llm_result.tag)

    async def send_for_ai_analyze(
        self, article_text: str | None, category: str | None = None
    ) -> PipelineResult:
        """Run full analysis flow and return the final message result."""
        if not article_text or not article_text.strip():
            logger.warning("Article text is empty after parser extraction")
            return PipelineResult.fail(
                "Failed to extract article text. Try another URL."
            )

        words_count = len(article_text.split())
        logger.debug(f"Article words count: {words_count}")

        if words_count < 100:
            return PipelineResult.fail("Article too short for meaningful analysis.")

        if category and category.lower() == "opinion":
            return PipelineResult.fail(
                "Low signal. Opinion piece - no actionable data."
            )

        logger.info("Started extracting facts. Step 1/2")
        extracted = await self.extract_facts(article_text)
        if not extracted.success or extracted.text is None:
            logger.warning("Failed to extract facts due to upstream LLM/API error")
            return PipelineResult.fail("AI extraction step failed. Please retry later.")

        logger.info("Started analyzing extracted facts. Step 2/2")
        analyzed = await self._call_llm(
            prompt=PUBLIC_ANALYSIS_PROMPT, content=extracted.text
        )
        if not analyzed.success or analyzed.text is None:
            logger.warning("AI response was unexpected")
            return PipelineResult.fail("AI analysis step failed. Please retry later.")

        logger.info("Successfully finished extracting facts")
        return PipelineResult.ok(text=analyzed.text, tag=analyzed.tag or extracted.tag)

    async def send_for_ai_analize(
        self, article_text: str | None, category: str | None = None
    ) -> PipelineResult:
        """Backward-compatible alias for legacy misspelled method name."""
        return await self.send_for_ai_analyze(
            article_text=article_text, category=category
        )
