from src import constants


def test_constants_bot_name_success_case() -> None:
    assert constants.BOT_NAME == "TG News Bot"


def test_constants_required_keys_failure_case_missing_non_required_key() -> None:
    assert "unknown" not in constants.REQUIRED_KEYS


def test_constants_required_keys_edge_case_contains_expected() -> None:
    assert {"id", "title", "link"}.issubset(constants.REQUIRED_KEYS)
