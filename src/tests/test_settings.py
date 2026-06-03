import os
from zoneinfo import ZoneInfoNotFoundError

import pytest

from src.settings import Settings, get_settings


def test_tz_returns_zoneinfo_success_case() -> None:
    cfg = Settings(
        AI_TOKEN="a", TG_BOT_TOKEN="b", OWNER_TG_ID=1, ADMIN_CHAT_ID=2, timezone="UTC"
    )
    assert cfg.tz.key == "UTC"


def test_tz_raises_for_invalid_timezone_failure_case() -> None:
    cfg = Settings(
        AI_TOKEN="a",
        TG_BOT_TOKEN="b",
        OWNER_TG_ID=1,
        ADMIN_CHAT_ID=2,
        timezone="BAD/TZ",
    )
    with pytest.raises(ZoneInfoNotFoundError):
        _ = cfg.tz


def test_tz_uses_default_timezone_edge_case() -> None:
    cfg = Settings(AI_TOKEN="a", TG_BOT_TOKEN="b", OWNER_TG_ID=1, ADMIN_CHAT_ID=2)
    assert cfg.tz.key == "UTC"


def test_get_settings_returns_settings_success_case() -> None:
    get_settings.cache_clear()
    loaded = get_settings()
    assert isinstance(loaded, Settings)


def test_get_settings_is_cached_edge_case() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_get_settings_reads_environment_failure_case(mocker) -> None:
    get_settings.cache_clear()
    mocker.patch.dict(
        os.environ,
        {
            "AI_TOKEN": "new-ai",
            "TG_BOT_TOKEN": "new-tg",
            "OWNER_TG_ID": "10",
            "ADMIN_CHAT_ID": "20",
        },
        clear=False,
    )
    loaded = get_settings()
    assert loaded.AI_TOKEN == "new-ai"
