import asyncio
from types import SimpleNamespace

from src.bot.sender import TelegramBot
from src.contracts import PipelineResult


class DummyMessage:
    def __init__(self, text: str | None, user_id: int = 1, chat_id: int = 2):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.chat = SimpleNamespace(id=chat_id)
        self.bot = SimpleNamespace(send_message=None)
        self.answer = None


class DummyService:
    def __init__(self, result: PipelineResult):
        self.result = result

    async def parse_news(self, _url: str) -> PipelineResult:
        return self.result


class DummyRegister:
    def __init__(self):
        self.calls = []

    def register(self, handler, command):
        self.calls.append((handler, command))


class DummyDispatcher:
    def __init__(self, raise_cancelled: bool = False):
        self.message = DummyRegister()
        self.raise_cancelled = raise_cancelled

    async def start_polling(self, *_args, **_kwargs):
        if self.raise_cancelled:
            raise asyncio.CancelledError
        return None


def build_bot(mocker, service_result: PipelineResult) -> TelegramBot:
    mocker.patch(
        "src.bot.sender.Bot",
        return_value=SimpleNamespace(
            send_message=mocker.AsyncMock(),
            set_my_commands=mocker.AsyncMock(),
        ),
    )
    return TelegramBot(analyzing_service=DummyService(service_result))


def test_parse_analyze_command_success_case() -> None:
    cmd, url = TelegramBot._parse_analyze_command(
        "/analyze https://coindesk.com/x")
    assert cmd == "/analyze" and url == "https://coindesk.com/x"


def test_parse_analyze_command_failure_case_wrong_command() -> None:
    cmd, url = TelegramBot._parse_analyze_command(
        "/start https://coindesk.com/x")
    assert cmd is None and url is None


def test_parse_analyze_command_edge_case_missing_url() -> None:
    cmd, url = TelegramBot._parse_analyze_command("/analyze")
    assert cmd is None and url is None


def test_parse_analize_command_alias_success_case() -> None:
    cmd, url = TelegramBot._parse_analize_command(
        "/analyze https://coindesk.com/x")
    assert cmd == "/analyze" and url == "https://coindesk.com/x"


def test_parse_analize_command_alias_failure_case() -> None:
    cmd, url = TelegramBot._parse_analize_command(
        "/start https://coindesk.com/x")
    assert cmd is None and url is None


def test_parse_analize_command_alias_edge_case_empty_text() -> None:
    cmd, url = TelegramBot._parse_analize_command(None)
    assert cmd is None and url is None


def test_is_allowed_platform_success_case_main_domain() -> None:
    assert TelegramBot._is_allowed_platform(
        "https://coindesk.com/news") is True


def test_is_allowed_platform_success_case_subdomain_edge() -> None:
    assert TelegramBot._is_allowed_platform(
        "https://www.sub.coindesk.com/news") is True


def test_is_allowed_platform_failure_case_bad_scheme() -> None:
    assert TelegramBot._is_allowed_platform("ftp://coindesk.com/news") is False


def test_init_success_case_with_service(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.service_layer is not None


def test_init_failure_case_without_service_dependency(mocker) -> None:
    mocker.patch(
        "src.bot.sender.Bot",
        return_value=SimpleNamespace(send_message=mocker.AsyncMock()),
    )
    mocker.patch("src.bot.sender.Parser", return_value=SimpleNamespace())
    mocker.patch("src.bot.sender.AIAnalyze", return_value=SimpleNamespace())
    mocker.patch(
        "src.bot.sender.AnalyzingTGService",
        return_value=SimpleNamespace(parse_news=mocker.AsyncMock()),
    )

    bot = TelegramBot(analyzing_service=None)

    assert bot.service_layer is not None


def test_init_edge_case_session_starts_none(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.session is None


def test_init_failure_case_value_error_when_factory_returns_none(mocker) -> None:
    mocker.patch(
        "src.bot.sender.Bot",
        return_value=SimpleNamespace(send_message=mocker.AsyncMock()),
    )
    mocker.patch("src.bot.sender.AnalyzingTGService",
                 return_value=None, create=True)

    try:
        _ = TelegramBot(analyzing_service=None)
    except ValueError as exc:
        assert "Analyzing service instance must be provided" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError when AnalyzingTGService() resolves to None"
        )


def test_start_handler_success_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/start", user_id=11, chat_id=22)
    message.bot.send_message = mocker.AsyncMock()

    asyncio.run(bot.start_handler(message))

    assert message.bot.send_message.call_count == 1


def test_start_handler_failure_case_non_start_command(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/noop")
    message.bot.send_message = mocker.AsyncMock()

    asyncio.run(bot.start_handler(message))

    assert message.bot.send_message.call_count == 0


def test_start_handler_edge_case_empty_text(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text=None)
    message.bot.send_message = mocker.AsyncMock()

    asyncio.run(bot.start_handler(message))

    assert message.bot.send_message.call_count == 0


def test_connection_handler_success_case_online(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/connection")
    message.answer = mocker.AsyncMock()
    mocker.patch.object(
        bot.bot_utils, "connection_check_via_request", return_value=True
    )

    asyncio.run(bot.connection_handler(message))

    assert (
        message.answer.await_args.kwargs["text"] == "Internet connection is available"
    )


def test_connection_handler_failure_case_offline(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/connection")
    message.answer = mocker.AsyncMock()
    mocker.patch.object(
        bot.bot_utils, "connection_check_via_request", return_value=False
    )

    asyncio.run(bot.connection_handler(message))

    assert message.answer.await_args.kwargs["text"] == "No internet connection"


def test_connection_handler_edge_case_permissions_message(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/connection")
    message.answer = mocker.AsyncMock()
    mocker.patch.object(
        bot.bot_utils,
        "connection_check_via_request",
        return_value="Insufficient permissions",
    )

    asyncio.run(bot.connection_handler(message))

    assert message.answer.await_args.kwargs["text"] == "Insufficient permissions"


def test_public_analyze_handler_failure_case_bad_command(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/analyze")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analyze_handler(message))

    assert "Usage: /analyze" in message.answer.await_args.kwargs["text"]


def test_public_analyze_handler_failure_case_not_allowed_platform(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/analyze https://example.com/x")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analyze_handler(message))

    assert (
        message.answer.await_args.kwargs["text"]
        == "Platform is not allowed. Use only CoinDesk links."
    )


def test_public_analyze_handler_failure_case_pipeline_error(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.fail("bad"))
    message = DummyMessage(text="/analyze https://coindesk.com/x")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analyze_handler(message))

    assert message.answer.await_args.kwargs["text"] == "bad"


def test_public_analyze_handler_success_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok(
        "**[L]:** text *So what: why*", "#BTC"))
    message = DummyMessage(text="/analyze https://coindesk.com/x")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analyze_handler(message))

    assert bot.bot.send_message.call_count == 1


def test_public_analize_handler_alias_edge_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    message = DummyMessage(text="/analyze")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analize_handler(message))

    assert message.answer.call_count == 1


def test_public_analize_handler_alias_success_case_delegates(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    delegated = mocker.patch.object(
        bot, "_public_analyze_handler", mocker.AsyncMock())
    message = DummyMessage(text="/analyze https://coindesk.com/x")
    message.answer = mocker.AsyncMock()

    asyncio.run(bot._public_analize_handler(message))

    assert delegated.call_count == 1


def test_public_analize_handler_alias_failure_case_delegates(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    delegated = mocker.patch.object(
        bot, "_public_analyze_handler", mocker.AsyncMock(
            side_effect=RuntimeError("x"))
    )
    message = DummyMessage(text="/analyze https://coindesk.com/x")
    message.answer = mocker.AsyncMock()

    try:
        asyncio.run(bot._public_analize_handler(message))
    except RuntimeError as exc:
        assert str(exc) == "x" and delegated.call_count == 1
    else:
        raise AssertionError("Expected RuntimeError from delegated handler")


def test_format_for_telegram_success_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    rendered = bot.format_for_telegram("**[Label]:** value\n*So what: reason*")
    assert "<b>[Label]:</b>" in rendered and "<i>So what: reason</i>" in rendered


def test_format_for_telegram_failure_case_no_markdown(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    rendered = bot.format_for_telegram("plain")
    assert rendered == "plain"


def test_format_for_telegram_edge_case_blank_lines(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    rendered = bot.format_for_telegram("\nline1\n\nline2\n")
    assert rendered == "line1\n\nline2"


def test_fix_html_tags_success_case_balanced(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot._fix_html_tags("<b>ok</b>") == "<b>ok</b>"


def test_fix_html_tags_failure_case_misordered_closing(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    fixed = bot._fix_html_tags("<b>hello</i>")
    assert fixed == "<b>hello</b>"


def test_fix_html_tags_edge_case_unknown_tag_kept(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    fixed = bot._fix_html_tags("<span>x</span>")
    assert fixed == "<span>x</span>"


def test_format_tags_for_tg_success_case_string(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.format_tags_for_tg("Bitcoin ETF") == "#Bitcoin_ETF"


def test_format_tags_for_tg_failure_case_empty_string(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.format_tags_for_tg("") == "#"


def test_format_tags_for_tg_edge_case_list(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.format_tags_for_tg(["A", "B C"]) == "#A #B_C"


def test_foramt_tags_for_tg_alias_success_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.foramt_tags_for_tg("Tag") == "#Tag"


def test_foramt_tags_for_tg_alias_failure_case_empty(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.foramt_tags_for_tg("") == "#"


def test_foramt_tags_for_tg_alias_edge_case_list(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    assert bot.foramt_tags_for_tg(["A B", "C"]) == "#A_B #C"


def test_send_ch_msg_success_case(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))

    asyncio.run(bot.send_ch_msg("hello"))

    assert bot.bot.send_message.call_count == 1


def test_send_ch_msg_edge_case_html_payload(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))

    asyncio.run(bot.send_ch_msg("<b>hello</b>"))

    assert bot.bot.send_message.await_args.kwargs["parse_mode"] == "HTML"


def test_send_ch_msg_failure_case_empty_text_still_sent(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))

    asyncio.run(bot.send_ch_msg(""))

    assert bot.bot.send_message.await_args.kwargs["text"] == ""


def test_main_success_case_registers_and_polls(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    dispatcher = DummyDispatcher(raise_cancelled=False)
    mocker.patch("src.bot.sender.Dispatcher", return_value=dispatcher)

    asyncio.run(bot.main())

    assert len(dispatcher.message.calls) == 3


def test_main_failure_case_cancelled_polling(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    dispatcher = DummyDispatcher(raise_cancelled=True)
    mocker.patch("src.bot.sender.Dispatcher", return_value=dispatcher)

    asyncio.run(bot.main())

    assert len(dispatcher.message.calls) == 3


def test_main_edge_case_handle_signals_flag(mocker) -> None:
    bot = build_bot(mocker, PipelineResult.ok("x"))
    dispatcher = DummyDispatcher(raise_cancelled=False)
    spy = mocker.spy(dispatcher, "start_polling")
    mocker.patch("src.bot.sender.Dispatcher", return_value=dispatcher)

    asyncio.run(bot.main())

    assert spy.await_args.kwargs["handle_signals"] is False
