import requests

from src.bot.bot_utils import BotUtils


def test_init_success_case_sets_defaults() -> None:
    utils = BotUtils()
    assert utils.url_get_204.startswith("https://")


def test_init_edge_case_has_bounded_semaphore() -> None:
    utils = BotUtils()
    assert utils._send_semaphore._value == 5


def test_init_failure_case_logger_is_present() -> None:
    utils = BotUtils()
    assert utils.logger is not None


def test_connection_check_success_case_owner_online(mocker) -> None:
    utils = BotUtils()
    mocker.patch("src.bot.bot_utils.settings.OWNER_TG_ID", 42)
    mocked_get = mocker.patch("src.bot.bot_utils.requests.get")

    result = utils.connection_check_via_request(42)

    assert result is True and mocked_get.call_count == 1


def test_connection_check_failure_case_owner_offline(mocker) -> None:
    utils = BotUtils()
    mocker.patch("src.bot.bot_utils.settings.OWNER_TG_ID", 42)
    mocker.patch(
        "src.bot.bot_utils.requests.get", side_effect=requests.RequestException("boom")
    )

    result = utils.connection_check_via_request(42)

    assert result is False


def test_connection_check_edge_case_non_owner() -> None:
    utils = BotUtils()
    result = utils.connection_check_via_request(777)
    assert result == "Insufficient permissions"
