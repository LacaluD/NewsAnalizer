import asyncio
import runpy
from types import SimpleNamespace

import pytest

import main as app_main


async def _raise_keyboard_interrupt():
    raise KeyboardInterrupt


async def _raise_runtime_error():
    raise RuntimeError("close failed")


def test_run_success_case(mocker) -> None:
    tg_bot = SimpleNamespace(main=mocker.AsyncMock())
    logger = SimpleNamespace(info=mocker.Mock())
    close_mock = mocker.AsyncMock()
    sleep_mock = mocker.AsyncMock()
    mocker.patch.object(app_main.session_manager, "close", close_mock)
    mocker.patch.object(app_main.asyncio, "sleep", sleep_mock)

    asyncio.run(app_main.run(tg_bot=tg_bot, logger=logger))

    assert close_mock.call_count == 1 and sleep_mock.call_count == 1


def test_run_failure_case_keyboard_interrupt(mocker) -> None:
    tg_bot = SimpleNamespace(main=_raise_keyboard_interrupt)
    logger = SimpleNamespace(info=mocker.Mock())
    close_mock = mocker.AsyncMock()
    mocker.patch.object(app_main.session_manager, "close", close_mock)
    mocker.patch.object(app_main.asyncio, "sleep", mocker.AsyncMock())

    asyncio.run(app_main.run(tg_bot=tg_bot, logger=logger))

    assert close_mock.call_count == 1


def test_run_edge_case_cleanup_error_propagates(mocker) -> None:
    tg_bot = SimpleNamespace(main=mocker.AsyncMock())
    logger = SimpleNamespace(info=mocker.Mock())
    mocker.patch.object(app_main.session_manager, "close", _raise_runtime_error)
    mocker.patch.object(app_main.asyncio, "sleep", mocker.AsyncMock())

    with pytest.raises(RuntimeError):
        asyncio.run(app_main.run(tg_bot=tg_bot, logger=logger))


def test_main_module_entrypoint_success_case(mocker) -> None:
    fake_logger = SimpleNamespace(info=mocker.Mock())
    mocker.patch("src.logger.MainLogger.init_logger", return_value=fake_logger)
    mocker.patch("src.parser.Parser", return_value=SimpleNamespace())
    mocker.patch("src.ai_core.AIAnalyze", return_value=SimpleNamespace())
    mocker.patch(
        "src.bot.analyzing_service.AnalyzingTGService", return_value=SimpleNamespace()
    )
    mocker.patch("src.bot.sender.TelegramBot", return_value=SimpleNamespace())
    mocked_run = mocker.patch("asyncio.run", side_effect=lambda coro: coro.close())

    runpy.run_module("main", run_name="__main__")

    assert mocked_run.call_count == 1


def test_main_module_entrypoint_failure_case_logger_init_raises(mocker) -> None:
    mocker.patch(
        "src.logger.MainLogger.init_logger", side_effect=RuntimeError("init failed")
    )

    with pytest.raises(RuntimeError):
        runpy.run_module("main", run_name="__main__")


def test_main_module_entrypoint_edge_case_finally_passes(mocker) -> None:
    mocker.patch("src.logger.MainLogger.init_logger", side_effect=KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        runpy.run_module("main", run_name="__main__")
