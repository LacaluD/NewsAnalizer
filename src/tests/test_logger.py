from pathlib import Path
import traceback
from types import SimpleNamespace

import pytest

from src.logger import MainLogger, format_exception_short, log_exception_short


def test_main_logger_init_success_case() -> None:
    lg = MainLogger()
    assert lg.logger is not None


def test_main_logger_init_edge_case_repeated_construction() -> None:
    first = MainLogger()
    second = MainLogger()
    assert first.logger is second.logger


def test_main_logger_init_failure_case_object_exists() -> None:
    lg = MainLogger()
    assert hasattr(lg, "logger")


def test_ensure_log_path_exists_success_case(mocker, tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "main.log"
    mocker.patch("src.logger.LOG_DIR_PATH", log_dir)
    mocker.patch("src.logger.LOG_FILE_PATH", log_file)

    MainLogger().ensure_log_path_exists()

    assert log_dir.exists() and log_file.exists()


def test_ensure_log_path_exists_edge_case_when_exists(mocker, tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "main.log"
    log_dir.mkdir(parents=True)
    log_file.touch()
    mocker.patch("src.logger.LOG_DIR_PATH", log_dir)
    mocker.patch("src.logger.LOG_FILE_PATH", log_file)

    MainLogger().ensure_log_path_exists()

    assert log_file.exists()


def test_ensure_log_path_exists_failure_case_mkdir_error(
    mocker, tmp_path: Path
) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "main.log"
    mocker.patch("src.logger.LOG_DIR_PATH", log_dir)
    mocker.patch("src.logger.LOG_FILE_PATH", log_file)
    mocker.patch.object(Path, "mkdir", side_effect=OSError("no"))

    with pytest.raises(OSError):
        MainLogger().ensure_log_path_exists()


def test_get_format_success_case_colorized() -> None:
    fmt = MainLogger().get_format(colorize=True)
    assert "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green>" in fmt


def test_get_format_failure_case_plain_has_no_color_markup() -> None:
    fmt = MainLogger().get_format(colorize=False)
    assert "<green>" not in fmt


def test_get_format_edge_case_contains_level_template() -> None:
    fmt = MainLogger().get_format(colorize=False)
    assert "[{level: <8}]" in fmt


def test_init_logger_success_case(mocker) -> None:
    lg = MainLogger()
    mocker.patch.object(lg, "ensure_log_path_exists")
    remove = mocker.patch.object(lg.logger, "remove")
    add = mocker.patch.object(lg.logger, "add")
    info = mocker.patch.object(lg.logger, "info")

    returned = lg.init_logger()

    assert (
        returned is lg.logger
        and remove.call_count == 1
        and add.call_count == 2
        and info.call_count == 1
    )


def test_init_logger_failure_case_when_ensure_fails(mocker) -> None:
    lg = MainLogger()
    mocker.patch.object(lg, "ensure_log_path_exists", side_effect=RuntimeError("x"))

    with pytest.raises(RuntimeError):
        lg.init_logger()


def test_init_logger_edge_case_calls_get_format_for_both_handlers(mocker) -> None:
    lg = MainLogger()
    mocker.patch.object(lg, "ensure_log_path_exists")
    mocker.patch.object(lg.logger, "remove")
    mocker.patch.object(lg.logger, "add")
    mocker.patch.object(lg.logger, "info")
    spy = mocker.spy(lg, "get_format")

    lg.init_logger()

    assert spy.call_count == 2


def test_format_exception_short_success_case_with_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        rendered = format_exception_short(exc)

    assert "ValueError: boom" in rendered


def test_format_exception_short_failure_case_without_traceback() -> None:
    exc = ValueError("plain")
    rendered = format_exception_short(exc)
    assert rendered == "ValueError: plain"


def test_format_exception_short_edge_case_limit_more_than_frames() -> None:
    try:
        raise RuntimeError("x")
    except RuntimeError as exc:
        rendered = format_exception_short(exc, limit=100)
    assert "RuntimeError: x" in rendered


def test_format_exception_short_failure_case_empty_extracted_frames(mocker) -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        mocker.patch("src.logger.traceback.extract_tb", return_value=[])
        rendered = format_exception_short(exc)

    assert rendered == "ValueError: boom"


def test_format_exception_short_edge_case_relative_to_fails(mocker) -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        mocker.patch(
            "src.logger.traceback.extract_tb",
            return_value=[
                traceback.FrameSummary("/tmp/outside.py", 7, "fn", line="x = 1")
            ],
        )
        rendered = format_exception_short(exc)

    assert "ValueError: boom" in rendered


def test_log_exception_short_success_case_selected_level(mocker) -> None:
    mocked_error = mocker.patch("src.logger.logger.error")
    exc = ValueError("bad")

    log_exception_short(exc, prefix="pref", level="error", limit=1)

    assert mocked_error.call_count == 1


def test_log_exception_short_failure_case_unknown_level_falls_back(mocker) -> None:
    mocked_error = mocker.patch("src.logger.logger.error")
    exc = ValueError("bad")

    log_exception_short(exc, prefix="pref", level="missing", limit=1)

    assert mocked_error.call_count == 1


def test_log_exception_short_failure_case_missing_log_method_branch(mocker) -> None:
    fake_error = mocker.Mock()
    mocker.patch("src.logger.logger", SimpleNamespace(error=fake_error))
    exc = ValueError("bad")

    log_exception_short(exc, prefix="pref", level="missing", limit=1)

    assert fake_error.call_count == 1


def test_log_exception_short_edge_case_internal_error_branch(mocker) -> None:
    mocker.patch(
        "src.logger.format_exception_short",
        side_effect=RuntimeError("formatter failed"),
    )
    mocked_error = mocker.patch("src.logger.logger.error")
    exc = ValueError("bad")

    log_exception_short(exc, prefix="pref", level="error", limit=1)

    assert mocked_error.call_count == 1
