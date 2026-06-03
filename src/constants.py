"""Project-wide constants for bot behavior, prompts, and timeouts."""

import logging
from pathlib import Path

from aiohttp import ClientTimeout

BOT_NAME = "TG News Bot"
BOT_PURPOSE = (
    "Tracks and delivers updates on global news related to the cryptocurrency world."
)

BASE_DIR = Path(__file__).parent.parent
LOG_DIR_PATH = BASE_DIR / "logs"
LOG_FILE_PATH = LOG_DIR_PATH / "main.log"

DEBUG_LEVEL = logging.INFO

DEFAULT_TIMEOUT = ClientTimeout(
    total=120,
    connect=6,
    sock_connect=6,
    sock_read=90,
)

REQUIRED_KEYS = {"id", "title", "link", "published", "author", "media_content", "tags"}

PUBLIC_EXTRACTION_PROMPT = """Extract the main facts from the article below.

OUTPUT FORMAT:
{
  "entities": ["companies, people, tokens mentioned"],
  "numbers": ["key figures mentioned"],
  "events": ["main things that happened"],
  "relationships": ["connections between entities if mentioned"]
}

Article:
----------------
"""

PUBLIC_ANALYSIS_PROMPT = """You are a crypto analyst. Summarize the extracted facts below for a fund manager.

Use only the provided facts.

OUTPUT: 2-4 bullets covering what happened and why it matters.

RULES:
- No investment advice
- Ground each bullet in a specific fact
- Telegram HTML format: <b>[Label]:</b> description. <i>So what: implication.</i>

Extracted facts:
----------------
"""

TAG_INSTRUCTIONS = """
Add one hashtag at the end of the message that reflects the main topic of the article.

Rules:
- Single word after #
- No spaces, only letters and numbers
- English only
- Specific enough to be useful: #BitcoinETF better than #Crypto
"""
