"""Utility helpers used by Telegram bot handlers."""

import asyncio

import requests
from loguru import logger

from src.settings import settings


class BotUtils:
    """Provide network and delivery helper methods for the bot."""

    def __init__(self) -> None:
        self.logger = logger
        self.url_get_204 = "https://clients3.google.com/generate_204"
        self._send_semaphore = asyncio.BoundedSemaphore(5)

    def connection_check_via_request(self, user_id: int) -> bool | str:
        """Return True when outbound internet connection is available."""
        if user_id == settings.OWNER_TG_ID:
            try:
                requests.get(self.url_get_204, timeout=3)
                return True
            except requests.RequestException:
                return False
        else:
            return "Insufficient permissions"
