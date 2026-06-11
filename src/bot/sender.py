"""Main Telegram bot logic."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import BotCommand, Message
from loguru import logger

from src.ai_core import AIAnalyze
from src.bot.analyzing_service import AnalyzingTGService
from src.bot.bot_utils import BotUtils
from src.parser import Parser
from src.settings import settings


class TelegramBot:
    """Handle Telegram commands and message delivery."""

    @staticmethod
    def _parse_analyze_command(text: str | None) -> tuple[str | None, str | None]:
        """Parse `/analyze <url>` (or legacy `/analize`) command safely."""
        if not text:
            return None, None

        parts = text.strip().split(maxsplit=1)
        if len(parts) != 2:
            return None, None

        cmd, url = parts
        if cmd not in {"/analyze", "/analize"}:
            return None, None

        return cmd, url.strip()

    @staticmethod
    def _parse_analize_command(text: str | None) -> tuple[str | None, str | None]:
        """Backward-compatible alias for legacy parser name."""
        return TelegramBot._parse_analyze_command(text)

    @staticmethod
    def _is_allowed_platform(url: str) -> bool:
        """Allow only CoinDesk domains in the public command."""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]

        return host == "coindesk.com" or host.endswith(".coindesk.com")

    def __init__(
        self,
        analyzing_service: AnalyzingTGService | None = None,
    ) -> None:
        """Initialize bot with canonical and legacy argument support."""
        self.bot = Bot(token=settings.TG_BOT_TOKEN)
        self.bot_utils = BotUtils()
        self.service_layer = (
            analyzing_service
            if analyzing_service is not None
            else AnalyzingTGService(news_parser=Parser(), ai_analyzer=AIAnalyze())
        )
        if self.service_layer is None:
            raise ValueError("Analyzing service instance must be provided")
        self.logger = logger

        self._send_semaphore = asyncio.BoundedSemaphore(5)
        self.session = None

    async def start_handler(self, message: Message) -> None:
        """Handle `/start` command and return basic bot context."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        if message.text and message.text == "/start":
            msg = (
                "Bot is running successfully\n"
                f"Your Telegram ID: {user_id}\n"
                f"Chat ID: {chat_id}"
            )
            await message.bot.send_message(text=msg, chat_id=chat_id)

    async def connection_handler(self, message: Message) -> None:
        """Handle `/connection` command to verify internet access."""
        connection = self.bot_utils.connection_check_via_request(message.from_user.id)
        if isinstance(connection, str):
            await message.answer(text=connection)
        elif connection:
            await message.answer(text="Internet connection is available")
        else:
            await message.answer(text="No internet connection")

    async def _public_analyze_handler(self, message: Message) -> None:
        """Handle `/analyze` command and send analyzed output."""
        cmd, url = self._parse_analyze_command(message.text)
        if cmd is None or url is None:
            await message.answer(text="Usage: /analyze https://www.coindesk.com/...")
            return

        if not self._is_allowed_platform(url):
            await message.answer(
                text="Platform is not allowed. Use only CoinDesk links."
            )
            return

        if cmd in {"/analyze", "/analize"}:
            await message.answer(text="Analyzing platform: coindesk")

            result = await self.service_layer.parse_news(url)
            if not result.success or result.text is None:
                self.logger.error(
                    f"Failed to build message from article: {result.error}"
                )
                await message.answer(
                    text=result.error or "Could not analyze this link right now."
                )
                return

            tag = result.tag or ""
            final_text = self.format_for_telegram(text=result.text)
            tg_message = f"{final_text}\n\n{tag}".strip()

            await self.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID, text=tg_message, parse_mode="HTML"
            )
            self.logger.success("Successfully finished pipeline")
            return

    async def _public_analize_handler(self, message: Message) -> None:
        """Backward-compatible alias for legacy handler name."""
        await self._public_analyze_handler(message)

    def format_for_telegram(self, text: str) -> str:
        """Convert simple markdown-style fragments to Telegram HTML."""
        blocks = [block.strip() for block in text.strip().split("\n") if block.strip()]
        result = []

        for block in blocks:
            block = re.sub(r"\*\*(\[[^\]]+\]:?)\*\*", r"<b>\1</b>", block)
            block = re.sub(r"\*(So what:[^*]+)\*", r"<i>\1</i>", block)
            result.append(block)

        return "\n\n".join(result)

    def _fix_html_tags(self, text: str) -> str:
        """Fix unmatched or misordered HTML tags for Telegram output."""
        allowed = ["b", "i", "u", "s", "code"]
        stack = []

        def replace_tag(match: re.Match) -> str:
            closing = match.group(1)
            tag = match.group(2).lower()
            if tag not in allowed:
                return str(match.group(0))
            if not closing:
                stack.append((tag, match.start()))
                return str(match.group(0))
            if stack and stack[-1][0] == tag:
                stack.pop()
                return str(match.group(0))
            return ""

        text = re.sub(r"<(/?)(\w+)[^>]*>", replace_tag, text)

        for tag, _ in reversed(stack):
            text += f"</{tag}>"

        return text

    def format_tags_for_tg(self, tags: str | list[str]) -> str:
        """Format one or many tags as Telegram hashtags."""
        if isinstance(tags, str):
            tags = [tags]
        return " ".join(f"#{tag.replace(' ', '_')}" for tag in tags)

    def foramt_tags_for_tg(self, tags: str | list[str]) -> str:
        """Backward-compatible alias for legacy misspelled method name."""
        return self.format_tags_for_tg(tags)

    async def send_ch_msg(self, msg: str) -> None:
        """Send a message to the configured admin chat."""
        self.logger.info("Sending built message to channel without image")
        await self.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID, text=msg, parse_mode="HTML"
        )

    async def main(self) -> None:
        """Register handlers and start bot polling."""
        self.dp = Dispatcher()
        self.dp.message.register(self.start_handler, Command("start"))
        self.dp.message.register(self.connection_handler, Command("connection"))
        self.dp.message.register(self._public_analyze_handler, Command("analyze"))

        await self.bot.set_my_commands(
            [
                BotCommand(command="start", description="Start the bot"),
                BotCommand(
                    command="connection", description="Check internet connection"
                ),
                BotCommand(
                    command="analyze", description="Analyze CoinDesk article by URL"
                ),
            ]
        )

        try:
            self.logger.info("Bot is ready to receive new commands")
            await self.dp.start_polling(self.bot, handle_signals=False)
        except asyncio.CancelledError:
            self.logger.debug("Bot finished polling process")
