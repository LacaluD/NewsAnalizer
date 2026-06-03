import asyncio

import aiohttp

from src.parser import Parser


class AsyncResponseCtx:
    def __init__(self, payload: str):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return self._payload


class DummySession:
    def __init__(self, response=None, error: Exception | None = None):
        self._response = response
        self._error = error

    def get(self, *_args, **_kwargs):
        if self._error:
            raise self._error
        return self._response


def test_session_property_uses_shared_manager_success_case(mocker) -> None:
    parser = Parser()
    shared = object()
    mocked_get = mocker.patch("src.parser.session_manager.get", return_value=shared)

    resolved = parser.session

    assert resolved is shared and mocked_get.call_count == 1


def test_extract_text_returns_parsed_text_success_case(mocker) -> None:
    parser = Parser()
    session = DummySession(response=AsyncResponseCtx("<html>body</html>"))
    mocker.patch.object(
        Parser, "session", new_callable=mocker.PropertyMock, return_value=session
    )
    mocker.patch("src.parser.trafilatura.extract", return_value="Parsed content")

    result = asyncio.run(parser.extract_text("https://example.com"))

    assert result == "Parsed content"


def test_extract_text_returns_none_on_network_failure_failure_case(mocker) -> None:
    parser = Parser()
    session = DummySession(error=aiohttp.ClientError("boom"))
    mocker.patch.object(
        Parser, "session", new_callable=mocker.PropertyMock, return_value=session
    )

    result = asyncio.run(parser.extract_text("https://example.com"))

    assert result is None


def test_extract_text_returns_none_on_empty_html_edge_case(mocker) -> None:
    parser = Parser()
    session = DummySession(response=AsyncResponseCtx(""))
    mocker.patch.object(
        Parser, "session", new_callable=mocker.PropertyMock, return_value=session
    )

    result = asyncio.run(parser.extract_text("https://example.com"))

    assert result is None


def test_extract_text_returns_none_when_extractor_fails_failure_case(mocker) -> None:
    parser = Parser()
    session = DummySession(response=AsyncResponseCtx("<html>body</html>"))
    mocker.patch.object(
        Parser, "session", new_callable=mocker.PropertyMock, return_value=session
    )
    mocker.patch("src.parser.trafilatura.extract", return_value=None)

    result = asyncio.run(parser.extract_text("https://example.com"))

    assert result is None
