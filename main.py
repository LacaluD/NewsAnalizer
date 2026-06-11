"""Main application entry point."""

from __future__ import annotations

import asyncio
from typing import Any

from src.ai_core import AIAnalyze
from src.bot.analyzing_service import AnalyzingTGService
from src.bot.sender import TelegramBot
from src.logger import MainLogger
from src.parser import Parser
from src.session_manager import session_manager
from version import __build__, __commit__, __version__


async def run(tg_bot: TelegramBot, logger: Any) -> None:
    """Start the Telegram bot and perform graceful shutdown cleanup."""
    try:
        await tg_bot.main()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Running final cleanup")
        await session_manager.close()
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    try:
        logger = MainLogger().init_logger()
        logger.info(
            f"Starting app {__version__} (build {__build__}, commit {__commit__})"
        )

        parser = Parser()
        ai_analyzer = AIAnalyze()

        tg_service_layer = AnalyzingTGService(
            news_parser=parser,
            ai_analyzer=ai_analyzer,
        )
        tg_bot = TelegramBot(analyzing_service=tg_service_layer)

        logger.info("Finished setting up necessary classes. Starting main task")
        asyncio.run(run(tg_bot, logger))
    finally:
        pass
